#!/usr/bin/env python3
"""
Kaggle Models Scraper - Parallel Version
Scrapes LLM model names and URLs from Kaggle with parallel execution
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from lxml import html
import csv
import time
import os
from typing import List, Dict, Tuple, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from threading import Lock, Event
import queue
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [Worker-%(thread)d] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

# Global thread-safe data structures
models_lock = Lock()
collected_models = []
seen_urls: Set[str] = set()
pages_lock = Lock()
discovered_pages: Set[int] = set()
max_page_found = 0
stop_discovery = Event()  # Signal to stop when no more pages found

def create_driver() -> webdriver.Chrome:
    """Create and configure a Chrome driver instance"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    return webdriver.Chrome(options=chrome_options)

def scrape_single_page(base_url: str, page_num: int) -> Tuple[List[Dict[str, str]], bool]:
    """
    Scrape a single page and determine if there's a next page

    Args:
        base_url: The base Kaggle models page URL
        page_num: Page number to scrape

    Returns:
        Tuple of (models list, has_next_page)
    """
    driver = None
    models = []
    has_next = False

    try:
        driver = create_driver()

        # For page 1, navigate directly. For others, we need to click through
        logging.info(f"Worker scraping page {page_num}")
        driver.get(base_url)

        # Wait for initial content
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.XPATH, '//ul/li/div/a[contains(@href, "/models/")]')))
        time.sleep(2)

        # Navigate to the target page by clicking next button multiple times
        current_page = 1
        while current_page < page_num:
            try:
                # Try to find and click next button
                next_button = driver.find_element(
                    By.XPATH,
                    '//button[.//svg[@data-testid="NavigateNextIcon"]]'
                )

                if next_button.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(0.5)
                    next_button.click()
                    time.sleep(2)  # Wait for page to load
                    current_page += 1
                else:
                    logging.warning(f"Cannot reach page {page_num}, stopped at page {current_page}")
                    return models, False

            except Exception:
                # Try fallback methods
                try:
                    next_button = driver.find_element(
                        By.XPATH,
                        '//nav//button[contains(@class, "MuiPaginationItem") and contains(@aria-label, "next")]'
                    )

                    if next_button.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                        time.sleep(0.5)
                        next_button.click()
                        time.sleep(2)
                        current_page += 1
                    else:
                        logging.warning(f"Cannot reach page {page_num}, stopped at page {current_page}")
                        return models, False

                except Exception:
                    logging.warning(f"Cannot navigate to page {page_num}, stopped at page {current_page}")
                    return models, False

        # Now we're on the target page, extract content
        page_source = driver.page_source
        tree = html.fromstring(page_source)

        # Extract model links
        list_items = tree.xpath('//ul/li/div/a[contains(@href, "/models/")]')

        logging.info(f"Page {page_num}: Found {len(list_items)} model links")

        for link in list_items:
            href = link.get('href', '')

            if not href or href == '/models':
                continue

            # Extract model name
            name_elements = link.xpath('.//div/div[2]/div/text()')

            if name_elements:
                model_name = name_elements[0].strip()
            else:
                model_name = link.text_content().strip()
                if not model_name:
                    parts = href.strip('/').split('/')
                    if len(parts) >= 2:
                        model_name = parts[-1].replace('-', ' ').title()
                    else:
                        continue

            # Build full URL
            full_url = f"https://www.kaggle.com{href}" if href.startswith('/') else href

            models.append({
                'name': model_name,
                'kaggle_url': full_url
            })

        # Check if there's a next page
        try:
            next_button = driver.find_element(
                By.XPATH,
                '//button[.//svg[@data-testid="NavigateNextIcon"]]'
            )
            has_next = next_button.is_enabled() and next_button.is_displayed()
        except:
            try:
                next_button = driver.find_element(
                    By.XPATH,
                    '//nav//button[contains(@class, "MuiPaginationItem") and contains(@aria-label, "next")]'
                )
                has_next = next_button.is_enabled() and next_button.is_displayed()
            except:
                has_next = False

        logging.info(f"Page {page_num}: Scraped {len(models)} models, has_next={has_next}")

    except Exception as e:
        logging.error(f"Error scraping page {page_num}: {e}")
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()

    return models, has_next

