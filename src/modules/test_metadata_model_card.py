#!/usr/bin/env python3
"""
Test scraper for Kaggle `model_card` metadata

This small, standalone test script extracts the "model_card" text using the
CSS selectors you provided:
  - div.sc-lkCrJH:nth-child(1)
  - .sc-chzmIZ > div:nth-child(1)

It uses Selenium (Chrome) and mirrors the project's driver options so it can be
used interactively during development.

Run: python src/modules/test_metadata_model_card.py

Author: Copied-style from project files
Date: 2025-10-09
"""

import sys
import os
import time
import logging
import random
import argparse

from typing import Optional, Dict

try:
    # allow running from src/modules or project root
    from .selectors_config import get_selectors_for_site, GeneralSelectors
except Exception:
    from selectors_config import get_selectors_for_site, GeneralSelectors

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

MODEL_CARD_SELECTORS = [
    'div.sc-lkCrJH:nth-child(1)',
    '.sc-chzmIZ > div:nth-child(1)'
]


def create_driver() -> webdriver.Chrome:
    """Create a Chrome webdriver configured like the project's other scripts."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    # Use a configured user-agent if available
    try:
        ua = random.choice(GeneralSelectors.USER_AGENTS)
        chrome_options.add_argument(f'user-agent={ua}')
    except Exception:
        pass

    return webdriver.Chrome(options=chrome_options)


def extract_model_card(driver: webdriver.Chrome, url: str, name: str = "") -> Dict[str, Optional[str]]:
    """Open `url` and attempt to extract the model_card text using CSS selectors.

    Returns dict with keys: name, url, model_card
    """
    result = {'name': name, 'url': url, 'model_card': '', 'links': []}

    logging.info(f"Loading page: {url}")
    driver.get(url)
    time.sleep(3)

    # Attempt to press the action button that may reveal the model card
    action_selector = '.sc-kHBIib > span:nth-child(2)'
    try:
        logging.info(f"Attempting to click action button: {action_selector}")
        try:
            wait = WebDriverWait(driver, 6)
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, action_selector)))
            btn.click()
            logging.info("Clicked action button via Selenium click")
            time.sleep(1)
        except Exception as e_click:
            logging.debug(f"Selenium click failed ({e_click}), trying JS click")
            try:
                btn = driver.find_element(By.CSS_SELECTOR, action_selector)
                driver.execute_script("arguments[0].click();", btn)
                logging.info("Clicked action button via JS")
                time.sleep(1)
            except Exception as e_js:
                logging.debug(f"JS click failed: {e_js}")
    except Exception as e:
        logging.debug(f"Action button click attempt failed: {e}")

    # After any click attempt, re-read the page source to capture dynamic changes
    page_source = driver.page_source
    tree = html.fromstring(page_source)

    # Try Selenium CSS selectors first (more robust for dynamic content)
    for sel in MODEL_CARD_SELECTORS:
        try:
            logging.debug(f"Trying Selenium CSS selector: {sel}")
            el = driver.find_element(By.CSS_SELECTOR, sel)
            text = el.text.strip()
            if text:
                result['model_card'] = text
                # extract all anchor links inside the element
                try:
                    anchors = el.find_elements(By.TAG_NAME, 'a')
                    for a in anchors:
                        try:
                            href = a.get_attribute('href')
                            link_text = a.text.strip()
                            if href:
                                result['links'].append({'text': link_text, 'href': href})
                        except Exception:
                            continue
                except Exception:
                    logging.debug('No anchors found via Selenium in model_card element')

                logging.info(f"Found model_card using Selenium selector: {sel}")
                return result
        except Exception as e:
            logging.debug(f"Selector {sel} not found via Selenium: {e}")

    # Fallback: try to locate via lxml XPath by converting CSS -> XPath manually for these selectors
    # We'll attempt a couple of conservative XPaths that should match the intended elements
    fallback_xpaths = [
        '//div[contains(@class, "sc-lkCrJH")][1]',
        '//div[contains(@class, "sc-chzmIZ")]/div[1]'
    ]

    for xp in fallback_xpaths:
        try:
            logging.debug(f"Trying lxml XPath selector: {xp}")
            elems = tree.xpath(xp)
            if elems:
                # text_content provides combined descendant text
                text = elems[0].text_content().strip()
                if text:
                    result['model_card'] = text
                    # extract anchor tags via lxml
                    try:
                        anchor_nodes = elems[0].xpath('.//a')
                        for node in anchor_nodes:
                            try:
                                href = node.get('href')
                                link_text = node.text_content().strip()
                                if href:
                                    result['links'].append({'text': link_text, 'href': href})
                            except Exception:
                                continue
                    except Exception:
                        logging.debug('No anchors found via lxml in model_card element')

                    logging.info(f"Found model_card using XPath fallback: {xp}")
                    return result
        except Exception as e:
            logging.debug(f"XPath {xp} failed: {e}")

    logging.warning(f"Could not find model_card for {name or url}")
    return result


def main():
    parser = argparse.ArgumentParser(description='Test extract model_card from a Kaggle model page')
    parser.add_argument('--url', '-u', default='https://www.kaggle.com/models/keras/gemma/', help='Kaggle model URL to test')
    parser.add_argument('--name', '-n', default='qwen-3-vl', help='Name to label the output')
    parser.add_argument('--out', '-o', default=os.path.join('output', 'testoutput.txt'), help='Output file path to save full result')

    args = parser.parse_args()

    test_url = args.url
    test_name = args.name
    out_path = args.out

    driver = create_driver()
    try:
        res = extract_model_card(driver, test_url, test_name)

        # Print to stdout
        print('\n--- RESULT ---')
        print(f"Name: {res['name']}")
        print(f"URL: {res['url']}")
        print("model_card:\n")
        print(res['model_card'] or "<empty>")
        print()
        if res.get('links'):
            print('Links found:')
            for link in res['links']:
                print(f" - {link.get('text','(no text)')}: {link.get('href')}")
            print()
        print()

        # Ensure output directory exists and write full result to file
        out_dir = os.path.dirname(out_path) or '.'
        os.makedirs(out_dir, exist_ok=True)

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('--- RESULT ---\n')
            f.write(f"Name: {res['name']}\n")
            f.write(f"URL: {res['url']}\n")
            f.write('model_card:\n\n')
            f.write(res['model_card'] or '<empty>')
            f.write('\n\n')
            if res.get('links'):
                f.write('Links:\n')
                for link in res['links']:
                    f.write(f"- {link.get('text','(no text)')}: {link.get('href')}\n")
            f.write('\n')

        print(f"Saved result to: {out_path}")
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
