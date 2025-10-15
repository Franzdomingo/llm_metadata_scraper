"""
NVIDIA-specific tags extraction functions
"""

import logging
import time
from typing import Dict, List, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .selenium_utils import (
    scroll_element_into_view,
    click_element_with_fallback,
    get_element_text,
)

logger = logging.getLogger(__name__)


def extract_visible_tags(container_element, selectors: Dict, model_name: str) -> Set[str]:
    """
    Extract initially visible tags from NVIDIA model card container

    Args:
        container_element: Selenium WebElement representing the model card container
        selectors: Selectors configuration dictionary
        model_name: Model name for logging

    Returns:
        Set of visible tag strings
    """
    tags = set()

    try:
        visible_container_selector = selectors.get('visible_tags_container')
        tag_button_selector = selectors.get('visible_tag_buttons')
        tag_link_selector = selectors.get('tag_link')

        if not all([visible_container_selector, tag_button_selector, tag_link_selector]):
            logger.warning(f"Missing selectors for visible tags extraction for {model_name}")
            return tags

        # Find the visible tags container WITHIN this specific model card container
        try:
            containers = container_element.find_elements(By.CSS_SELECTOR, visible_container_selector)

            if not containers:
                logger.debug(f"No visible tags container found for {model_name}")
                return tags

            logger.debug(f"Found {len(containers)} visible tags containers for {model_name}")

            # Process each container (there may be multiple per model card)
            for container in containers:
                try:
                    # Find tag buttons within this container
                    tag_buttons = container.find_elements(By.CSS_SELECTOR, tag_button_selector)

                    for button in tag_buttons:
                        try:
                            # Find the link within the button
                            link = button.find_element(By.CSS_SELECTOR, tag_link_selector)
                            tag_text = get_element_text(link)

                            if tag_text and tag_text.strip():
                                tags.add(tag_text.strip())
                                logger.debug(f"Found visible tag: {tag_text.strip()}")
                        except NoSuchElementException:
                            # Try to get text from button itself if no link found
                            tag_text = get_element_text(button)
                            if tag_text and tag_text.strip() and not tag_text.startswith('+'):
                                tags.add(tag_text.strip())
                                logger.debug(f"Found visible tag (from button): {tag_text.strip()}")
                        except Exception as e:
                            logger.debug(f"Error extracting tag from button: {e}")
                            continue

                except Exception as e:
                    logger.debug(f"Error processing tags container: {e}")
                    continue

        except Exception as e:
            logger.debug(f"Error finding visible tags container: {e}")

    except Exception as e:
        logger.error(f"Error in extract_visible_tags for {model_name}: {e}")

    if tags:
        logger.info(f"Extracted {len(tags)} visible tags for {model_name}")
    else:
        logger.debug(f"No visible tags found for {model_name}")

    return tags


