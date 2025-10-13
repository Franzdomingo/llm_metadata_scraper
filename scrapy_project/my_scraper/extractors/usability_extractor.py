"""
Usability extraction functions
"""

import logging
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html

logger = logging.getLogger(__name__)


def extract_usability(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                      selectors: Dict, name: str) -> str:
    """
    Extract usability score using configured selectors

    Args:
        driver: Selenium driver instance (for dynamic content)
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        Extracted usability score or empty string
    """
    usability = ""

    # If no driver, can't extract usability (requires JavaScript rendering)
    if not driver:
        logger.debug(f"No driver provided, skipping usability extraction for {name}")
        return usability

    # Try CSS selectors via Selenium for dynamic content
    for selector in selectors.get('usability', []):
        # Check if it's a CSS selector
        if selector.startswith('.') or selector.startswith('#') or selector.startswith('p') or selector.startswith('div'):
            try:
                logger.debug(f"Trying usability CSS selector via Selenium: {selector}")
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.debug(f"Found {len(elements)} elements with CSS selector")

                for elem in elements:
                    try:
                        text = elem.text.strip()
                        logger.debug(f"Checking element text: '{text}'")
                        if text:
                            # Found a valid value - return it immediately
                            logger.info(f"Found usability using selector '{selector}': {text}")
                            return text
                    except Exception as e:
                        logger.debug(f"Error getting text from element: {e}")
                        continue
            except Exception as e:
                logger.debug(f"Usability CSS selector {selector} failed: {e}")

    # Try XPath selectors using lxml tree as fallback
    for selector in selectors.get('usability', []):
        # Skip CSS selectors (already tried above)
        if selector.startswith('.') or selector.startswith('#') or selector.startswith('p') or selector.startswith('div'):
            continue

        try:
            logger.debug(f"Trying usability XPath selector: {selector}")
            usability_elements = tree.xpath(selector)
            logger.debug(f"Found {len(usability_elements)} elements with XPath")

            if usability_elements:
                for elem in usability_elements:
                    text = elem.text_content().strip()
                    logger.debug(f"Checking element text: '{text}'")
                    if text:
                        # Found a valid value - return it immediately
                        logger.info(f"Found usability using XPath '{selector}': {text}")
                        return text
        except Exception as e:
            logger.debug(f"Usability XPath selector {selector} failed: {e}")
            continue

    # Fallback: Search for text near "Usability" heading
    if not usability:
        logger.debug(f"Trying fallback: searching for usability near 'Usability' heading")
        try:
            # Find the Usability heading and look for siblings/nearby elements
            usability_heading = driver.find_elements(By.XPATH, "//*[contains(text(), 'Usability')]")

            if usability_heading:
                logger.debug(f"Found {len(usability_heading)} 'Usability' headings")

                # Look for parent container and find the score within it
                for heading in usability_heading[:2]:
                    try:
                        # Try to find parent div/section
                        parent = heading.find_element(By.XPATH, './ancestor::div[1]')
                        # Look for p elements in the parent's following siblings
                        following_p = parent.find_element(By.XPATH, './following-sibling::*//p')
                        if following_p:
                            text = following_p.text.strip()
                            if text:
                                usability = text
                                logger.info(f"Found usability near heading: {usability}")
                                break
                    except Exception:
                        continue

        except Exception as e:
            logger.error(f"Fallback usability search failed: {e}")

    if not usability:
        logger.warning(f"Could not find usability for {name}")

    return usability
