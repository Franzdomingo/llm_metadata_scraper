"""
Provenance extraction functions
"""

import logging
import time
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html
from my_scraper.extractors.selenium_utils import click_element

logger = logging.getLogger(__name__)


def extract_provenance(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                      selectors: Dict, name: str) -> str:
    """
    Extract provenance information using configured selectors

    Args:
        driver: Selenium driver instance
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        Provenance information as text
    """
    provenance_text = ""

    # If no driver, can't extract provenance (requires JavaScript rendering)
    if not driver:
        logger.debug(f"No driver provided, skipping provenance extraction for {name}")
        return ""

    try:
        logger.debug(f"Starting provenance extraction for {name}")

        # Try to click the action button if configured (to expand provenance section)
        action_selector = selectors.get('provenance_action')
        if action_selector:
            try:
                logger.debug(f"Looking for provenance action button: {action_selector}")
                button = driver.find_element(By.CSS_SELECTOR, action_selector)

                # Check if the section is collapsed (aria-expanded="false")
                aria_expanded = button.get_attribute('aria-expanded')
                logger.debug(f"Provenance section aria-expanded: {aria_expanded}")

                if aria_expanded == 'false':
                    logger.info(f"Expanding provenance section for {name}")
                    if click_element(driver, action_selector):
                        time.sleep(0.5)  # Wait for expansion animation
                        # Refresh tree after click
                        tree = lxml_html.fromstring(driver.page_source)
            except Exception as e:
                logger.debug(f"Could not interact with provenance action button: {e}")

        # Try CSS selectors via Selenium first
        for selector in selectors.get('provenance', []):
            try:
                if selector.startswith('.') or selector.startswith('#') or selector.startswith('div'):
                    # CSS selector - use Selenium
                    logger.debug(f"Trying provenance CSS selector: {selector}")
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.debug(f"Found {len(elements)} provenance elements")

                    for elem in elements:
                        try:
                            text = elem.text.strip()
                            if text:
                                provenance_text = text
                                logger.info(f"Found provenance using CSS selector: {selector}")
                                break
                        except Exception as e:
                            logger.debug(f"Error extracting text from element: {e}")
                            continue

                    if provenance_text:
                        break
                else:
                    # XPath selector - use lxml
                    logger.debug(f"Trying provenance XPath selector: {selector}")
                    elements = tree.xpath(selector)
                    logger.debug(f"Found {len(elements)} provenance elements via XPath")

                    for elem in elements:
                        try:
                            text = elem.text_content().strip()
                            if text:
                                provenance_text = text
                                logger.info(f"Found provenance using XPath: {selector}")
                                break
                        except Exception as e:
                            logger.debug(f"Error extracting text from XPath element: {e}")
                            continue

                    if provenance_text:
                        break

            except Exception as e:
                logger.debug(f"Provenance selector {selector} failed: {e}")
                continue

        if provenance_text:
            logger.info(f"Successfully extracted provenance for {name}")
        else:
            logger.warning(f"Could not find provenance information for {name}")

    except Exception as e:
        logger.error(f"Error extracting provenance for {name}: {e}")

    return provenance_text
