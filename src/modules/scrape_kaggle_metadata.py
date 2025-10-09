#!/usr/bin/env python3
"""
Kaggle Metadata Scraper
Scrapes metadata (short_descri        # Extract short_description using configured selectors
        metadata['short_description'] = _extract_description(driver, tree, selectors, name)

        # Extract downloads using configured selectors
        metadata['downloads'] = _extract_downloads(tree, selectors, name)

        # Extract tags using configured selectors
        metadata['tags'] = _extract_tags(driver, tree, selectors, name)

        # Create more detailed logging
        desc_preview = metadata['short_description'][:50] if metadata['short_description'] else 'None'
        tags_preview = metadata['tags'][:50] if metadata['tags'] else 'None'
        logging.info(f" {name}: desc='{desc_preview}...', downloads={metadata['downloads']}, tags='{tags_preview}'")downloads) from Kaggle model pages
Author: Franz Phillip G. Domingo
Date: 2025-10-08
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
import re
from typing import List, Dict, Optional
import logging
import random

# Import selectors configuration
try:
    from .selectors_config import get_selectors_for_site, GeneralSelectors
except ImportError:
    # Fallback for direct execution
    from selectors_config import get_selectors_for_site, GeneralSelectors

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Enable debug logging temporarily
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

def create_driver() -> webdriver.Chrome:
    """Create and configure a Chrome driver instance"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Use random user agent from configuration
    user_agent = random.choice(GeneralSelectors.USER_AGENTS)
    chrome_options.add_argument(f'user-agent={user_agent}')

    return webdriver.Chrome(options=chrome_options)

def scrape_model_metadata(driver: webdriver.Chrome, url: str, name: str) -> Dict[str, str]:
    """
    Scrape metadata from a single Kaggle model page

    Args:
        driver: Selenium Chrome driver instance
        url: The Kaggle model URL
        name: The model name from kaggle_output.csv

    Returns:
        Dictionary containing name, url, short_description, downloads, and tags
    """
    metadata = {
        'name': name,
        'kaggle_url': url,
        'short_description': '',
        'downloads': '',
        'tags': ''
    }

    try:
        logging.info(f"Scraping: {name}")
        driver.get(url)

        # Wait for page to load
        wait = WebDriverWait(driver, 20)
        time.sleep(3)  # Additional wait for dynamic content
        
        # Wait specifically for tags section to load
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2")))
            time.sleep(2)  # Extra wait for tags to render
        except:
            logging.debug("Could not wait for tags section, continuing anyway")

        # Get page source
        page_source = driver.page_source
        tree = html.fromstring(page_source)

        # Get selectors configuration
        selectors = get_selectors_for_site('kaggle')

        # Extract short_description using configured selectors
        metadata['short_description'] = _extract_description(driver, tree, selectors, name)

        # Extract downloads using configured selectors
        metadata['downloads'] = _extract_downloads(tree, selectors, name)

        logging.info(f" {name}: desc='{metadata['short_description'][:50]}...', downloads={metadata['downloads']}")
        # Extract tags using configured selectors (was missing)
        metadata['tags'] = _extract_tags(driver, tree, selectors, name)

        # Create more detailed logging
        desc_preview = metadata['short_description'][:50] if metadata['short_description'] else 'None'
        tags_preview = metadata['tags'][:50] if metadata['tags'] else 'None'
        logging.info(f"{name}: desc='{desc_preview}...', downloads={metadata['downloads']}, tags='{tags_preview}'")

    except Exception as e:
        logging.error(f"Error scraping {name} at {url}: {e}")

    return metadata


def _extract_description(driver: webdriver.Chrome, tree, selectors: Dict, name: str) -> str:
    """
    Extract description using configured selectors
    
    Args:
        driver: Selenium driver instance
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging
        
    Returns:
        Extracted description text or empty string
    """
    description = ""
    
    # Try XPath selectors first
    for selector in selectors.get('description', []):
        # Skip CSS selector (it's handled separately)
        if selector.startswith('.sc-'):
            continue
            
        try:
            desc_elements = tree.xpath(selector)
            if desc_elements and desc_elements[0].text_content().strip():
                description = desc_elements[0].text_content().strip()
                break
        except Exception:
            continue

    # If still not found, try CSS selector approach through Selenium
    if not description and 'description_css_fallback' in selectors:
        try:
            desc_element = driver.find_element(By.CSS_SELECTOR, selectors['description_css_fallback'])
            description = desc_element.text.strip()
        except Exception:
            logging.warning(f"Could not find short_description for {name}")
    
    return description


