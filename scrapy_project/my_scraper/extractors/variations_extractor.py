"""
Transformers variations extraction functions
"""

import logging
import time
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from .selenium_utils import click_element

logger = logging.getLogger(__name__)


def click_dropdown_to_open(driver: webdriver.Chrome, selector: str, timeout: int = 3) -> bool:
    """
    Aggressively try to open a dropdown by clicking it multiple ways

    Args:
        driver: Selenium driver instance
        selector: CSS selector for dropdown element
        timeout: Max seconds to wait for aria-expanded=true

    Returns:
        True if dropdown opened (aria-expanded=true), False otherwise
    """
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)

        # First, scroll the element into view
        logger.info("Scrolling dropdown element into view")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
        time.sleep(0.5)

        # Try to hide any overlaying elements (common issue)
        try:
            logger.info("Attempting to hide overlay elements")
            # Hide common overlay classes
            driver.execute_script("""
                let overlays = document.querySelectorAll('.sc-ABqPz.hkFQpn');
                overlays.forEach(el => el.style.display = 'none');
            """)
            time.sleep(0.3)
        except Exception as e:
            logger.info(f"Could not hide overlays: {e}")

        # Method 1: JavaScript click with force
        try:
            logger.info("Method 1: Trying JavaScript click")
            driver.execute_script("arguments[0].click();", element)
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 1 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 1 failed: {e}")

        # Method 2: JavaScript MouseEvent dispatch (most powerful)
        try:
            logger.info("Method 2: Trying JavaScript MouseEvent dispatch")
            driver.execute_script("""
                var element = arguments[0];
                var event = new MouseEvent('mousedown', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                element.dispatchEvent(event);

                var clickEvent = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                element.dispatchEvent(clickEvent);
            """, element)
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 2 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 2 failed: {e}")

        # Method 3: Focus and press SPACE key (accessibility method)
        try:
            logger.info("Method 3: Trying focus via JavaScript and SPACE key")
            driver.execute_script("arguments[0].focus();", element)
            time.sleep(0.2)
            element.send_keys(Keys.SPACE)
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 3 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 3 failed: {e}")

        # Method 4: Focus and press ENTER key
        try:
            logger.info("Method 4: Trying focus via JavaScript and ENTER key")
            driver.execute_script("arguments[0].focus();", element)
            time.sleep(0.2)
            element.send_keys(Keys.ENTER)
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 4 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 4 failed: {e}")

        # Method 5: Regular Selenium click (after overlay removal)
        try:
            logger.info("Method 5: Trying regular Selenium click after overlay removal")
            element.click()
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 5 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 5 failed: {e}")

        # Method 6: ActionChains with offset
        try:
            logger.info("Method 6: Trying ActionChains with offset")
            actions = ActionChains(driver)
            actions.move_to_element(element).move_by_offset(0, 0).click().perform()
            time.sleep(0.5)
            if element.get_attribute('aria-expanded') == 'true':
                logger.info("Method 6 succeeded - dropdown opened")
                return True
        except Exception as e:
            logger.info(f"Method 6 failed: {e}")

        logger.warning("All click methods failed - dropdown did not open")
        return False

    except Exception as e:
        logger.error(f"Error in click_dropdown_to_open: {e}")
        return False


