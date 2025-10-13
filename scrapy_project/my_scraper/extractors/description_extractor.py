"""
Description extraction functions
"""

import logging
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html
from my_scraper.utils import html_to_text

logger = logging.getLogger(__name__)


def extract_description(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                       selectors: Dict, name: str) -> str:
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
                logger.debug(f"Trying description CSS selector via Selenium: {selector}")
                desc_element = driver.find_element(By.CSS_SELECTOR, selector)
                outer = desc_element.get_attribute('outerHTML')
                if outer and outer.strip():
                    logger.info(f"Found short_description using CSS selector: {selector}")
                    return html_to_text(outer)
            except Exception as e:
                logger.debug(f"Description CSS selector {selector} not found: {e}")

    # Next try XPath selectors using lxml tree
    for selector in selectors.get('description', []):
        if selector.startswith('.') or selector.startswith('#'):
            continue
        try:
            logger.debug(f"Trying description XPath selector: {selector}")
            desc_elements = tree.xpath(selector)
            if desc_elements and desc_elements[0].text_content().strip():
                logger.info(f"Found short_description using XPath selector: {selector}")
                return desc_elements[0].text_content().strip()
        except Exception as e:
            logger.debug(f"Description XPath selector {selector} failed: {e}")

    # Final fallback: use configured CSS fallback
    if 'description_css_fallback' in selectors:
        try:
            desc_element = driver.find_element(By.CSS_SELECTOR, selectors['description_css_fallback'])
            outer = desc_element.get_attribute('outerHTML')
            if outer and outer.strip():
                logger.info(f"Found short_description using fallback CSS selector")
                return html_to_text(outer)
        except Exception:
            logger.warning(f"Could not find short_description for {name}")

    return description
