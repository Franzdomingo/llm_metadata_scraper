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


def extract_variations_for_tab(
    driver: webdriver.Chrome,
    selectors: Dict,
    name: str,
    tab_prefix: str,
    variation_counter_start: int = 1
) -> List[Dict]:
    """
    Extract variations for a single tab

    Args:
        driver: Selenium driver instance
        selectors: Selectors configuration dictionary
        name: Model name for logging
        tab_prefix: Tab name to use as prefix (e.g., "Transformers", "GGUF")
        variation_counter_start: Starting number for variation counter

    Returns:
        List of variation dictionaries with detailed information
    """
    variations = []

    try:
        logger.info(f"Extracting variations for tab '{tab_prefix}' - {name}")

        # Get selectors from configuration
        action_selector = selectors.get('variation_action')
        list_items_selector = selectors.get('variation_list_items')
        name_selector = selectors.get('variation_name')
        version_selector = selectors.get('variation_version')
        downloads_selector = selectors.get('variation_downloads')
        license_selector = selectors.get('variation_license')
        model_card_selector = selectors.get('variation_model_card')
        is_finetunable_selector = selectors.get('is_finetunable')
        example_usage_selector = selectors.get('example_usage')

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
            list_container_selector = selectors.get('variation_list_container', 'ul[role="listbox"]')

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
        variation_counter = variation_counter_start

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
                    list_container_selector = selectors.get('variation_list_container', 'ul[role="listbox"]')
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
                variation_example_usage = ''

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
                        # Find all matching elements to ensure we get the right one
                        downloads_elems = driver.find_elements(By.CSS_SELECTOR, downloads_selector)
                        logger.info(f"Variation {variation_counter}: Found {len(downloads_elems)} elements matching downloads selector")

                        # Look for the element with numeric content only (no text)
                        for idx, elem in enumerate(downloads_elems):
                            text = elem.text.strip()
                            # Check if text is numeric (digits only, possibly with K/M suffix)
                            if text and (text.isdigit() or (text[:-1].isdigit() and text[-1] in ['K', 'M', 'k', 'm'])):
                                variation_downloads = text
                                logger.info(f"Variation {variation_counter}: Found downloads '{variation_downloads}' from element {idx + 1}/{len(downloads_elems)}")
                                break

                        # If no numeric-only element found, use the first one as fallback
                        if not variation_downloads and len(downloads_elems) > 0:
                            variation_downloads = downloads_elems[0].text.strip()
                            logger.info(f"Variation {variation_counter}: Using first element for downloads: '{variation_downloads}'")

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
                # Model card should be within the variation-specific content area
                # If selector doesn't exist or doesn't find any elements, leave empty
                model_card_selectors = model_card_selector if isinstance(model_card_selector, list) else [model_card_selector] if model_card_selector else []

                for idx, mc_selector in enumerate(model_card_selectors):
                    try:
                        # Try to find all matching elements (there might be multiple)
                        model_card_elems = driver.find_elements(By.CSS_SELECTOR, mc_selector)

                        # If selector doesn't exist (0 elements found), skip and leave field empty
                        if len(model_card_elems) == 0:
                            logger.info(f"Variation {variation_counter}: Selector '{mc_selector}' found 0 elements - skipping")
                            continue

                        logger.info(f"Variation {variation_counter}: Found {len(model_card_elems)} elements matching model card selector: '{mc_selector}'")

                        # Try each element until we find one with content
                        for elem_idx, model_card_elem in enumerate(model_card_elems):
                            try:
                                # Get text content
                                text_content = model_card_elem.text.strip()

                                # Only accept if it has meaningful content (> 5 chars)
                                if text_content and len(text_content) > 5:
                                    variation_model_card = text_content
                                    # Log truncated version (first 100 chars) to avoid log spam
                                    preview = variation_model_card[:100] + '...' if len(variation_model_card) > 100 else variation_model_card
                                    logger.info(f"Variation {variation_counter}: Found model card - Preview: {preview}")
                                    break
                                else:
                                    logger.info(f"Variation {variation_counter}: Element {elem_idx + 1} has content too short ({len(text_content)} chars)")
                            except Exception as elem_error:
                                logger.info(f"Variation {variation_counter}: Error extracting text from element {elem_idx + 1}: {elem_error}")
                                continue

                        # If we found content, break out of selector loop
                        if variation_model_card:
                            break

                    except Exception as e:
                        logger.info(f"Variation {variation_counter}: Model card selector failed: {e}")
                        continue

                # Log if field remains empty (this is expected and OK if selector doesn't exist)
                if not variation_model_card:
                    logger.info(f"Variation {variation_counter}: Model card field will be empty (selector not found or no content)")

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

                # Extract example usage (try multiple selectors)
                example_usage_selectors = example_usage_selector if isinstance(example_usage_selector, list) else [example_usage_selector] if example_usage_selector else []

                for idx, eu_selector in enumerate(example_usage_selectors):
                    try:
                        example_usage_elem = driver.find_element(By.CSS_SELECTOR, eu_selector)

                        # First check if it contains the "no usage guide" message
                        # Look for the specific paragraph element
                        try:
                            no_guide_elem = example_usage_elem.find_element(By.CSS_SELECTOR, 'p.sc-hwddKA.dIsQKt')
                            if no_guide_elem and 'This variation does not have a usage guide yet.' in no_guide_elem.text:
                                variation_example_usage = ''
                                logger.info(f"Variation {variation_counter}: No usage guide available")
                                break
                        except:
                            pass  # No "no guide" message found, continue with extraction

                        # Try to find the content div (sibling to the header)
                        try:
                            content_elem = example_usage_elem.find_element(By.CSS_SELECTOR, 'div.sc-lkCrJH.ghmUBs')
                            variation_example_usage = content_elem.text.strip()
                        except:
                            # Fallback: get all text from parent (includes header)
                            variation_example_usage = example_usage_elem.text.strip()
                            # Remove the "Example Use" header if present at the start
                            if variation_example_usage.startswith('Example Use\n'):
                                variation_example_usage = variation_example_usage[12:].strip()
                            elif variation_example_usage.startswith('Example Use'):
                                variation_example_usage = variation_example_usage[11:].strip()

                        if variation_example_usage:
                            # Log truncated version (first 100 chars) to avoid log spam
                            preview = variation_example_usage[:100] + '...' if len(variation_example_usage) > 100 else variation_example_usage
                            logger.info(f"Variation {variation_counter}: Found example usage using selector {idx + 1}/{len(example_usage_selectors)} - Preview: {preview}")
                            break
                    except Exception as e:
                        logger.info(f"Variation {variation_counter}: Example usage selector {idx + 1}/{len(example_usage_selectors)} failed: {e}")
                        continue

                if not variation_example_usage and example_usage_selectors:
                    logger.info(f"Variation {variation_counter}: Could not find example usage with any selector")

                # Create variation dictionary with prefix
                # Format: "Transformers/variation_01" using tab_prefix
                variation_id = f'{tab_prefix}/variation_{variation_counter:02d}'

                variation = {
                    'variation': variation_id,
                    'variation_name': variation_name,
                    'variation_version': variation_version,
                    'variation_license': variation_license,
                    'variation_downloads': variation_downloads,
                    'model_card': variation_model_card,
                    'is_finetunable': variation_is_finetunable,
                    'example_usage': variation_example_usage
                }
                variations.append(variation)
                logger.info(f"Extracted {variation_id}: {variation_name} (Version: {variation_version}, Downloads: {variation_downloads}, License: {variation_license})")
                variation_counter += 1

            except Exception as e:
                logger.warning(f"Error processing variation {variation_counter} ({queued_name}): {e}")
                continue

        if variations:
            logger.info(f"Successfully extracted {len(variations)} variations for tab '{tab_prefix}' - {name}")
        else:
            logger.warning(f"No variations extracted for tab '{tab_prefix}' - {name}")

    except Exception as e:
        logger.error(f"Error extracting variations for tab '{tab_prefix}' - {name}: {e}")

    return variations


