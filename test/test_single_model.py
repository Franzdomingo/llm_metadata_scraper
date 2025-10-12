#!/usr/bin/env python3
"""
Single model tag test
Author: Franz Phillip G. Domingo
Date: 2025-10-08
"""

import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from .selectors_config import get_selectors_for_site, GeneralSelectors
except ImportError:
    from selectors_config import get_selectors_for_site, GeneralSelectors

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from lxml import html
import time
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
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

def test_single_model():
    """Test tag extraction on a single model"""
    test_url = "https://www.kaggle.com/models/qwen-lm/qwen-3-vl"
    test_name = "Qwen2.5"
    
    print(f"Testing tag extraction for: {test_name}")
    print(f"URL: {test_url}")
    print("=" * 50)
    
    driver = create_driver()
    
    try:
        driver.get(test_url)
        time.sleep(3)  # Wait for page to load

        # Get page source
        page_source = driver.page_source
        tree = html.fromstring(page_source)

        # Get selectors
        selectors = get_selectors_for_site('kaggle')

        # Test tag extraction with debug info
        from scrape_kaggle_metadata import _extract_tags
        tags = _extract_tags(driver, tree, selectors, test_name)

        print("=" * 50)
        print(f"RESULT: {tags}")

        # Save page source only if explicitly requested by the environment variable
        from print_utils import maybe_print, save_long_text
        # Provide a short preview to stdout instead of dumping full HTML
        maybe_print(page_source, label='PAGE SOURCE PREVIEW', max_chars=1000)
        saved = save_long_text(page_source)
        if saved:
            print(f"Page source saved to {saved}")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_single_model()