def extract_variations(driver: webdriver.Chrome, selectors: Dict, name: str, model_id: int) -> List[Dict]:
    """
    Extract transformers variation entries by clicking each variation and extracting details

    Args:
        driver: Selenium driver instance
        selectors: Selectors configuration dictionary
        name: Model name for logging
        model_id: Model ID

    Returns:
        List of variation dictionaries with detailed information
    """
    variations = []

    if not driver:
        logger.info(f"No driver provided, skipping variations extraction for {name}")
        return variations

    try:
        logger.info(f"Starting variations extraction for {name}")

        # Get selectors from configuration
        action_selector = selectors.get('transformers_variation_action')
        list_items_selector = selectors.get('transformers_variation_list_items')
        name_selector = selectors.get('transformers_variation_name')
        version_selector = selectors.get('transformers_variation_version')
        downloads_selector = selectors.get('transformers_variation_downloads')
        license_selector = selectors.get('transformers_variation_license')
        model_card_selector = selectors.get('transformers_variation_model_card')
        is_finetunable_selector = selectors.get('transformers_is_finetunable')

        logger.info(f"Using selectors - action: {action_selector}, list_items: {list_items_selector}")

        # Step 1: Click the dropdown button to open the variation list
        if not action_selector:
            logger.warning(f"No action_selector configured for variations")
            return variations

        try:
            dropdown_buttons = driver.find_elements(By.CSS_SELECTOR, action_selector)
            logger.info(f"Found {len(dropdown_buttons)} dropdown buttons with selector '{action_selector}'")

            if len(dropdown_buttons) == 0:
                logger.warning(f"No variation dropdown found for {name} - this model may not have variations")
                return variations

            # Click the first dropdown button to open the variation list
            logger.info(f"Attempting to click dropdown button for {name}")
            if not click_dropdown_to_open(driver, action_selector):
                logger.warning(f"Could not open variation dropdown for {name} - all click methods failed")
                return variations

            logger.info(f"Successfully opened variation dropdown for {name}")
            time.sleep(0.5)  # Additional wait for list to render

        except Exception as e:
            logger.error(f"Error finding/clicking variation dropdown for {name}: {e}")
            return variations

        # Step 2: Build a queue of variation buttons to click
        variation_queue = []

        if not list_items_selector:
            logger.warning(f"No list_items_selector configured for variations")
            return variations

        try:
            # Wait for the list container to appear first
            list_container_selector = selectors.get('transformers_variation_list_container', 'ul[role="listbox"]')

            logger.info(f"Waiting for list container with selector '{list_container_selector}'")

            # Try multiple selectors with fallback
            list_container_found = False
            container_selectors = [
                list_container_selector,  # ul[role="listbox"]
                'ul.MuiMenu-list[role="listbox"]',  # More specific MUI selector
                'ul.MuiList-root[role="listbox"]',  # Alternative MUI selector
                'ul[role="listbox"][aria-labelledby]',  # With aria-labelledby attribute
            ]

            for selector in container_selectors:
                try:
                    logger.info(f"Trying container selector: {selector}")
                    # Use shorter timeout for each attempt (2 seconds)
                    wait = WebDriverWait(driver, 2)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"List container appeared with selector: {selector}")
                    list_container_selector = selector  # Update to working selector
                    list_container_found = True
                    break
                except TimeoutException:
                    logger.info(f"Selector '{selector}' timed out, trying next...")
                    continue

            if not list_container_found:
                logger.warning(f"Could not find list container with any selector")
                return variations

            # Add small delay for list items to render
            time.sleep(0.5)

            # Find all variation list items within the list container
            # Use a more specific selector that targets items within the listbox
            specific_selector = f'{list_container_selector} {list_items_selector}'
            logger.info(f"Finding list items with selector '{specific_selector}'")

            list_items = driver.find_elements(By.CSS_SELECTOR, specific_selector)
            logger.info(f"Found {len(list_items)} variation list items")

            if len(list_items) == 0:
                logger.warning(f"Dropdown opened but no variation list items found for {name}")
                return variations

            # Build queue: store variation names and their indices
            for idx, item in enumerate(list_items):
                try:
                    # Extract variation name from the list item
                    variation_name = ''
                    if name_selector:
                        try:
                            name_elem = item.find_element(By.CSS_SELECTOR, name_selector)
                            variation_name = name_elem.text.strip()
                        except:
                            variation_name = item.text.strip()
                    else:
                        variation_name = item.text.strip()

                    if variation_name:
                        variation_queue.append({
                            'index': idx,
                            'name': variation_name
                        })
                        logger.info(f"Added to queue - Index {idx}: {variation_name}")

                except Exception as e:
                    logger.warning(f"Error extracting name from list item {idx}: {e}")
                    continue

            logger.info(f"Built variation queue with {len(variation_queue)} items for {name}")

        except TimeoutException:
            logger.warning(f"Timeout waiting for variation list items to appear for {name}")
            return variations
        except Exception as e:
            logger.error(f"Error building variation queue for {name}: {e}")
            return variations

        # Step 3: Process each variation in the queue
        variation_counter = 1

        for queue_item in variation_queue:
            idx = queue_item['index']
            queued_name = queue_item['name']

            try:
                logger.info(f"Processing variation {variation_counter}/{len(variation_queue)}: {queued_name}")

                # Re-open the dropdown (it may have closed after previous selection)
                if variation_counter > 1:  # Don't re-open on first iteration
                    try:
                        if not click_dropdown_to_open(driver, action_selector):
                            logger.warning(f"Could not re-open dropdown for variation {variation_counter}")
                            continue
                        logger.info(f"Re-opened dropdown for variation {variation_counter}")
                        time.sleep(0.3)  # Wait for dropdown to open
                    except Exception as e:
                        logger.error(f"Error re-opening dropdown for variation {variation_counter}: {e}")
                        continue

                # Re-find the list items (they may be stale after re-opening dropdown)
                try:
                    # Wait for list container to appear again
                    list_container_selector = selectors.get('transformers_variation_list_container', 'ul[role="listbox"]')
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, list_container_selector)))
                    time.sleep(0.3)  # Small delay for items to render

                    # Find items within the list container
                    specific_selector = f'{list_container_selector} {list_items_selector}'
                    list_items = driver.find_elements(By.CSS_SELECTOR, specific_selector)

                    if idx >= len(list_items):
                        logger.warning(f"Index {idx} out of range, only {len(list_items)} items found")
                        continue

                    # Click the variation button at the specified index
                    variation_button = list_items[idx]
                    variation_button.click()
                    logger.info(f"Clicked variation button at index {idx}: {queued_name}")
                    time.sleep(0.8)  # Wait for variation details to load

                except (TimeoutException, StaleElementReferenceException) as e:
                    logger.warning(f"Could not find/click variation button at index {idx}: {e}")
                    continue

                # Step 4: Extract variation details after clicking
                variation_name = queued_name  # Use the name from queue
                variation_version = ''
                variation_downloads = ''
                variation_license = ''
                variation_model_card = ''
                variation_is_finetunable = ''

                # Extract version
                if version_selector:
                    try:
                        version_elem = driver.find_element(By.CSS_SELECTOR, version_selector)
                        variation_version = version_elem.text.strip()
                        logger.info(f"Variation {variation_counter}: Found version '{variation_version}'")
                    except Exception as e:
                        logger.info(f"Variation {variation_counter}: Could not find version: {e}")

                # Extract downloads
                if downloads_selector:
                    try:
                        downloads_elem = driver.find_element(By.CSS_SELECTOR, downloads_selector)
                        variation_downloads = downloads_elem.text.strip()
                        logger.info(f"Variation {variation_counter}: Found downloads '{variation_downloads}'")
                    except Exception as e:
                        logger.info(f"Variation {variation_counter}: Could not find downloads: {e}")

                # Extract license (try multiple selectors)
                license_selectors = license_selector if isinstance(license_selector, list) else [license_selector] if license_selector else []

                for idx, lic_selector in enumerate(license_selectors):
                    try:
                        license_elem = driver.find_element(By.CSS_SELECTOR, lic_selector)
                        variation_license = license_elem.text.strip()

                        # Clean license text - remove icon text and extra whitespace
                        if variation_license:
                            # Remove common icon texts
                            variation_license = variation_license.replace('open_in_new', '').strip()
                            # Remove multiple spaces
                            variation_license = ' '.join(variation_license.split())

                            logger.info(f"Variation {variation_counter}: Found license '{variation_license}' using selector {idx + 1}/{len(license_selectors)}")
                            break
                    except Exception as e:
                        logger.info(f"Variation {variation_counter}: License selector {idx + 1}/{len(license_selectors)} failed: {e}")
                        continue

                if not variation_license and license_selectors:
                    logger.info(f"Variation {variation_counter}: Could not find license with any selector")

                # Extract model card (try multiple selectors)
                model_card_selectors = model_card_selector if isinstance(model_card_selector, list) else [model_card_selector] if model_card_selector else []

                for idx, mc_selector in enumerate(model_card_selectors):
                    try:
                        model_card_elem = driver.find_element(By.CSS_SELECTOR, mc_selector)
                        # Get the text content, preserving some structure
                        variation_model_card = model_card_elem.text.strip()

                        if variation_model_card:
                            # Log truncated version (first 100 chars) to avoid log spam
                            preview = variation_model_card[:100] + '...' if len(variation_model_card) > 100 else variation_model_card
                            logger.info(f"Variation {variation_counter}: Found model card using selector {idx + 1}/{len(model_card_selectors)} - Preview: {preview}")
                            break
                    except Exception as e:
                        logger.info(f"Variation {variation_counter}: Model card selector {idx + 1}/{len(model_card_selectors)} failed: {e}")
                        continue

                if not variation_model_card and model_card_selectors:
                    logger.info(f"Variation {variation_counter}: Could not find model card with any selector")

                # Extract is_finetunable (try multiple selectors)
                # Note: We need to find all matching elements and filter for "Yes"/"No" since
                # the selector matches multiple elements (version, license, etc.)
                is_finetunable_selectors = is_finetunable_selector if isinstance(is_finetunable_selector, list) else [is_finetunable_selector] if is_finetunable_selector else []

                for idx, ft_selector in enumerate(is_finetunable_selectors):
                    try:
                        # Find ALL matching elements instead of just the first one
                        finetunable_elems = driver.find_elements(By.CSS_SELECTOR, ft_selector)
                        logger.info(f"Variation {variation_counter}: Found {len(finetunable_elems)} elements matching is_finetunable selector {idx + 1}")

                        # Look for element with "Yes" or "No" text
                        for elem in finetunable_elems:
                            text = elem.text.strip()
                            # Check if it's a Yes/No value (case-insensitive)
                            if text.lower() in ['yes', 'no']:
                                variation_is_finetunable = text
                                logger.info(f"Variation {variation_counter}: Found is_finetunable '{variation_is_finetunable}' using selector {idx + 1}/{len(is_finetunable_selectors)}")
                                break

                        if variation_is_finetunable:
                            break
                    except Exception as e:
                        logger.info(f"Variation {variation_counter}: Is_finetunable selector {idx + 1}/{len(is_finetunable_selectors)} failed: {e}")
                        continue

                if not variation_is_finetunable and is_finetunable_selectors:
                    logger.info(f"Variation {variation_counter}: Could not find is_finetunable with any selector")

                # Create variation dictionary
                variation = {
                    'transformers_variation': f'variation_{variation_counter:02d}',
                    'transformers_variation_name': variation_name,
                    'transformers_variation_version': variation_version,
                    'transformers_variation_license': variation_license,
                    'transformers_variation_downloads': variation_downloads,
                    'transformers_model_card': variation_model_card,
                    'transformers_is_finetunable': variation_is_finetunable
                }
                variations.append(variation)
                logger.info(f"Extracted variation_{variation_counter:02d}: {variation_name} (Version: {variation_version}, Downloads: {variation_downloads}, License: {variation_license})")
                variation_counter += 1

            except Exception as e:
                logger.warning(f"Error processing variation {variation_counter} ({queued_name}): {e}")
                continue

        if variations:
            logger.info(f"Successfully extracted {len(variations)} variations with details for {name}")
        else:
            logger.warning(f"No variations extracted for {name} despite finding {len(variation_queue)} items in queue")

    except Exception as e:
        logger.error(f"Error in extract_variations for {name}: {e}")

    return variations
