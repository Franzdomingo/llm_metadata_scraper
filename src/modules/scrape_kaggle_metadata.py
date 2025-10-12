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
import json
from .scraper_settings import (
    build_possible_input_paths,
    DEFAULT_DELAY,
    OUTPUT_JSON_NAME,
    OUTPUT_CSV_NAME,
    START_MESSAGE,
    NOT_FOUND_MESSAGE,
)

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
    """Create and configure a Chrome driver instance.

    This is kept intentionally simple so callers can create a driver once
    and reuse it across multiple scraping operations.
    """
    chrome_options = Options()
    # default to headless; callers can modify this function if they need
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    # Use random user agent from configuration if available
    try:
        user_agent = random.choice(GeneralSelectors.USER_AGENTS)
        chrome_options.add_argument(f'user-agent={user_agent}')
    except Exception:
        logging.debug('No user agents configured, using default browser UA')

    return webdriver.Chrome(options=chrome_options)


def fetch_page(driver: webdriver.Chrome, url: str, wait_seconds: float = 3.0) -> str:
    """Load a page with Selenium and return the page source.

    Keeps the wait logic in one place so callers can control timings
    and helps with reuse in other workflows.
    """
    driver.get(url)
    # Small sleep here to allow dynamic content to settle. Tests calling
    # this function can change or mock wait_seconds as needed.
    time.sleep(wait_seconds)
    return driver.page_source


def parse_tree_from_driver(driver: webdriver.Chrome) -> html.HtmlElement:
    """Create and return an lxml tree from the driver's current page source."""
    page_source = driver.page_source
    return html.fromstring(page_source)

def scrape_model_metadata(driver: webdriver.Chrome, url: str, name: str, selectors: Optional[Dict] = None, model_id: Optional[int] = None) -> Dict[str, str]:
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
        'model_id': model_id,
        'name': name,
        'kaggle_url': url,
        'short_description': '',
        'downloads': '',
        'tags': '',
        'model_card': ''
    }

    try:
        logging.info(f"Scraping: {name}")

        # Load page and parse tree
        fetch_page(driver, url, wait_seconds=3.0)
        # Give a small extra wait for sections to render and for clickable elements
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2")))
            time.sleep(1)
        except Exception:
            logging.debug("h2 not found or waiting timed out; continuing")

        tree = parse_tree_from_driver(driver)

        # Allow caller to supply selectors for reusability in tests or other sites
        if selectors is None:
            selectors = get_selectors_for_site('kaggle')

        # Extract short_description using configured selectors
        metadata['short_description'] = _extract_description(driver, tree, selectors, name)

        # Extract downloads using configured selectors
        metadata['downloads'] = _extract_downloads(tree, selectors, name)

        # Extract model_card using configured selectors (may require clicking an action button)
        try:
            model_card_result = _extract_model_card(driver, tree, selectors, name)
            mc_text = model_card_result.get('text', '') or ''
            links = model_card_result.get('links', []) or []
            if links:
                mc_text = mc_text + '\n\nLinks:\n' + '\n'.join([f"- {l}" for l in links])
            metadata['model_card'] = mc_text
        except Exception as e:
            logging.debug(f"Error extracting model_card for {name}: {e}")

        # Extract tags using configured selectors
        metadata['tags'] = _extract_tags(driver, tree, selectors, name)

        # Extract transformers variations (if any) and attach to metadata
        try:
            metadata['transformers_variation__info'] = _extract_transformers_variations(driver, selectors, name, model_id)
        except Exception as e:
            logging.debug(f"Error extracting transformers variations for {name}: {e}")

        # Create more detailed logging
        desc_preview = metadata['short_description'][:50] if metadata['short_description'] else 'None'
        tags_preview = metadata['tags'][:50] if metadata['tags'] else 'None'
        logging.info(f"{name}: desc='{desc_preview}...', downloads={metadata['downloads']}, tags='{tags_preview}'")

    except Exception as e:
        logging.error(f"Error scraping {name} at {url}: {e}")

    return metadata


