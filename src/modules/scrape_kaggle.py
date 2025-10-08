#!/usr/bin/env python3
"""
Kaggle Models Scraper
Scrapes LLM model names and URLs from Kaggle's models page
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
from typing import List, Dict

def scrape_kaggle_models(url: str) -> List[Dict[str, str]]:
    """
    Scrape Kaggle models page for LLM models using Selenium

    Args:
        url: The Kaggle models page URL

    Returns:
        List of dictionaries containing model name and URL
    """
    models = []
    driver = None

    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        print(f"Initializing browser...")
        driver = webdriver.Chrome(options=chrome_options)

        # Navigate to the page
        print(f"Fetching: {url}")
        driver.get(url)

        # Wait for the page to load - wait for the ul element containing models
        print("Waiting for page to load...")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.XPATH, '//ul/li/div/a[contains(@href, "/models/")]')))

        # Give extra time for all elements to render
        time.sleep(3)

        current_page = 1
        max_pages = 50  # Safety limit to prevent infinite loops

        while current_page <= max_pages:
            print(f"\nScraping page {current_page}...")

            # Get page source and parse with lxml
            page_source = driver.page_source
            tree = html.fromstring(page_source)

            # XPath pattern based on provided full XPath
            # Full XPath: /html/body/div/div[1]/div[2]/div/div[6]/div/div/div/ul/li[1]/div/a
            # Flexible version to get all list items
            list_items = tree.xpath('//ul/li/div/a[contains(@href, "/models/")]')

            print(f"Found {len(list_items)} model links on page {current_page}")

            for link in list_items:
                # Get the href (kaggle_url)
                href = link.get('href', '')

                if not href or href == '/models':
                    continue

                # Get the model name using the relative XPath from the link element
                # Full XPath for name: /html/body/div/div[1]/div[2]/div/div[6]/div/div/div/ul/li[1]/div/a/div/div[2]/div
                # Relative to the <a> tag: ./div/div[2]/div
                name_elements = link.xpath('.//div/div[2]/div/text()')

                if name_elements:
                    model_name = name_elements[0].strip()
                else:
                    # Fallback: try to get any text from the link
                    model_name = link.text_content().strip()
                    if not model_name:
                        # Extract from URL as last resort
                        parts = href.strip('/').split('/')
                        if len(parts) >= 2:
                            model_name = parts[-1].replace('-', ' ').title()
                        else:
                            continue

                # Build full URL
                full_url = f"https://www.kaggle.com{href}" if href.startswith('/') else href

                # Avoid duplicates
                if not any(m['kaggle_url'] == full_url for m in models):
                    models.append({
                        'name': model_name,
                        'kaggle_url': full_url
                    })
                    print(f"Found: {model_name}")

            # Try to find and click the next page button
            try:
                next_page = current_page + 1
                # Look for the next page button using the pattern from your HTML
                next_button = driver.find_element(
                    By.XPATH,
                    f'//button[contains(@class, "MuiPaginationItem-page") and @aria-label="Go to page {next_page}"]'
                )

                if next_button and next_button.is_enabled():
                    print(f"Clicking to page {next_page}...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    next_button.click()

                    # Wait for new content to load
                    time.sleep(3)
                    current_page = next_page
                else:
                    print("No more pages available")
                    break
            except Exception as e:
                print(f"No more pages or error finding next button: {e}")
                break

        # If no models found, try a broader XPath
        if not models:
            print("No models found with primary XPath, trying broader search...")
            page_source = driver.page_source
            tree = html.fromstring(page_source)
            all_model_links = tree.xpath('//a[contains(@href, "/models/")]')

            for link in all_model_links:
                href = link.get('href', '')
                if not href or href == '/models':
                    continue

                # Try to get text content
                text = link.text_content().strip()
                if text and len(text) > 2:
                    full_url = f"https://www.kaggle.com{href}" if href.startswith('/') else href

                    if not any(m['kaggle_url'] == full_url for m in models):
                        models.append({
                            'name': text.split('\n')[0] if '\n' in text else text,
                            'kaggle_url': full_url
                        })
                        print(f"Found: {text}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        if driver:
            driver.quit()

    return models

def save_to_csv(models: List[Dict[str, str]], output_file: str):
    """
    Save scraped models to CSV file

    Args:
        models: List of model dictionaries
        output_file: Path to output CSV file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'kaggle_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for model in models:
            writer.writerow(model)

    print(f"\nSaved {len(models)} models to {output_file}")

def main():
    """Main function to run the scraper"""

    # Target URL
    url = "https://www.kaggle.com/models?owner-type=organization"

    # Output file
    output_file = "output/kaggle_output.csv"

    print("Starting Kaggle Models Scraper")
    print("=" * 50)

    # Scrape models
    models = scrape_kaggle_models(url)

    if models:
        print(f"\nFound {len(models)} models")

        # Display first few models
        print("\nSample of scraped models:")
        for model in models[:5]:
            print(f"  - {model['name']}: {model['kaggle_url']}")

        # Save to CSV
        save_to_csv(models, output_file)
    else:
        print("\nNo models found. The page structure might have changed.")
        print("Consider using Selenium for dynamic content or checking if the page requires authentication.")

        # Save empty CSV with headers
        save_to_csv([], output_file)

    print("\nScraping complete!")

if __name__ == "__main__":
    main()