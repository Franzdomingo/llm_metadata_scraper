"""
Tags extraction functions
"""

import logging
import time
from typing import Dict, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from lxml import html as lxml_html

from .selenium_utils import (
    scroll_element_into_view,
    click_element_with_fallback,
    close_popup,
    get_element_text,
    get_element_attribute
)

logger = logging.getLogger(__name__)


def clean_tag_text(tag_text: str) -> str:
    """
    Clean up tag text by removing accessibility and formatting artifacts

    Args:
        tag_text: Raw tag text to clean

    Returns:
        Cleaned tag text
    """
    if not tag_text:
        return ''

    # Remove common accessibility suffixes
    tag_text = tag_text.replace(' opens in new window', '')
    tag_text = tag_text.replace(' opens in a new window', '')
    tag_text = tag_text.replace(', opens in new window', '')
    tag_text = tag_text.replace(', opens in a new window', '')

    return tag_text.strip()


def extract_tags_from_more_buttons(driver: webdriver.Chrome, selectors: Dict) -> Set[str]:
    """
    Extract tags from hidden 'more' buttons that reveal additional tags in popups

    Args:
        driver: Selenium driver instance
        selectors: Selectors configuration dictionary

    Returns:
        Set of tag strings found in popups
    """
    all_tags = set()

    try:
        # Get selectors from configuration
        more_button_span = selectors.get('tag_more_button_span', 'span.eWEDa-d')
        popup_container = selectors.get('tag_more_popup', '.eqXpEC')
        popup_checkbox = selectors.get('tag_popup_checkbox', 'button[role="checkbox"]')
        popup_text_span = selectors.get('tag_popup_text_span', 'span.bMbEZO')

        logger.debug("Looking for 'more' buttons to expand tags")

        # Find all buttons that contain the "more" text span
        more_text_spans = driver.find_elements(By.CSS_SELECTOR, more_button_span)

        # Get the parent buttons
        more_buttons = []
        for span in more_text_spans:
            try:
                # Check if the span text contains "more"
                if 'more' in span.text.lower():
                    button = span.find_element(By.XPATH, './ancestor::button[@role="button"]')
                    if button and button not in more_buttons:
                        more_buttons.append(button)
            except Exception:
                continue

        if not more_buttons:
            logger.debug("No 'more' buttons found")
            return all_tags

        logger.info(f"Found {len(more_buttons)} 'more' buttons to click")

        # Click each more button and extract tags from the popup
        buttons_clicked = 0
        for i, button in enumerate(more_buttons):
            try:
                # Get button text for logging
                button_text = get_element_text(button, f'button {i+1}')
                logger.debug(f"Clicking button {i+1}/{len(more_buttons)}: '{button_text}'")

                # Scroll button into view and click
                scroll_element_into_view(driver, button)

                # Click the button
                if not click_element_with_fallback(driver, button):
                    logger.debug(f"Failed to click button {i+1}, skipping")
                    continue

                buttons_clicked += 1
                time.sleep(0.5)  # Wait for popup to appear

                # Find the popup div
                try:
                    wait = WebDriverWait(driver, 3)
                    popup = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, popup_container)))

                    # Extract all tags from the popup
                    tag_buttons = popup.find_elements(By.CSS_SELECTOR, popup_checkbox)

                    for tag_button in tag_buttons:
                        # Get the aria-label which contains the tag name
                        tag_name = get_element_attribute(tag_button, 'aria-label')
                        if tag_name:
                            tag_name = clean_tag_text(tag_name)
                            if tag_name:
                                all_tags.add(tag_name)
                        else:
                            # Fallback: get text from span
                            tag_spans = tag_button.find_elements(By.CSS_SELECTOR, popup_text_span)
                            for span in tag_spans:
                                tag_text = get_element_text(span)
                                if tag_text:
                                    tag_text = clean_tag_text(tag_text)
                                    if tag_text:
                                        all_tags.add(tag_text)

                    logger.debug(f"Extracted {len(tag_buttons)} tags from popup")

                    # Close the popup
                    close_popup(driver)

                except TimeoutException:
                    logger.debug(f"Popup did not appear for button {i+1}")
                except Exception as e:
                    logger.debug(f"Error extracting tags from popup: {e}")

            except StaleElementReferenceException:
                logger.debug(f"Button {i+1} became stale, skipping")
                continue
            except Exception as e:
                logger.debug(f"Error clicking button {i+1}: {e}")
                continue

        logger.info(f"Clicked {buttons_clicked} 'more' buttons and found {len(all_tags)} additional tags")

    except Exception as e:
        logger.error(f"Error in extract_tags_from_more_buttons: {e}")

    return all_tags