def _extract_transformers_variations(driver: webdriver.Chrome, selectors: Dict, name: str, model_id: Optional[int]) -> List[Dict[str, object]]:
    """
    Extract transformers_variation entries by clicking the variation dropdown (if present)

    Returns a list of dicts matching the schema fields (most fields will be empty if not
    available on the model page).
    """
    variations = []

    if not selectors:
        return variations

    action_selector = selectors.get('transformers_variation_action')
    item_selector = selectors.get('transformers_variation_item')

    # Try to click the action that reveals the list
    try:
        if action_selector:
            logging.debug(f"Trying to click transformers variation action: {action_selector}")
            action_el = driver.find_element(By.CSS_SELECTOR, action_selector)
            try:
                action_el.click()
                time.sleep(0.5)
            except Exception:
                logging.debug("Click on transformers variation action failed; attempting JavaScript click")
                driver.execute_script("arguments[0].click();", action_el)
                time.sleep(0.5)
    except Exception as e:
        logging.debug(f"Could not click transformers variation action for {name}: {e}")

    elems = []
    # Prefer a general list item selector if available
    try:
        # Try common pattern first
        elems = driver.find_elements(By.CSS_SELECTOR, 'li.MuiButtonBase-root')
        if not elems and item_selector:
            elems = driver.find_elements(By.CSS_SELECTOR, item_selector)
    except Exception:
        # Fallback to the configured item selector only
        try:
            if item_selector:
                elems = driver.find_elements(By.CSS_SELECTOR, item_selector)
        except Exception:
            elems = []

    for el in elems:
        try:
            text = el.text.strip()
            if not text:
                # try inner p element
                try:
                    p = el.find_element(By.CSS_SELECTOR, 'p')
                    text = p.text.strip()
                except Exception:
                    text = ''

            if text:
                variations.append({
                    'model_id': model_id,
                    'transformers_variation': text,
                    'transformers_variation_version': '',
                    'transformers_variation_license': '',
                    'transformers_variation_downloads': '',
                    'transformers_model_card': '',
                    'transformers_description': ''
                })
        except Exception:
            continue

    # If we found nothing, return empty list
    return variations


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

    # First try CSS selectors (via Selenium) - these are more reliable for dynamic content
    for selector in selectors.get('description', []):
        if selector.startswith('.') or selector.startswith('#'):
            try:
                logging.debug(f"Trying description CSS selector via Selenium: {selector}")
                desc_element = driver.find_element(By.CSS_SELECTOR, selector)
                # Return outerHTML so the caller can inspect formatting if needed
                outer = desc_element.get_attribute('outerHTML')
                if outer and outer.strip():
                    logging.info(f"Found short_description (outerHTML) using CSS selector: {selector}")
                    # convert HTML to cleaned plain text before returning
                    return _html_to_text(outer)
            except Exception as e:
                logging.debug(f"Description CSS selector {selector} not found via Selenium: {e}")

    # Next try XPath selectors using lxml tree
    for selector in selectors.get('description', []):
        # Skip CSS selectors here
        if selector.startswith('.') or selector.startswith('#'):
            continue
        try:
            logging.debug(f"Trying description XPath selector: {selector}")
            desc_elements = tree.xpath(selector)
            if desc_elements and desc_elements[0].text_content().strip():
                logging.info(f"Found short_description using XPath selector: {selector}")
                return desc_elements[0].text_content().strip()
        except Exception as e:
            logging.debug(f"Description XPath selector {selector} failed: {e}")

    # Final fallback: use configured CSS fallback (Selenium) and return outerHTML
    if 'description_css_fallback' in selectors:
        try:
            desc_element = driver.find_element(By.CSS_SELECTOR, selectors['description_css_fallback'])
            outer = desc_element.get_attribute('outerHTML')
            if outer and outer.strip():
                logging.info(f"Found short_description (outerHTML) using fallback CSS selector")
                return _html_to_text(outer)
        except Exception:
            logging.warning(f"Could not find short_description for {name}")

    return description


def _html_to_text(html_snippet: str) -> str:
    """Convert an HTML snippet (outerHTML) into cleaned plain text.

    Uses lxml to parse and extract text_content(), then collapses whitespace.
    """
    if not html_snippet:
        return ''

    try:
        node = html.fromstring(html_snippet)
        text = node.text_content() or ''
    except Exception:
        # Fallback: remove tags with a simple regex
        text = re.sub(r'<[^>]+>', ' ', html_snippet)

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


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