def extract_variations(driver: webdriver.Chrome, selectors: Dict, name: str, model_id: int) -> List[Dict]:
    """
    Extract ALL variations across ALL tabs by detecting and clicking each tab

    Args:
        driver: Selenium driver instance
        selectors: Selectors configuration dictionary
        name: Model name for logging
        model_id: Model ID

    Returns:
        List of variation dictionaries with detailed information from all tabs
    """
    all_variations = []

    if not driver:
        logger.info(f"No driver provided, skipping variations extraction for {name}")
        return all_variations

    try:
        logger.info(f"Starting multi-tab variations extraction for {name}")

        # Get tab selectors from configuration
        tabs_all_selector = selectors.get('variation_tabs_all')
        tab_text_selector = selectors.get('variation_tab_text')

        if not tabs_all_selector or not tab_text_selector:
            logger.warning(f"Tab selectors not configured, falling back to single-tab extraction")
            # Fallback: extract without tab information
            return extract_variations_for_tab(driver, selectors, name, "variation", 1)

        # Step 1: Find all tab buttons and build a tab queue
        tab_queue = []

        try:
            tab_buttons = driver.find_elements(By.CSS_SELECTOR, tabs_all_selector)
            logger.info(f"Found {len(tab_buttons)} tab buttons with selector '{tabs_all_selector}'")

            if len(tab_buttons) == 0:
                logger.warning(f"No tabs found for {name}, skipping variations")
                return all_variations

            # Build queue: store tab text and indices
            for idx, tab_button in enumerate(tab_buttons):
                try:
                    # Extract tab text
                    tab_text_elem = tab_button.find_element(By.CSS_SELECTOR, tab_text_selector)
                    tab_text = tab_text_elem.text.strip()

                    if tab_text:
                        tab_queue.append({
                            'index': idx,
                            'text': tab_text,
                            'button': tab_button
                        })
                        logger.info(f"Added tab to queue - Index {idx}: {tab_text}")

                except Exception as e:
                    logger.warning(f"Error extracting text from tab button {idx}: {e}")
                    continue

            logger.info(f"Built tab queue with {len(tab_queue)} tabs for {name}")

        except Exception as e:
            logger.error(f"Error building tab queue for {name}: {e}")
            return all_variations

        # Step 2: Process each tab
        variation_counter = 1  # Global counter across all tabs

        for tab_item in tab_queue:
            tab_idx = tab_item['index']
            tab_text = tab_item['text']

            try:
                logger.info(f"Processing tab {tab_idx + 1}/{len(tab_queue)}: {tab_text}")

                # Click the tab button
                try:
                    # Re-find the tab button (it may be stale)
                    tab_buttons = driver.find_elements(By.CSS_SELECTOR, tabs_all_selector)
                    if tab_idx < len(tab_buttons):
                        tab_button = tab_buttons[tab_idx]

                        # Scroll into view and click
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", tab_button)
                        time.sleep(0.3)
                        tab_button.click()
                        logger.info(f"Clicked tab: {tab_text}")
                        time.sleep(1)  # Wait for tab content to load
                    else:
                        logger.warning(f"Tab index {tab_idx} out of range")
                        continue

                except Exception as e:
                    logger.error(f"Error clicking tab '{tab_text}': {e}")
                    continue

                # Extract variations for this tab
                tab_variations = extract_variations_for_tab(
                    driver, selectors, name, tab_text, variation_counter
                )

                # Add to all_variations and update counter
                all_variations.extend(tab_variations)
                variation_counter += len(tab_variations)

                logger.info(f"Extracted {len(tab_variations)} variations from tab '{tab_text}'")

            except Exception as e:
                logger.warning(f"Error processing tab '{tab_text}': {e}")
                continue

        logger.info(f"Completed multi-tab extraction: {len(all_variations)} total variations from {len(tab_queue)} tabs for {name}")

    except Exception as e:
        logger.error(f"Error in multi-tab extract_variations for {name}: {e}")

    return all_variations