def _extract_downloads(tree, selectors: Dict, name: str) -> str:
    """
    Extract download count using configured selectors
    
    Args:
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging
        
    Returns:
        Extracted download count or empty string
    """
    downloads = ""
    
    # Try primary download selectors
    for selector in selectors.get('downloads', []):
        try:
            download_elements = tree.xpath(selector)
            if download_elements:
                # Get all elements and look for numeric values
                for elem in download_elements:
                    text = elem.text_content().strip()
                    # Check if it's a number (could be "399" or "1.2K" etc)
                    if text and _is_numeric_value(text):
                        downloads = text
                        break
                if downloads:
                    break
        except Exception:
            continue

    if not downloads:
        logging.warning(f"Could not find downloads for {name}")
    
    return downloads


def _is_numeric_value(text: str) -> bool:
    """
    Check if text represents a numeric value (including K/M suffixes)
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be a numeric value
    """
    
    # Simple digit check
    if text.isdigit():
        return True
    
    # Check against numeric patterns from config
    for pattern in GeneralSelectors.NUMERIC_PATTERNS:
        if re.match(pattern, text):
            return True
    
    # Fallback: check for common download indicators
    return bool(re.match(r'\d+[KkMmBb]?', text) or 
               ('K' in text and any(char.isdigit() for char in text)) or
               ('M' in text and any(char.isdigit() for char in text)))


def _extract_tags(driver: webdriver.Chrome, tree, selectors: Dict, name: str) -> str:
    """
    Extract tags using configured selectors
    
    Args:
        driver: Selenium driver instance
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging
        
    Returns:
        Comma-separated string of tags or empty string
    """
    tags = []

    try:
        logging.debug(f"Starting tag extraction for {name}")

        # First try the specific tag link selector
        tag_link_selector = selectors.get('tag_links')
        if tag_link_selector:
            logging.debug(f"Trying specific tag link selector: {tag_link_selector}")
            try:
                tag_links = driver.find_elements(By.CSS_SELECTOR, tag_link_selector)
                logging.debug(f"Found {len(tag_links)} tag links")
                
                for link in tag_links:
                    try:
                        tag_text = link.text.strip()
                        if tag_text and tag_text not in tags:
                            tags.append(tag_text)
                            logging.debug(f"Added tag: '{tag_text}'")
                    except Exception as e:
                        logging.debug(f"Error extracting text from tag link: {e}")
                        continue
                        
                if tags:
                    logging.info(f"Found {len(tags)} tags using specific selector: {tags}")
                    return ', '.join(tags)
                    
            except Exception as e:
                logging.debug(f"Specific tag link selector failed: {e}")

        # If specific selector failed, try container selectors
        for i, selector in enumerate(selectors.get('tags', []), 1):
            logging.debug(f"Trying tag container selector {i}: {selector}")
            try:
                if selector.startswith('.') or selector.startswith('#'):
                    # CSS selector - use Selenium
                    tag_containers = driver.find_elements(By.CSS_SELECTOR, selector)
                    logging.debug(f"Found {len(tag_containers)} containers with CSS selector")
                    
                    for container in tag_containers:
                        # Look for anchor tags within the container
                        anchor_tags = container.find_elements(By.TAG_NAME, 'a')
                        logging.debug(f"Found {len(anchor_tags)} anchor tags in container")
                        
                        for anchor in anchor_tags:
                            try:
                                tag_text = anchor.text.strip()
                                if tag_text and tag_text not in tags:
                                    tags.append(tag_text)
                                    logging.debug(f"Added tag: '{tag_text}'")
                            except Exception as e:
                                logging.debug(f"Error extracting anchor text: {e}")
                                continue
                else:
                    # XPath selector - use lxml
                    tag_elements = tree.xpath(selector)
                    logging.debug(f"Found {len(tag_elements)} elements with XPath selector")
                    
                    for elem in tag_elements:
                        # Look for anchor tags within the element
                        anchor_elements = elem.xpath('.//a')
                        logging.debug(f"Found {len(anchor_elements)} anchor elements")
                        
                        for anchor in anchor_elements:
                            try:
                                tag_text = anchor.text_content().strip()
                                if tag_text and tag_text not in tags:
                                    tags.append(tag_text)
                                    logging.debug(f"Added tag: '{tag_text}'")
                            except Exception as e:
                                logging.debug(f"Error extracting element text: {e}")
                                continue

                if tags:  # Stop if we found tags
                    logging.debug(f"Found {len(tags)} tags with container selector, stopping search")
                    break

            except Exception as e:
                logging.debug(f"Container selector {selector} failed: {e}")
                continue

        # Final result logging
        if tags:
            logging.info(f"Successfully extracted {len(tags)} tags for {name}: {tags}")
        else:
            logging.warning(f"Could not find any tags for {name}")

    except Exception as e:
        logging.error(f"Error extracting tags for {name}: {e}")

    # Return as comma-separated string
    return ', '.join(tags) if tags else ''


