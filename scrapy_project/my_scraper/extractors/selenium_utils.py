"""
Selenium utility functions for web scraping
"""

import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html as lxml_html

logger = logging.getLogger(__name__)


def get_driver_from_response(response) -> Optional[webdriver.Chrome]:
    """
    Get Selenium driver from response meta

    Args:
        response: Scrapy response object

    Returns:
        Selenium driver instance or None
    """
    return response.meta.get('driver')


def parse_tree_from_response(response, driver: Optional[webdriver.Chrome] = None) -> lxml_html.HtmlElement:
    """
    Create lxml tree from response

    Args:
        response: Scrapy response object
        driver: Optional Selenium driver (not used, kept for backwards compatibility)

    Returns:
        lxml HtmlElement tree
    """
    # Always use response.text which contains the page source captured by middleware
    # at the correct time. DO NOT use driver.page_source as the driver may have
    # navigated to a different page by the time this method is called.
    return lxml_html.fromstring(response.text)


def wait_for_element(driver: webdriver.Chrome, selector: str,
                     by: By = By.CSS_SELECTOR, timeout: int = 10) -> Optional[any]:
    """
    Wait for element to be present

    Args:
        driver: Selenium driver instance
        selector: Element selector
        by: Selenium By type (default: CSS_SELECTOR)
        timeout: Wait timeout in seconds

    Returns:
        WebElement or None
    """
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.presence_of_element_located((by, selector)))
        return element
    except Exception as e:
        logger.debug(f"Element not found: {selector} - {e}")
        return None


def click_element(driver: webdriver.Chrome, selector: str,
                 by: By = By.CSS_SELECTOR) -> bool:
    """
    Try to click an element (with JS fallback)

    Args:
        driver: Selenium driver instance
        selector: Element selector
        by: Selenium By type (default: CSS_SELECTOR)

    Returns:
        True if clicked successfully, False otherwise
    """
    try:
        element = driver.find_element(by, selector)
        try:
            element.click()
            logger.debug(f"Clicked element: {selector}")
            return True
        except Exception:
            # Try JavaScript click as fallback
            driver.execute_script("arguments[0].click();", element)
            logger.debug(f"Clicked element via JS: {selector}")
            return True
    except Exception as e:
        logger.debug(f"Could not click element: {selector} - {e}")
        return False
