"""
NVIDIA Models Spider
Scrapes model metadata from NVIDIA Build (https://build.nvidia.com/models)
"""

import scrapy
import time
import random
import re
from datetime import datetime
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from lxml import html as lxml_html
from bs4 import BeautifulSoup

from my_scraper.items import NvidiaModelItem
from my_scraper.selectors.site_selectors import get_selectors_for_site
from my_scraper.extractors.selenium_utils import parse_tree_from_response
from my_scraper.extractors.nvidia_tags_extractor import extract_nvidia_tags


class NvidiaModelsSpider(scrapy.Spider):
    """
    Spider to scrape NVIDIA model metadata from build.nvidia.com

    Extracts:
    - Model name
    - NVIDIA URL (relative path)
    - Tags (both visible and from "+N" popover)
    """

    name = 'nvidia_models'
    allowed_domains = ['build.nvidia.com']
    start_urls = ['https://build.nvidia.com/models']

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,  # Increased from 4 for better throughput
        'DOWNLOAD_DELAY': 0.5,  # Reduced from 1.0 for faster scraping
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # Randomize delays
        'AUTOTHROTTLE_ENABLED': True,  # Enable auto-throttling
        'AUTOTHROTTLE_START_DELAY': 0.5,  # Reduced from 1.0
        'AUTOTHROTTLE_MAX_DELAY': 5.0,  # Reduced from 10.0
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 4.0,  # Increased from 2.0
    }

    def __init__(self, *args, skip_modelcard=False, **kwargs):
        """
        Initialize spider

        Args:
            skip_modelcard: If True, skip model card extraction for faster scraping
        """
        super().__init__(*args, **kwargs)
        self.selectors = get_selectors_for_site('nvidia')
        self.model_counter = 0
        self.processed_urls = set()  # Track processed URLs to avoid duplicates
        self.processed_names = set()  # Track processed names to avoid duplicates
        self.skip_modelcard = skip_modelcard

        if self.skip_modelcard:
            self.logger.info('Model card extraction is DISABLED - will scrape faster')

    def clean_model_card_html(self, html_content):
        """
        Clean model card HTML by removing UI elements and keeping only content

        Args:
            html_content: Raw HTML string from model card page

        Returns:
            Cleaned HTML string with only semantic content
        """
        if not html_content:
            return ''

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unwanted elements
            # 1. Remove all SVG elements (icons, graphics)
            for svg in soup.find_all('svg'):
                svg.decompose()

            # 2. Remove all button elements
            for button in soup.find_all('button'):
                button.decompose()

            # 3. Remove elements with specific classes that are UI-only
            ui_classes = [
                'btn-', 'flex', 'grid', 'rounded', 'border',
                'bg-', 'hover:', 'active:', 'aria-', 'gap-',
                'inline-flex', 'items-center', 'justify-center'
            ]

            for element in soup.find_all():
                if element.get('class'):
                    classes = ' '.join(element.get('class', []))
                    # If element has only UI classes and no semantic content, remove it
                    if any(ui_class in classes for ui_class in ui_classes):
                        # But keep if it has important semantic tags inside
                        if not element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 'a', 'code', 'pre']):
                            element.decompose()
                            continue

            # 4. Clean up attributes on remaining elements
            # Keep only semantic HTML with minimal attributes
            for tag in soup.find_all():
                # Preserve href on links, but clean the rest
                if tag.name == 'a':
                    attrs_to_keep = {}
                    if tag.get('href'):
                        attrs_to_keep['href'] = tag['href']
                    if tag.get('target'):
                        attrs_to_keep['target'] = tag['target']
                    tag.attrs = attrs_to_keep
                elif tag.name == 'code':
                    # Keep code elements clean
                    tag.attrs = {}
                elif tag.name == 'pre':
                    # Keep pre elements clean
                    tag.attrs = {}
                elif tag.name in ['div', 'span']:
                    # For div/span, keep only if they have important content
                    # Otherwise strip them but keep content
                    if not tag.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'a', 'pre']):
                        # Replace div/span with its contents
                        tag.unwrap()
                    else:
                        tag.attrs = {}
                else:
                    # For semantic tags (h1, h2, p, ul, etc.), remove all attributes
                    tag.attrs = {}

            # Get the cleaned HTML
            cleaned_html = str(soup)

            # Post-processing cleanup
            # Remove excessive whitespace
            cleaned_html = re.sub(r'\n\s*\n', '\n\n', cleaned_html)
            cleaned_html = re.sub(r'  +', ' ', cleaned_html)

            return cleaned_html.strip()

        except Exception as e:
            self.logger.warning(f'Error cleaning HTML: {e}')
            # Return original if cleaning fails
            return html_content

    def safe_get_attribute(self, driver, selector, attribute, max_retries=3):
        """
        Safely get attribute from element with retry logic for stale elements

        Args:
            driver: Selenium WebDriver instance
            selector: CSS selector to find the element
            attribute: Attribute name to extract
            max_retries: Maximum number of retries

        Returns:
            Attribute value or None if not found
        """
        for attempt in range(max_retries):
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                return element.get_attribute(attribute)
            except StaleElementReferenceException:
                if attempt < max_retries - 1:
                    self.logger.debug(f'Stale element on attempt {attempt + 1}, retrying...')
                    time.sleep(0.2)  # Brief pause before retry
                else:
                    self.logger.warning(f'Element remained stale after {max_retries} attempts')
                    raise
            except Exception as e:
                self.logger.debug(f'Error getting attribute: {e}')
                return None
        return None

    def safe_get_element_attribute(self, element, driver, card_selector, attribute, max_retries=3):
        """
        Safely get attribute from a potentially stale element with retry logic

        Args:
            element: WebElement that might be stale
            driver: Selenium WebDriver instance
            card_selector: CSS selector to re-find the element
            attribute: Attribute name to extract
            max_retries: Maximum number of retries

        Returns:
            Attribute value or None if not found
        """
        for attempt in range(max_retries):
            try:
                return element.get_attribute(attribute)
            except StaleElementReferenceException:
                if attempt < max_retries - 1:
                    self.logger.debug(f'Stale element on attempt {attempt + 1}, re-finding element...')
                    time.sleep(0.2)  # Brief pause before retry
                    try:
                        # Re-find the element using the selector
                        element = driver.find_element(By.CSS_SELECTOR, card_selector)
                    except Exception as e:
                        self.logger.warning(f'Could not re-find element: {e}')
                        return None
                else:
                    self.logger.warning(f'Element remained stale after {max_retries} attempts')
                    raise
            except Exception as e:
                self.logger.debug(f'Error getting attribute: {e}')
                return None
        return None

    def start_requests(self):
        """Generate initial request to NVIDIA models page"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'selenium': True,
                    'selenium_wait': 5,  # Wait for dynamic content to load
                    'selenium_wait_selector': 'a[data-linkbox-overlay="true"]',
                }
            )

    def parse(self, response):
        """
        Parse NVIDIA models page and extract model information

        Args:
            response: Scrapy response object

        Yields:
            NvidiaModelItem with extracted metadata
        """
        # Use the driver from the middleware (already loaded with the page)
        driver = response.meta.get('driver')

        if not driver:
            self.logger.error('No driver available for NVIDIA models page')
            return

        try:
            # Parse tree from the response
            tree = parse_tree_from_response(response)

            # Get model cards selector
            model_cards_selector = self.selectors.get('model_cards')

            if not model_cards_selector:
                self.logger.error('No model cards selector configured')
                return

            # Find all model cards on the page
            model_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)

            if not model_cards:
                self.logger.warning('No model cards found on page')
                return

            total_cards = len(model_cards)
            self.logger.info(f'Found {total_cards} model cards on page')

            # Process each model card
            processed_in_iteration = 0

            # Scroll to bottom to ensure all lazy-loaded cards are visible
            self.logger.info('Scrolling page to load all model cards...')
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 10

            while scroll_attempts < max_scroll_attempts:
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Wait for page to load

                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # No more content loaded, break
                    break

                last_height = new_height
                scroll_attempts += 1

                # Re-count cards after scrolling
                current_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)
                self.logger.info(f'Scroll attempt {scroll_attempts}: Found {len(current_cards)} cards')

            # Get final card count after scrolling
            model_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)
            final_card_count = len(model_cards)
            self.logger.info(f'After scrolling: Found {final_card_count} model cards (initially found {total_cards})')

            # STEP 1: Extract ALL model data from the main page FIRST
            # This prevents the driver from navigating away while we're still processing
            all_items = []

            self.logger.info('STEP 1: Extracting all model data from main page...')
            for idx in range(final_card_count):
                try:
                    # Re-find all cards in each iteration to avoid stale references
                    model_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)

                    # Check if current card index is still valid
                    if idx >= len(model_cards):
                        self.logger.warning(f'Card at index {idx} no longer available (have {len(model_cards)} cards)')
                        continue

                    card = model_cards[idx]

                    # Extract model name from title attribute with retry logic
                    model_name_attr = self.selectors.get('model_name_attr', 'title')
                    model_name = None

                    for attempt in range(3):
                        try:
                            model_name = card.get_attribute(model_name_attr)
                            break
                        except StaleElementReferenceException:
                            self.logger.debug(f'Stale element for card {idx + 1}, re-finding (attempt {attempt + 1})')
                            time.sleep(0.3)
                            model_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)
                            if idx < len(model_cards):
                                card = model_cards[idx]
                            else:
                                break

                    if not model_name:
                        self.logger.warning(f'Model card {idx + 1} has no name attribute')
                        continue

                    # Extract model URL from href attribute with retry logic
                    model_url_attr = self.selectors.get('model_url_attr', 'href')
                    model_url = None

                    for attempt in range(3):
                        try:
                            model_url = card.get_attribute(model_url_attr)
                            break
                        except StaleElementReferenceException:
                            self.logger.debug(f'Stale element getting URL for {model_name}, re-finding (attempt {attempt + 1})')
                            time.sleep(0.3)
                            model_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)
                            if idx < len(model_cards):
                                card = model_cards[idx]
                            else:
                                break

                    if not model_url:
                        self.logger.warning(f'Model {model_name} has no URL attribute')
                        continue

                    # Ensure we have the full URL
                    if not model_url.startswith('http'):
                        # If it's just a path, prepend the base URL
                        model_url = f'https://build.nvidia.com{model_url}'

                    # Check for duplicates - skip if already processed
                    if model_url in self.processed_urls:
                        self.logger.debug(f'Skipping duplicate URL: {model_url} ({model_name})')
                        continue

                    if model_name in self.processed_names:
                        self.logger.debug(f'Skipping duplicate name: {model_name}')
                        continue

                    # Mark as processed
                    self.processed_urls.add(model_url)
                    self.processed_names.add(model_name)
                    self.model_counter += 1
                    processed_in_iteration += 1

                    self.logger.info(f'Extracting {self.model_counter}/{final_card_count}: {model_name}')

                    # Create item
                    item = NvidiaModelItem()
                    item['name'] = model_name
                    item['nvidia_url'] = model_url

                    # Add timestamp
                    item['scraped_on'] = datetime.now().isoformat()

                    # Extract tags for this model
                    # Note: We need to find the parent container of the card to locate tags
                    try:
                        parent_container = None
                        # Navigate to parent container that includes both the link and tags
                        # The structure is typically: a[data-linkbox-overlay] is nested within several divs
                        # that also contain the tags. We need to find the right ancestor.
                        for attempt in range(3):
                            try:
                                parent_container = card.find_element(By.XPATH, './ancestor::div[3]')
                                break
                            except StaleElementReferenceException:
                                self.logger.debug(f'Stale element finding parent for {model_name}, re-finding (attempt {attempt + 1})')
                                time.sleep(0.3)
                                model_cards = driver.find_elements(By.CSS_SELECTOR, model_cards_selector)
                                if idx < len(model_cards):
                                    card = model_cards[idx]
                                else:
                                    break

                        if parent_container:
                            # Scroll the container into view to ensure tags are visible
                            driver.execute_script("arguments[0].scrollIntoView(true);", parent_container)
                            time.sleep(random.uniform(0.2, 0.4))  # Reduced delay for faster extraction

                            # Extract tags for this specific model, passing the scoped container
                            item['tags'] = extract_nvidia_tags(parent_container, driver, self.selectors, model_name)
                        else:
                            self.logger.warning(f'Could not find parent container for {model_name}')
                            item['tags'] = []

                    except Exception as e:
                        self.logger.warning(f'Error extracting tags for {model_name}: {e}')
                        item['tags'] = []

                    # Store item for later processing
                    all_items.append(item)

                except Exception as e:
                    self.logger.error(f'Error processing model card {idx + 1}: {e}')
                    import traceback
                    traceback.print_exc()
                    continue

            self.logger.info(f'STEP 1 COMPLETE: Extracted {len(all_items)} models from main page')

            # STEP 2: Now yield all items (with or without modelcard requests)
            self.logger.info('STEP 2: Yielding items and requesting modelcards...')
            for item in all_items:
                model_name = item.get('name')
                model_url = item.get('nvidia_url')
                tags_count = len(item.get('tags', [])) if item.get('tags') else 0

                # Check if we should fetch model card
                if self.skip_modelcard:
                    # Yield item immediately without model card
                    item['model_card'] = ''
                    self.logger.info(f"DONE {model_name} - URL: {model_url} - Tags: {tags_count} - ModelCard: Skipped")
                    yield item
                else:
                    # Make request to modelcard page to extract model card content
                    modelcard_url = f"{model_url}/modelcard"
                    self.logger.debug(f"Requesting modelcard: {modelcard_url}")

                    yield scrapy.Request(
                        url=modelcard_url,
                        callback=self.parse_modelcard,
                        errback=self.handle_modelcard_error,
                        meta={
                            'selenium': True,
                            'selenium_wait': 5,
                            'selenium_wait_selector': 'div.prose',
                            'item': item,  # Pass the fully filled item (except model_card)
                        },
                        dont_filter=True
                    )

            self.logger.info(f'Successfully extracted and queued {len(all_items)} models for processing')

        except Exception as e:
            self.logger.error(f'Error parsing NVIDIA models page: {e}')
            import traceback
            traceback.print_exc()

    def handle_modelcard_error(self, failure):
        """
        Handle errors when requesting model card page

        Args:
            failure: Twisted Failure object

        Yields:
            NvidiaModelItem with empty model_card field
        """
        # Get the item from the request meta
        item = failure.request.meta.get('item')

        if item:
            model_name = item.get('name', 'Unknown')
            model_url = item.get('nvidia_url', 'Unknown')

            # Log the error but continue with the item
            self.logger.warning(f'Failed to fetch modelcard for {model_name}: {failure.value}')

            # Set model card to empty string
            item['model_card'] = ''

            # Log final summary
            tags_count = len(item.get('tags', [])) if item.get('tags') else 0
            self.logger.info(f"DONE {model_name} - URL: {model_url} - Tags: {tags_count} - ModelCard: Error/Not Found")

            # Yield the item anyway so it's not lost
            yield item
        else:
            self.logger.error(f'No item found in failed request: {failure.request.url}')

    def parse_modelcard(self, response):
        """
        Parse NVIDIA model card page and extract model card content

        Args:
            response: Scrapy response object from /modelcard page

        Yields:
            Complete NvidiaModelItem with model card content
        """
        # Get the partially filled item from meta
        item = response.meta.get('item')

        if not item:
            self.logger.error('No item found in meta for modelcard page')
            return

        model_name = item.get('name', 'Unknown')
        model_url = item.get('nvidia_url', 'Unknown')

        # Use the driver from the middleware
        driver = response.meta.get('driver')

        if not driver:
            self.logger.warning(f'No driver available for modelcard page: {model_name}')
            # Yield item without model card if driver unavailable
            item['model_card'] = ''
            yield item
            return

        try:
            # Add extra wait time for content to fully load with randomization
            # Reduced wait time for better throughput
            wait_time = random.uniform(1.0, 1.5)
            self.logger.debug(f"Waiting {wait_time:.2f}s for model card to load")
            time.sleep(wait_time)  # Give more time for heavy content to load

            # Get model card content selector
            model_card_selector = self.selectors.get('model_card_content', 'div.prose.prose-markdown-compat')

            # Alternative selectors to try
            alternative_selectors = [
                'div.prose.prose-markdown-compat.max-w-[85ch]',  # Full prose format
                'div.prose',  # Generic prose
                'div.prose-markdown-compat',  # Just markdown-compat
            ]

            model_card_element = None
            used_selector = None

            # Try to find the model card content div with multiple selectors
            try:
                # First try the primary selector (reduced timeout from 10 to 5)
                try:
                    model_card_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, model_card_selector))
                    )
                    used_selector = model_card_selector
                    self.logger.debug(f"Found model card with primary selector for {model_name}")
                except:
                    # Try alternative selectors
                    for alt_selector in alternative_selectors:
                        try:
                            model_card_element = driver.find_element(By.CSS_SELECTOR, alt_selector)
                            used_selector = alt_selector
                            self.logger.debug(f"Found model card with alternative selector '{alt_selector}' for {model_name}")
                            break
                        except:
                            continue

                if model_card_element:
                    # Add a small delay to ensure content is fully rendered (reduced from 0.5)
                    time.sleep(0.2)

                    # Extract the HTML content or text content
                    # Using outerHTML to preserve the full structure including div
                    model_card_html = None

                    for attempt in range(3):
                        try:
                            model_card_html = model_card_element.get_attribute('outerHTML')
                            break
                        except StaleElementReferenceException:
                            self.logger.debug(f'Stale element getting model card HTML, retrying (attempt {attempt + 1})')
                            time.sleep(0.5)
                            # Re-find the element
                            try:
                                if used_selector:
                                    model_card_element = driver.find_element(By.CSS_SELECTOR, used_selector)
                            except:
                                break

                    if model_card_html and model_card_html.strip():
                        # Clean the HTML to remove UI elements
                        cleaned_html = self.clean_model_card_html(model_card_html)
                        item['model_card'] = cleaned_html
                        self.logger.info(f"✓ Extracted model card for {model_name} ({len(model_card_html)} chars -> {len(cleaned_html)} chars after cleaning)")
                    else:
                        # Fallback to text content if outerHTML is empty
                        model_card_text = None
                        for attempt in range(3):
                            try:
                                model_card_text = model_card_element.text.strip()
                                break
                            except StaleElementReferenceException:
                                self.logger.debug(f'Stale element getting model card text, retrying (attempt {attempt + 1})')
                                time.sleep(0.5)
                                try:
                                    if used_selector:
                                        model_card_element = driver.find_element(By.CSS_SELECTOR, used_selector)
                                except:
                                    break

                        if model_card_text:
                            item['model_card'] = model_card_text
                            self.logger.info(f"✓ Extracted model card text for {model_name} ({len(model_card_text)} chars)")
                        else:
                            item['model_card'] = ''
                            self.logger.warning(f"Model card element found but empty for {model_name}")
                else:
                    item['model_card'] = ''
                    self.logger.warning(f'Could not find model card element with any selector for {model_name}')

            except Exception as e:
                self.logger.warning(f'Could not find model card element for {model_name}: {e}')
                item['model_card'] = ''

            # Log final summary
            tags_count = len(item.get('tags', [])) if item.get('tags') else 0
            has_model_card = 'Yes' if item.get('model_card') else 'No'
            self.logger.info(f"DONE {model_name} - URL: {model_url} - Tags: {tags_count} - ModelCard: {has_model_card}")

            yield item

        except Exception as e:
            self.logger.error(f'Error parsing modelcard for {model_name}: {e}')
            import traceback
            traceback.print_exc()
            # Yield item without model card in case of error
            item['model_card'] = ''
            yield item