def extract_tags(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                selectors: Dict, name: str) -> list:
    """
    Extract tags using configured selectors

    Args:
        driver: Selenium driver instance
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        List of tag strings
    """
    tags = []

    # If no driver, can't extract tags (requires JavaScript rendering)
    if not driver:
        logger.debug(f"No driver provided, skipping tags extraction for {name}")
        return []

    try:
        logger.debug(f"Starting tag extraction for {name}")

        # First, try to extract tags from hidden "more" buttons
        logger.debug("Checking for hidden tags in 'more' buttons")
        hidden_tags = extract_tags_from_more_buttons(driver, selectors)
        if hidden_tags:
            logger.info(f"Found {len(hidden_tags)} tags from 'more' buttons")
            tags.extend(list(hidden_tags))

        # Then try the specific tag link selector
        tag_link_selector = selectors.get('tag_links')
        if tag_link_selector:
            logger.debug(f"Trying specific tag link selector: {tag_link_selector}")
            try:
                tag_links = driver.find_elements(By.CSS_SELECTOR, tag_link_selector)
                logger.debug(f"Found {len(tag_links)} tag links")

                tags_before = len(tags)
                skipped_empty = 0
                skipped_duplicates = 0

                for link in tag_links:
                    try:
                        # Try to get text from element
                        tag_text = link.text.strip()

                        # If no visible text, try aria-label or title attributes
                        if not tag_text:
                            tag_text = link.get_attribute('aria-label')
                            if tag_text:
                                tag_text = tag_text.strip()

                        if not tag_text:
                            tag_text = link.get_attribute('title')
                            if tag_text:
                                tag_text = tag_text.strip()

                        # If still no text, try to get from href (last part after /)
                        if not tag_text:
                            href = link.get_attribute('href')
                            if href and '/tag/' in href:
                                tag_text = href.split('/tag/')[-1].strip('/')
                                tag_text = tag_text.replace('-', ' ').replace('_', ' ').title()

                        # Clean up accessibility text from tags
                        tag_text = clean_tag_text(tag_text)

                        if tag_text:
                            if tag_text not in tags:
                                tags.append(tag_text)
                            else:
                                skipped_duplicates += 1
                        else:
                            skipped_empty += 1
                            logger.debug(f"Tag link has no text, aria-label, title, or href info")
                    except Exception as e:
                        logger.debug(f"Error extracting tag from link: {e}")
                        continue

                tags_added = len(tags) - tags_before
                if tags_added > 0:
                    log_msg = f"Found {tags_added} new tags using specific selector"
                    if skipped_duplicates > 0:
                        log_msg += f" ({skipped_duplicates} duplicates skipped"
                        if skipped_empty > 0:
                            log_msg += f", {skipped_empty} empty tags skipped)"
                        else:
                            log_msg += ")"
                    elif skipped_empty > 0:
                        log_msg += f" ({skipped_empty} empty tags skipped)"
                    logger.info(log_msg)
                elif skipped_empty > 0 or skipped_duplicates > 0:
                    logger.debug(f"No new tags added: {skipped_duplicates} duplicates, {skipped_empty} empty")

            except Exception as e:
                logger.debug(f"Specific tag link selector failed: {e}")

        # If specific selector failed, try container selectors
        for selector in selectors.get('tags', []):
            try:
                if selector.startswith('.') or selector.startswith('#'):
                    # CSS selector - use Selenium
                    tag_containers = driver.find_elements(By.CSS_SELECTOR, selector)

                    for container in tag_containers:
                        anchor_tags = container.find_elements(By.TAG_NAME, 'a')

                        for anchor in anchor_tags:
                            try:
                                tag_text = anchor.text.strip()
                                if tag_text and tag_text not in tags:
                                    tags.append(tag_text)
                            except Exception:
                                continue
                else:
                    # XPath selector - use lxml
                    tag_elements = tree.xpath(selector)

                    for elem in tag_elements:
                        anchor_elements = elem.xpath('.//a')

                        for anchor in anchor_elements:
                            try:
                                tag_text = anchor.text_content().strip()
                                if tag_text and tag_text not in tags:
                                    tags.append(tag_text)
                            except Exception:
                                continue

                if tags:
                    break

            except Exception as e:
                logger.debug(f"Container selector {selector} failed: {e}")
                continue

        # Fallback: Look for links near "TAGS" or "Tags" heading
        if not tags:
            logger.debug(f"Trying fallback: searching for links near 'TAGS' heading")
            try:
                # Find TAGS heading
                tags_heading = driver.find_elements(By.XPATH, "//*[contains(text(), 'TAGS') or contains(text(), 'Tags')]")

                if tags_heading:
                    logger.debug(f"Found {len(tags_heading)} 'TAGS' headings")

                    # Look for nearby links
                    for heading in tags_heading[:2]:
                        try:
                            # Try to find parent container
                            parent = heading.find_element(By.XPATH, './ancestor::div[2]')
                            # Find all links in the container
                            links = parent.find_elements(By.TAG_NAME, 'a')

                            for link in links:
                                tag_text = link.text.strip()
                                if tag_text and tag_text not in tags:
                                    # Filter out common non-tag link text
                                    if tag_text.lower() not in ['home', 'models', 'datasets', 'code', 'competitions', 'learn']:
                                        tags.append(tag_text)
                                        logger.debug(f"Found tag via fallback: {tag_text}")
                        except Exception:
                            continue

                    if tags:
                        logger.info(f"Found {len(tags)} tags using fallback method")
                else:
                    logger.debug("No TAGS heading found")

            except Exception as e:
                logger.debug(f"Fallback tags search failed: {e}")

        if tags:
            logger.info(f"Successfully extracted {len(tags)} total unique tags for {name}")
        else:
            logger.warning(f"Could not find any tags for {name}")

    except Exception as e:
        logger.error(f"Error extracting tags for {name}: {e}")

    return tags
