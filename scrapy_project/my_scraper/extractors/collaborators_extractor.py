"""
Collaborators extraction functions
"""

import logging
import time
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html
from my_scraper.extractors.selenium_utils import click_element

logger = logging.getLogger(__name__)


def extract_collaborators(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                         selectors: Dict, name: str) -> list:
    """
    Extract collaborators using configured selectors

    Args:
        driver: Selenium driver instance
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        List of collaborator names
    """
    collaborators = []

    # If no driver, can't extract collaborators (requires JavaScript rendering)
    if not driver:
        logger.debug(f"No driver provided, skipping collaborators extraction for {name}")
        return []

    try:
        logger.debug(f"Starting collaborator extraction for {name}")

        # Try to click the action button if configured (to expand collaborators section)
        action_selector = selectors.get('collaborators_action')
        if action_selector:
            try:
                logger.debug(f"Looking for collaborators action button: {action_selector}")
                button = driver.find_element(By.CSS_SELECTOR, action_selector)

                # Check if the section is collapsed (aria-expanded="false")
                aria_expanded = button.get_attribute('aria-expanded')
                logger.debug(f"Collaborators section aria-expanded: {aria_expanded}")

                if aria_expanded == 'false':
                    logger.info(f"Expanding collaborators section for {name}")
                    if click_element(driver, action_selector):
                        time.sleep(0.5)  # Wait for expansion animation
                        # Refresh tree after click
                        tree = lxml_html.fromstring(driver.page_source)
            except Exception as e:
                logger.debug(f"Could not interact with collaborators action button: {e}")

        # Try CSS selectors via Selenium first
        for selector in selectors.get('collaborators', []):
            try:
                if selector.startswith('.') or selector.startswith('#') or selector.startswith('p') or selector.startswith('div'):
                    # CSS selector - use Selenium
                    logger.debug(f"Trying collaborator CSS selector: {selector}")
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.debug(f"Found {len(elements)} collaborator elements")

                    for elem in elements:
                        try:
                            text = elem.text.strip()
                            # Filter out empty text and duplicates
                            if text and text not in collaborators:
                                # Skip unwanted entries
                                # 1. Skip if contains newlines
                                if '\n' in text:
                                    logger.debug(f"Skipping collaborator (contains newline): {text[:50]}")
                                    continue
                                # 2. Skip navigation/UI elements
                                if any(keyword in text for keyword in ['trending_up', '·', 'JAX', 'Models', 'Version']):
                                    logger.debug(f"Skipping collaborator (UI element): {text}")
                                    continue
                                # 3. Skip very short text (likely not a name)
                                if len(text) <= 2:
                                    logger.debug(f"Skipping collaborator (too short): {text}")
                                    continue
                                # 4. Skip if it's a number or mostly numbers
                                if text.replace(' ', '').isdigit():
                                    logger.debug(f"Skipping collaborator (numeric): {text}")
                                    continue

                                # Additional filter: ensure it looks like a collaborator entry
                                # MUST have format "name (role)" with role in parentheses
                                if '(' in text and ')' in text:
                                    collaborators.append(text)
                                    logger.debug(f"Found collaborator: {text}")
                                else:
                                    logger.debug(f"Skipping collaborator (no role in parentheses): {text}")
                        except Exception as e:
                            logger.debug(f"Error extracting text from element: {e}")
                            continue

                    if collaborators:
                        logger.info(f"Found {len(collaborators)} collaborators using CSS selector: {selector}")
                        break
                else:
                    # XPath selector - use lxml
                    logger.debug(f"Trying collaborator XPath selector: {selector}")
                    elements = tree.xpath(selector)
                    logger.debug(f"Found {len(elements)} collaborator elements via XPath")

                    for elem in elements:
                        try:
                            text = elem.text_content().strip()
                            if text and text not in collaborators:
                                # Skip unwanted entries
                                # 1. Skip if contains newlines
                                if '\n' in text:
                                    logger.debug(f"Skipping collaborator (contains newline): {text[:50]}")
                                    continue
                                # 2. Skip navigation/UI elements
                                if any(keyword in text for keyword in ['trending_up', '·', 'JAX', 'Models', 'Version']):
                                    logger.debug(f"Skipping collaborator (UI element): {text}")
                                    continue
                                # 3. Skip very short text (likely not a name)
                                if len(text) <= 2:
                                    logger.debug(f"Skipping collaborator (too short): {text}")
                                    continue
                                # 4. Skip if it's a number or mostly numbers
                                if text.replace(' ', '').isdigit():
                                    logger.debug(f"Skipping collaborator (numeric): {text}")
                                    continue

                                # Same filtering as above - MUST have format "name (role)"
                                if '(' in text and ')' in text:
                                    collaborators.append(text)
                                    logger.debug(f"Found collaborator via XPath: {text}")
                                else:
                                    logger.debug(f"Skipping collaborator (no role in parentheses): {text}")
                        except Exception as e:
                            logger.debug(f"Error extracting text from XPath element: {e}")
                            continue

                    if collaborators:
                        logger.info(f"Found {len(collaborators)} collaborators using XPath: {selector}")
                        break

            except Exception as e:
                logger.debug(f"Collaborator selector {selector} failed: {e}")
                continue

        if collaborators:
            logger.info(f"Successfully extracted {len(collaborators)} collaborators for {name}")
        else:
            logger.warning(f"Could not find any collaborators for {name}")

    except Exception as e:
        logger.error(f"Error extracting collaborators for {name}: {e}")

    return collaborators
