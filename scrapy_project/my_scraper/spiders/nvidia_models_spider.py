"""
NVIDIA Models Spider
Scrapes model metadata from NVIDIA Build (https://build.nvidia.com/models)
"""

import scrapy
import time
from datetime import datetime
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html as lxml_html

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
        'CONCURRENT_REQUESTS': 8,  # Moderate concurrency for external site
        'DOWNLOAD_DELAY': 0.5,  # Be respectful to external site
    }

    def __init__(self, *args, **kwargs):
        """Initialize spider"""
        super().__init__(*args, **kwargs)
        self.selectors = get_selectors_for_site('nvidia')
        self.model_counter = 0
        self.processed_urls = set()  # Track processed URLs to avoid duplicates
        self.processed_names = set()  # Track processed names to avoid duplicates

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

            self.logger.info(f'Found {len(model_cards)} model cards on page')

            # Process each model card
            for idx, card in enumerate(model_cards):
                try:
                    # Extract model name from title attribute
                    model_name_attr = self.selectors.get('model_name_attr', 'title')
                    model_name = card.get_attribute(model_name_attr)

                    if not model_name:
                        self.logger.warning(f'Model card {idx + 1} has no name attribute')
                        continue

                    # Extract model URL from href attribute
                    model_url_attr = self.selectors.get('model_url_attr', 'href')
                    model_url = card.get_attribute(model_url_attr)

                    if not model_url:
                        self.logger.warning(f'Model {model_name} has no URL attribute')
                        continue

                    # Extract base URL if full URL is provided
                    if model_url.startswith('http'):
                        from urllib.parse import urlparse
                        parsed = urlparse(model_url)
                        model_url = parsed.path

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

                    self.logger.info(f'Processing {self.model_counter}: {model_name}')

                    # Create item
                    item = NvidiaModelItem()
                    item['name'] = model_name
                    item['nvidia_url'] = model_url

                    # Add timestamp
                    item['scraped_on'] = datetime.now().isoformat()

                    # Extract tags for this model
                    # Note: We need to find the parent container of the card to locate tags
                    try:
                        # Navigate to parent container that includes both the link and tags
                        # The structure is typically: a[data-linkbox-overlay] is nested within several divs
                        # that also contain the tags. We need to find the right ancestor.
                        parent_container = card.find_element(By.XPATH, './ancestor::div[3]')

                        # Scroll the container into view to ensure tags are visible
                        driver.execute_script("arguments[0].scrollIntoView(true);", parent_container)
                        time.sleep(0.3)  # Brief pause for any animations

                        # Extract tags for this specific model, passing the scoped container
                        item['tags'] = extract_nvidia_tags(parent_container, driver, self.selectors, model_name)

                    except Exception as e:
                        self.logger.warning(f'Error extracting tags for {model_name}: {e}')
                        import traceback
                        traceback.print_exc()
                        item['tags'] = []

                    # Log summary from main page
                    tags_count = len(item['tags']) if item['tags'] else 0
                    self.logger.info(f"Extracted {tags_count} tags for {model_name}")

                    # Make request to modelcard page to extract model card content
                    modelcard_url = f"https://build.nvidia.com{model_url}/modelcard"
                    self.logger.info(f"Requesting modelcard: {modelcard_url}")

                    yield scrapy.Request(
                        url=modelcard_url,
                        callback=self.parse_modelcard,
                        meta={
                            'selenium': True,
                            'selenium_wait': 3,
                            'selenium_wait_selector': 'div.prose',
                            'item': item,  # Pass the partially filled item
                        },
                        dont_filter=True
                    )

                except Exception as e:
                    self.logger.error(f'Error processing model card {idx + 1}: {e}')
                    import traceback
                    traceback.print_exc()
                    continue

            self.logger.info(f'Successfully processed {self.model_counter} models')

        except Exception as e:
            self.logger.error(f'Error parsing NVIDIA models page: {e}')
            import traceback
            traceback.print_exc()

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
            # Get model card content selector
            model_card_selector = self.selectors.get('model_card_content', 'div.prose.prose-markdown-compat')

            # Try to find the model card content div
            try:
                model_card_element = driver.find_element(By.CSS_SELECTOR, model_card_selector)

                # Extract the HTML content or text content
                # Using innerHTML to preserve formatting
                model_card_html = model_card_element.get_attribute('innerHTML')

                if model_card_html and model_card_html.strip():
                    item['model_card'] = model_card_html.strip()
                    self.logger.info(f"✓ Extracted model card for {model_name} ({len(model_card_html)} chars)")
                else:
                    # Fallback to text content if innerHTML is empty
                    model_card_text = model_card_element.text.strip()
                    if model_card_text:
                        item['model_card'] = model_card_text
                        self.logger.info(f"✓ Extracted model card text for {model_name} ({len(model_card_text)} chars)")
                    else:
                        item['model_card'] = ''
                        self.logger.warning(f"Model card element found but empty for {model_name}")

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
