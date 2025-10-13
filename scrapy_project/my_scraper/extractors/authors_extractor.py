"""
Authors extraction functions
"""

import logging
import time
import re
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html
from my_scraper.extractors.selenium_utils import click_element

logger = logging.getLogger(__name__)


def extract_authors(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                   selectors: Dict, name: str) -> list:
    """
    Extract authors using configured selectors

    Args:
        driver: Selenium driver instance
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        List of author names
    """
    authors = []

    # If no driver, can't extract authors (requires JavaScript rendering)
    if not driver:
        logger.debug(f"No driver provided, skipping authors extraction for {name}")
        return []

    try:
        logger.debug(f"Starting authors extraction for {name}")

        # Try to click the action button if configured (to expand authors section)
        action_selector = selectors.get('authors_action')
        if action_selector:
            try:
                logger.debug(f"Looking for authors action button: {action_selector}")
                button = driver.find_element(By.CSS_SELECTOR, action_selector)

                # Check if the section is collapsed (aria-expanded="false")
                aria_expanded = button.get_attribute('aria-expanded')
                logger.debug(f"Authors section aria-expanded: {aria_expanded}")

                if aria_expanded == 'false':
                    logger.info(f"Expanding authors section for {name}")
                    if click_element(driver, action_selector):
                        time.sleep(0.5)  # Wait for expansion animation
                        # Refresh tree after click
                        tree = lxml_html.fromstring(driver.page_source)
            except Exception as e:
                logger.debug(f"Could not interact with authors action button: {e}")

        # Try CSS selectors via Selenium first
        for selector in selectors.get('authors', []):
            try:
                if selector.startswith('.') or selector.startswith('#') or selector.startswith('p') or selector.startswith('div'):
                    # CSS selector - use Selenium
                    logger.debug(f"Trying authors CSS selector: {selector}")
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.debug(f"Found {len(elements)} author elements")

                    for elem in elements:
                        try:
                            # Get the full text content (includes both anchor text and plain text)
                            text = elem.text.strip()
                            if text:
                                # Split by commas, but keep text in parentheses together
                                parts = re.split(r',\s*(?![^()]*\))', text)
                                for part in parts:
                                    part = part.strip()
                                    # Clean up and filter
                                    if part and part not in authors and len(part) > 2:
                                        # Skip unwanted entries
                                        # 1. Skip if contains newlines
                                        if '\n' in part:
                                            logger.debug(f"Skipping author (contains newline): {part[:50]}")
                                            continue
                                        # 2. Skip header/label text and empty state messages
                                        if part in ['Model development contributors', 'Model release contributors and general support', 'NAME']:
                                            logger.debug(f"Skipping author (header text): {part}")
                                            continue
                                        # 3. Skip empty state messages
                                        if 'does not have any authors' in part.lower():
                                            logger.debug(f"Skipping author (empty state message): {part}")
                                            continue
                                        # 4. Skip if contains role in parentheses (likely a collaborator, not author)
                                        if '(' in part and ')' in part:
                                            logger.debug(f"Skipping author (contains role - likely collaborator): {part}")
                                            continue
                                        # 5. Skip if it's just a URL or common non-author text
                                        if part.startswith('http') or part.startswith('www.'):
                                            logger.debug(f"Skipping author (URL): {part}")
                                            continue

                                        authors.append(part)
                                        logger.debug(f"Found author: {part}")
                        except Exception as e:
                            logger.debug(f"Error extracting text from element: {e}")
                            continue

                    if authors:
                        logger.info(f"Found {len(authors)} authors using CSS selector: {selector}")
                        break
                else:
                    # XPath selector - use lxml
                    logger.debug(f"Trying authors XPath selector: {selector}")
                    elements = tree.xpath(selector)
                    logger.debug(f"Found {len(elements)} author elements via XPath")

                    for elem in elements:
                        try:
                            # Get the full text content (includes both anchor text and plain text)
                            text = elem.text_content().strip()
                            if text:
                                # Split by commas, but keep text in parentheses together
                                parts = re.split(r',\s*(?![^()]*\))', text)
                                for part in parts:
                                    part = part.strip()
                                    # Clean up and filter
                                    if part and part not in authors and len(part) > 2:
                                        # Skip unwanted entries
                                        # 1. Skip if contains newlines
                                        if '\n' in part:
                                            logger.debug(f"Skipping author (contains newline): {part[:50]}")
                                            continue
                                        # 2. Skip header/label text and empty state messages
                                        if part in ['Model development contributors', 'Model release contributors and general support', 'NAME']:
                                            logger.debug(f"Skipping author (header text): {part}")
                                            continue
                                        # 3. Skip empty state messages
                                        if 'does not have any authors' in part.lower():
                                            logger.debug(f"Skipping author (empty state message): {part}")
                                            continue
                                        # 4. Skip if contains role in parentheses (likely a collaborator, not author)
                                        if '(' in part and ')' in part:
                                            logger.debug(f"Skipping author (contains role - likely collaborator): {part}")
                                            continue
                                        # 5. Skip if it's just a URL or common non-author text
                                        if part.startswith('http') or part.startswith('www.'):
                                            logger.debug(f"Skipping author (URL): {part}")
                                            continue

                                        authors.append(part)
                                        logger.debug(f"Found author via XPath: {part}")
                        except Exception as e:
                            logger.debug(f"Error extracting text from XPath element: {e}")
                            continue

                    if authors:
                        logger.info(f"Found {len(authors)} authors using XPath: {selector}")
                        break

            except Exception as e:
                logger.debug(f"Authors selector {selector} failed: {e}")
                continue

        if authors:
            logger.info(f"Successfully extracted {len(authors)} authors for {name}")
        else:
            logger.warning(f"Could not find any authors for {name}")

    except Exception as e:
        logger.error(f"Error extracting authors for {name}: {e}")

    return authors