def read_kaggle_input(input_file: str) -> List[Dict[str, str]]:
    """
    Read the kaggle_output.csv file

    Args:
        input_file: Path to kaggle_output.csv

    Returns:
        List of dictionaries with name and kaggle_url
    """
    models = []

    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            models.append({
                'name': row['name'],
                'kaggle_url': row['kaggle_url']
            })

    logging.info(f"Loaded {len(models)} models from {input_file}")
    return models

def save_to_csv(metadata_list: List[Dict[str, str]], output_file: str):
    """
    Save scraped metadata to CSV file

    Args:
        metadata_list: List of metadata dictionaries
        output_file: Path to output CSV file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'kaggle_url', 'short_description', 'downloads', 'tags']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for metadata in metadata_list:
            writer.writerow(metadata)

    logging.info(f"Saved {len(metadata_list)} model metadata to {output_file}")

def main():
    """Main function to run the metadata scraper"""

    # Configuration - handle both root and modules directory execution
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up two levels from modules
    
    # Try to find the input file in multiple locations
    possible_input_paths = [
        "output/kaggle_output.csv",  # From root directory
        "../../output/kaggle_output.csv",  # From modules directory
        os.path.join(project_root, "output", "kaggle_output.csv")  # Absolute path
    ]
    
    input_file = None
    for path in possible_input_paths:
        if os.path.exists(path):
            input_file = path
            break
    
    # Set output file relative to input file location
    if input_file:
        input_dir = os.path.dirname(input_file)
        output_file = os.path.join(input_dir, "kaggle_metadata.csv")
    else:
        # Default fallback
        output_file = "output/kaggle_metadata.csv"

    print("=" * 60)
    print("Kaggle Metadata Scraper")
    print("=" * 60)

    # Check if input file exists
    if not input_file:
        print("Error: Input file 'kaggle_output.csv' not found in any of these locations:")
        for path in possible_input_paths:
            print(f"  - {path}")
        print("\nPlease ensure the kaggle_output.csv file exists in the output directory.")
        return

    start_time = time.time()

    # Read input models
    models = read_kaggle_input(input_file)

    if not models:
        print("No models found in input file.")
        return

    print(f"\nScraping metadata for {len(models)} models...")

    # Create driver
    driver = create_driver()
    metadata_list = []

    try:
        for i, model in enumerate(models, 1):
            print(f"\n[{i}/{len(models)}] Processing: {model['name']}")

            metadata = scrape_model_metadata(driver, model['kaggle_url'], model['name'])
            metadata_list.append(metadata)

            # Small delay between requests to be respectful
            time.sleep(1)

    finally:
        driver.quit()

    elapsed_time = time.time() - start_time

    # Save results
    save_to_csv(metadata_list, output_file)

    # Display summary
    print("\n" + "=" * 60)
    print(f"Scraping complete!")
    print(f"Total models processed: {len(metadata_list)}")
    print(f"Execution time: {elapsed_time:.2f} seconds")

    # Show sample results
    print("\nSample results:")
    for metadata in metadata_list[:3]:
        print(f"\n  Name: {metadata['name']}")
        print(f"  URL: {metadata['kaggle_url']}")
        print(f"  Description: {metadata['short_description'][:80]}...")
        print(f"  Downloads: {metadata['downloads']}")
        print(f"  Tags: {metadata['tags']}")

    print(f"\nFull results saved to: {output_file}")

if __name__ == "__main__":
    main()
