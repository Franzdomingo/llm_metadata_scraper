"""
Tags extraction functions
"""

import logging
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import html as lxml_html

logger = logging.getLogger(__name__)


def extract_tags(driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                selectors: Dict, name: str) -> str:
    """
    Extract tags using configured selectors

    Args:
        driver: Selenium driver instance
        tree: lxml tree object
        selectors: Selectors configuration dictionary
        name: Model name for logging

    Returns:
        Comma-separated string of tags or empty string
    """
    tags = []

    # If no driver, can't extract tags (requires JavaScript rendering)
    if not driver:
        logger.debug(f"No driver provided, skipping tags extraction for {name}")
        return ''

    try:
        logger.debug(f"Starting tag extraction for {name}")

        # First try the specific tag link selector
        tag_link_selector = selectors.get('tag_links')
        if tag_link_selector:
            logger.debug(f"Trying specific tag link selector: {tag_link_selector}")
            try:
                tag_links = driver.find_elements(By.CSS_SELECTOR, tag_link_selector)
                logger.debug(f"Found {len(tag_links)} tag links")

                for link in tag_links:
                    try:
                        tag_text = link.text.strip()
                        if tag_text and tag_text not in tags:
                            tags.append(tag_text)
                    except Exception:
                        continue

                if tags:
                    logger.info(f"Found {len(tags)} tags using specific selector")
                    return ', '.join(tags)

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
            logger.info(f"Successfully extracted {len(tags)} tags for {name}")
        else:
            logger.warning(f"Could not find any tags for {name}")

    except Exception as e:
        logger.error(f"Error extracting tags for {name}: {e}")

    return ', '.join(tags) if tags else ''