def _extract_model_card(driver: webdriver.Chrome, tree, selectors: Dict, name: str) -> Dict[str, object]:
    """
    Extract the model_card text and links. Attempts to click a configured action button
    before extraction to reveal hidden content.

    Returns a dict with keys: 'text' (str) and 'links' (List[str])
    """
    result = {'text': '', 'links': []}

    # Attempt to click an action button if configured
    action_selector = selectors.get('model_card_action')
    if action_selector:
        try:
            logging.debug(f"Attempting to click model_card action: {action_selector}")
            try:
                wait = WebDriverWait(driver, 6)
                btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, action_selector)))
                btn.click()
                logging.debug("Clicked model_card action via Selenium click")
                time.sleep(1)
            except Exception as e_click:
                logging.debug(f"Selenium click failed ({e_click}), trying JS click")
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, action_selector)
                    driver.execute_script("arguments[0].click();", btn)
                    logging.debug("Clicked model_card action via JS")
                    time.sleep(1)
                except Exception as e_js:
                    logging.debug(f"JS click failed: {e_js}")
        except Exception as e:
            logging.debug(f"Action click attempt error: {e}")

    # Refresh tree after any click
    page_source = driver.page_source
    tree = html.fromstring(page_source)

    # Try CSS selectors via Selenium first
    for sel in selectors.get('model_card_selectors', []):
        try:
            logging.debug(f"Trying model_card CSS selector via Selenium: {sel}")
            el = driver.find_element(By.CSS_SELECTOR, sel)
            text = el.text.strip()
            if text:
                result['text'] = text
                # extract anchor hrefs
                try:
                    anchors = el.find_elements(By.TAG_NAME, 'a')
                    for a in anchors:
                        href = a.get_attribute('href')
                        if href:
                            result['links'].append(href)
                except Exception:
                    logging.debug('No anchors found via Selenium in model_card element')

                logging.info(f"Found model_card using Selenium selector: {sel}")
                return result
        except Exception as e:
            logging.debug(f"model_card CSS selector {sel} not found via Selenium: {e}")

    # Fallback to XPath using lxml
    fallback_xpaths = [
        '//div[contains(@class, "sc-lkCrJH")][1]',
        '//div[contains(@class, "sc-chzmIZ")]/div[1]'
    ]

    for xp in fallback_xpaths:
        try:
            elems = tree.xpath(xp)
            if elems:
                text = elems[0].text_content().strip()
                if text:
                    result['text'] = text
                    try:
                        anchor_nodes = elems[0].xpath('.//a')
                        for node in anchor_nodes:
                            href = node.get('href')
                            if href:
                                result['links'].append(href)
                    except Exception:
                        logging.debug('No anchors found via lxml in model_card element')

                    logging.info(f"Found model_card using XPath fallback: {xp}")
                    return result
        except Exception as e:
            logging.debug(f"XPath {xp} failed: {e}")

    logging.warning(f"Could not find model_card for {name}")
    return result


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


def scrape_models(driver: webdriver.Chrome, models: List[Dict[str, str]], selectors: Optional[Dict] = None, delay: float = 1.0) -> List[Dict[str, str]]:
    """Scrape a list of models using a shared Selenium driver.

    Args:
        driver: Selenium webdriver instance to reuse across requests
        models: List of dicts with keys 'name' and 'kaggle_url'
        selectors: Optional selectors mapping to pass to each scrape
        delay: Seconds to wait between scraping each model

    Returns:
        List of metadata dictionaries
    """
    results = []

    # Generate sequential model_id starting at 1 for each model processed
    for i, model in enumerate(models, 1):
        name = model.get('name')
        url = model.get('kaggle_url')
        model_id = i  # integer ID (1, 2, 3, ...). If zero-padded string is desired use f"{i:02d}"
        logging.info(f"Processing {i}/{len(models)}: {name} (model_id={model_id})")
        metadata = scrape_model_metadata(driver, url, name, selectors=selectors, model_id=model_id)
        results.append(metadata)
        time.sleep(delay)

    return results


def save_to_json(metadata_list: List[Dict[str, str]], output_file: str):
    """
    Save scraped metadata to JSON file

    Args:
        metadata_list: List of metadata dictionaries
        output_file: Path to output JSON file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write pretty-printed JSON with UTF-8 encoding
    with open(output_file, 'w', encoding='utf-8') as jf:
        json.dump(metadata_list, jf, ensure_ascii=False, indent=2)

    logging.info(f"Saved {len(metadata_list)} model metadata to {output_file} (JSON)")


# CSV output removed — script now saves JSON only

def main():
    """Main function to run the metadata scraper"""

    # Configuration - handle both root and modules directory execution
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up two levels from modules
    
    # Build possible input file paths and pick the first existing
    possible_input_paths = build_possible_input_paths(project_root)
    input_file = None
    for path in possible_input_paths:
        if os.path.exists(path):
            input_file = path
            break
    
    # Set output file relative to input file location
    if input_file:
        input_dir = os.path.dirname(input_file)
        output_file = os.path.join(input_dir, "kaggle_metadata.csv")
        output_json = os.path.join(input_dir, "kaggle_metadata.json")
    else:
        # Default fallback
        output_file = "output/kaggle_metadata.csv"
        output_json = "output/kaggle_metadata.json"

    # Minimal user-facing start message
    print(START_MESSAGE)

    # Check if input file exists
    if not input_file:
        print(NOT_FOUND_MESSAGE)
        for path in possible_input_paths:
            print(f" - {path}")
        return

    start_time = time.time()

    # Read input models
    models = read_kaggle_input(input_file)

    if not models:
        print("No models found in input file.")
        return

    print(f"Scraping {len(models)} models...")

    # Create driver and run batch scraping (re-usable entry point)
    driver = create_driver()
    try:
        metadata_list = scrape_models(driver, models, selectors=None, delay=DEFAULT_DELAY)
    finally:
        driver.quit()

    elapsed_time = time.time() - start_time

    # Save results as JSON only
    save_to_json(metadata_list, output_json)

    # Minimal summary for user
    print(f"Scraping complete: {len(metadata_list)} models processed in {elapsed_time:.2f}s")
    print(f"Results saved to: {output_json}")

if __name__ == "__main__":
    main()