def worker_process_page(base_url: str, work_queue: queue.Queue) -> None:
    """
    Worker function to process pages from the work queue

    Args:
        base_url: Base URL for scraping
        work_queue: Queue containing page numbers to process
    """
    global max_page_found, discovered_pages

    while not stop_discovery.is_set():
        try:
            # Get a page number to process
            page_num = work_queue.get(timeout=1)

            if page_num is None:  # Poison pill
                break

            # Check if already processed
            with pages_lock:
                if page_num in discovered_pages:
                    work_queue.task_done()
                    continue
                discovered_pages.add(page_num)

            # Scrape the page
            models, has_next = scrape_single_page(base_url, page_num)

            # Add models to collection
            if models:
                with models_lock:
                    for model in models:
                        url = model['kaggle_url']
                        if url not in seen_urls:
                            seen_urls.add(url)
                            collected_models.append(model)

            # If there's a next page, add it to the queue
            if has_next:
                next_page = page_num + 1
                with pages_lock:
                    if next_page not in discovered_pages and next_page <= 100:  # Safety limit
                        work_queue.put(next_page)
                        max_page_found = max(max_page_found, next_page)
                        logging.info(f"Page {page_num} discovered page {next_page}, adding to queue")

            work_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            logging.error(f"Worker error processing page: {e}")
            if work_queue.unfinished_tasks > 0:
                work_queue.task_done()

def scrape_kaggle_models_parallel(url: str, num_workers: int = 16) -> List[Dict[str, str]]:
    """
    Scrape Kaggle models using parallel workers with dynamic page discovery

    Args:
        url: The Kaggle models page URL
        num_workers: Number of parallel workers

    Returns:
        List of dictionaries containing model name and URL
    """
    global collected_models, seen_urls, discovered_pages, max_page_found, stop_discovery
    collected_models = []
    seen_urls = set()
    discovered_pages = set()
    max_page_found = 1
    stop_discovery.clear()

    logging.info(f"Starting parallel scraping with {num_workers} workers")

    # Create work queue
    work_queue = queue.Queue()

    # Start with page 1
    work_queue.put(1)

    # Create and start worker threadsj
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Start workers
        futures = []
        for i in range(num_workers):
            future = executor.submit(worker_process_page, url, work_queue)
            futures.append(future)

        # Monitor progress
        last_check_count = 0
        no_progress_checks = 0
        max_no_progress = 5  # Stop if no new models found after 5 checks

        while True:
            time.sleep(3)  # Check every 3 seconds

            # Check if work is still being done
            if work_queue.empty() and work_queue.unfinished_tasks == 0:
                # No more work in queue and all tasks done
                current_count = len(collected_models)

                if current_count == last_check_count:
                    no_progress_checks += 1
                    if no_progress_checks >= max_no_progress:
                        logging.info("No new models found, stopping discovery")
                        break
                else:
                    no_progress_checks = 0
                    last_check_count = current_count

                logging.info(f"Progress: {len(discovered_pages)} pages processed, {current_count} models found")

                # Check if we should stop
                with pages_lock:
                    if len(discovered_pages) >= max_page_found and work_queue.empty():
                        logging.info(f"All {max_page_found} discovered pages have been processed")
                        break

            # Safety check
            if len(discovered_pages) >= 100:
                logging.info("Reached page limit (100), stopping")
                break

        # Signal workers to stop
        stop_discovery.set()

        # Send poison pills to workers
        for _ in range(num_workers):
            work_queue.put(None)

        # Wait for all workers to complete
        for future in futures:
            try:
                future.result(timeout=5)
            except Exception as e:
                logging.error(f"Worker error: {e}")

    logging.info(f"Scraping complete. Processed {len(discovered_pages)} pages, found {len(collected_models)} unique models")

    # Sort models by name for consistent output
    collected_models.sort(key=lambda x: x['name'])

    return collected_models

def save_to_csv(models: List[Dict[str, str]], output_file: str):
    """
    Save scraped models to CSV file

    Args:
        models: List of model dictionaries
        output_file: Path to output CSV file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'kaggle_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for model in models:
            writer.writerow(model)

    logging.info(f"Saved {len(models)} models to {output_file}")

def main():
    """Main function to run the parallel scraper"""

    # Configuration
    url = "https://www.kaggle.com/models?owner-type=organization"
    output_file = "output/kaggle_output_parallel.csv"
    num_workers = 16

    print("=" * 60)
    print("Kaggle Models Scraper - Parallel Version")
    print(f"Using {num_workers} parallel workers")
    print("=" * 60)

    start_time = time.time()

    # Scrape models in parallel
    models = scrape_kaggle_models_parallel(url, num_workers)

    elapsed_time = time.time() - start_time

    if models:
        print(f"\nFound {len(models)} unique models in {elapsed_time:.2f} seconds")

        # Display sample
        print("\nSample of scraped models:")
        for model in models[:5]:
            print(f"  - {model['name']}: {model['kaggle_url']}")

        # Save to CSV
        save_to_csv(models, output_file)
    else:
        print("\nNo models found.")
        save_to_csv([], output_file)

    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")
    print("Scraping complete!")

if __name__ == "__main__":
    main()