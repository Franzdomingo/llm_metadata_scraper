"""
Selenium utility functions for web scraping
"""

import logging
import time
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
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
    Create lxml tree from response or driver

    Args:
        response: Scrapy response object
        driver: Optional Selenium driver. If provided, will use current page source from driver
                instead of response.text. This is useful after navigation events.

    Returns:
        lxml HtmlElement tree
    """
    # If driver is provided, use its current page source (for post-navigation parsing)
    # Otherwise, use response.text which contains the page source captured by middleware
    if driver is not None:
        page_source = driver.page_source
        return lxml_html.fromstring(page_source)
    else:
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


def click_element_with_fallback(driver: webdriver.Chrome, element: WebElement) -> bool:
    """
    Try to click a WebElement (with JS fallback)

    Args:
        driver: Selenium driver instance
        element: WebElement to click

    Returns:
        True if clicked successfully, False otherwise
    """
    try:
        try:
            element.click()
            logger.debug("Clicked element successfully")
            return True
        except Exception:
            # Try JavaScript click as fallback
            driver.execute_script("arguments[0].click();", element)
            logger.debug("Clicked element via JS fallback")
            return True
    except Exception as e:
        logger.debug(f"Could not click element: {e}")
        return False


def scroll_element_into_view(driver: webdriver.Chrome, element: WebElement,
                             block: str = 'center', delay: float = 0.3) -> None:
    """
    Scroll an element into view with optional delay

    Args:
        driver: Selenium driver instance
        element: WebElement to scroll into view
        block: Scroll alignment ('start', 'center', 'end', 'nearest')
        delay: Delay in seconds after scrolling (default: 0.3)
    """
    try:
        driver.execute_script(f"arguments[0].scrollIntoView({{block: '{block}'}});", element)
        if delay > 0:
            time.sleep(delay)
        logger.debug(f"Scrolled element into view (block={block})")
    except Exception as e:
        logger.debug(f"Could not scroll element into view: {e}")


def close_popup(driver: webdriver.Chrome, delay: float = 0.3) -> None:
    """
    Close popup by clicking on document body

    Args:
        driver: Selenium driver instance
        delay: Delay in seconds after closing (default: 0.3)
    """
    try:
        driver.execute_script("document.body.click();")
        if delay > 0:
            time.sleep(delay)
        logger.debug("Closed popup")
    except Exception as e:
        logger.debug(f"Could not close popup: {e}")


def get_element_text(element: WebElement, fallback: str = '') -> str:
    """
    Safely get text from a WebElement

    Args:
        element: WebElement to get text from
        fallback: Fallback value if text extraction fails

    Returns:
        Element text or fallback value
    """
    try:
        text = element.text.strip()
        return text if text else fallback
    except Exception as e:
        logger.debug(f"Could not get element text: {e}")
        return fallback


def get_element_attribute(element: WebElement, attribute: str, fallback: str = '') -> str:
    """
    Safely get attribute from a WebElement

    Args:
        element: WebElement to get attribute from
        attribute: Attribute name to retrieve
        fallback: Fallback value if attribute extraction fails

    Returns:
        Attribute value or fallback value
    """
    try:
        value = element.get_attribute(attribute)
        return value.strip() if value else fallback
    except Exception as e:
        logger.debug(f"Could not get element attribute '{attribute}': {e}")
        return fallback


def find_elements_by_parent(driver: webdriver.Chrome, parent_selector: str,
                            child_selector: str, by: By = By.CSS_SELECTOR) -> List[WebElement]:
    """
    Find child elements within parent elements

    Args:
        driver: Selenium driver instance
        parent_selector: Selector for parent element
        child_selector: Selector for child elements
        by: Selenium By type (default: CSS_SELECTOR)

    Returns:
        List of child WebElements
    """
    children = []
    try:
        parents = driver.find_elements(by, parent_selector)
        for parent in parents:
            try:
                children.extend(parent.find_elements(by, child_selector))
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"Could not find elements: {e}")
    return children