def extract_popover_tags(container_element, driver: webdriver.Chrome, selectors: Dict, model_name: str) -> Set[str]:
    """
    Extract tags from the "+N" popover button within a specific model card container

    Args:
        container_element: Selenium WebElement representing the model card container
        driver: Selenium driver instance (needed for waiting/clicking popovers)
        selectors: Selectors configuration dictionary
        model_name: Model name for logging

    Returns:
        Set of popover tag strings
    """
    tags = set()

    try:
        more_button_selector = selectors.get('more_tags_button')
        popover_container_selector = selectors.get('popover_tags_container')
        popover_container_alt_selector = selectors.get('popover_tags_container_alt')
        popover_tag_button_selector = selectors.get('popover_tag_buttons')
        tag_link_selector = selectors.get('tag_link')

        if not all([more_button_selector, popover_tag_button_selector, tag_link_selector]):
            logger.debug(f"Missing selectors for popover tags extraction for {model_name}")
            return tags

        # Find "+N" more button WITHIN this specific model card container
        try:
            more_buttons = container_element.find_elements(By.CSS_SELECTOR, more_button_selector)

            if not more_buttons:
                logger.debug(f"No '+N' more tags buttons found for {model_name}")
                return tags

            logger.debug(f"Found {len(more_buttons)} '+N' buttons for {model_name}")

            # Click each button and extract tags from the popover
            for idx, button in enumerate(more_buttons):
                try:
                    button_text = get_element_text(button)
                    logger.debug(f"Clicking '+N' button {idx + 1}/{len(more_buttons)}: {button_text}")

                    # Scroll button into view
                    scroll_element_into_view(driver, button)
                    time.sleep(0.3)

                    # Click the button to open popover
                    if not click_element_with_fallback(driver, button):
                        logger.debug(f"Failed to click '+N' button {idx + 1}")
                        continue

                    # Wait for popover to appear
                    time.sleep(0.5)

                    # Try to find the popover container
                    popover = None
                    try:
                        if popover_container_selector:
                            wait = WebDriverWait(driver, 2)
                            popover = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, popover_container_selector))
                            )
                    except TimeoutException:
                        # Try alternative selector
                        if popover_container_alt_selector:
                            try:
                                popover = driver.find_element(By.CSS_SELECTOR, popover_container_alt_selector)
                            except NoSuchElementException:
                                logger.debug(f"Popover not found with alternative selector")

                    if not popover:
                        logger.debug(f"Popover did not appear for button {idx + 1}")
                        # Try to close any open popover
                        try:
                            driver.find_element(By.TAG_NAME, 'body').click()
                        except:
                            pass
                        continue

                    # Extract tags from popover
                    try:
                        tag_buttons = popover.find_elements(By.CSS_SELECTOR, popover_tag_button_selector)
                        logger.debug(f"Found {len(tag_buttons)} tags in popover")

                        for tag_button in tag_buttons:
                            try:
                                # Find the link within the button
                                link = tag_button.find_element(By.CSS_SELECTOR, tag_link_selector)
                                tag_text = get_element_text(link)

                                if tag_text and tag_text.strip():
                                    tags.add(tag_text.strip())
                                    logger.debug(f"Found popover tag: {tag_text.strip()}")
                            except NoSuchElementException:
                                # Try to get text from button itself if no link found
                                tag_text = get_element_text(tag_button)
                                if tag_text and tag_text.strip():
                                    tags.add(tag_text.strip())
                                    logger.debug(f"Found popover tag (from button): {tag_text.strip()}")
                            except Exception as e:
                                logger.debug(f"Error extracting tag from popover button: {e}")
                                continue
                    except Exception as e:
                        logger.debug(f"Error extracting tags from popover: {e}")

                    # Close the popover by clicking outside or pressing Escape
                    try:
                        driver.find_element(By.TAG_NAME, 'body').click()
                        time.sleep(0.3)
                    except:
                        pass

                except Exception as e:
                    logger.debug(f"Error processing '+N' button {idx + 1}: {e}")
                    # Try to close any open popover
                    try:
                        driver.find_element(By.TAG_NAME, 'body').click()
                    except:
                        pass
                    continue

        except Exception as e:
            logger.debug(f"Error finding '+N' buttons: {e}")

    except Exception as e:
        logger.error(f"Error in extract_popover_tags for {model_name}: {e}")

    if tags:
        logger.info(f"Extracted {len(tags)} tags from popovers for {model_name}")
    else:
        logger.debug(f"No popover tags found for {model_name}")

    return tags


def extract_nvidia_tags(container_element, driver: webdriver.Chrome, selectors: Dict, model_name: str) -> List[str]:
    """
    Extract all tags (visible + popover) for an NVIDIA model from a specific container

    Args:
        container_element: Selenium WebElement representing the model card container
        driver: Selenium driver instance (needed for waiting/clicking popovers)
        selectors: Selectors configuration dictionary
        model_name: Model name for logging

    Returns:
        List of all unique tag strings
    """
    if not driver or not container_element:
        logger.warning(f"No driver or container provided for {model_name}, cannot extract tags")
        return []

    try:
        logger.debug(f"Starting NVIDIA tags extraction for {model_name}")

        # Extract visible tags from the specific container
        visible_tags = extract_visible_tags(container_element, selectors, model_name)

        # Extract popover tags from the specific container
        popover_tags = extract_popover_tags(container_element, driver, selectors, model_name)

        # Combine all tags
        all_tags = visible_tags.union(popover_tags)

        if all_tags:
            logger.info(f"Total extracted {len(all_tags)} unique tags for {model_name} "
                       f"({len(visible_tags)} visible + {len(popover_tags)} from popover)")
        else:
            logger.warning(f"No tags found for {model_name}")

        return sorted(list(all_tags))

    except Exception as e:
        logger.error(f"Error extracting NVIDIA tags for {model_name}: {e}")
        import traceback
        traceback.print_exc()
        return []
