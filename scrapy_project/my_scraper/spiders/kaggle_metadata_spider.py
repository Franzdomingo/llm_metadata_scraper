"""
Kaggle Metadata Spider
Scrapes detailed metadata from Kaggle model pages
"""

import scrapy
import time
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html as lxml_html
from my_scraper.items import KaggleMetadataItem, TransformersVariationItem
from my_scraper.utils import html_to_text
from my_scraper.selectors.site_selectors import get_selectors_for_site
from my_scraper.extractors.selenium_utils import parse_tree_from_response, click_element
from my_scraper.extractors.description_extractor import extract_description
from my_scraper.extractors.downloads_extractor import extract_downloads
from my_scraper.extractors.usability_extractor import extract_usability
from my_scraper.extractors.tags_extractor import extract_tags
from my_scraper.extractors.collaborators_extractor import extract_collaborators
from my_scraper.extractors.authors_extractor import extract_authors
from my_scraper.extractors.provenance_extractor import extract_provenance
from my_scraper.extractors.variations_extractor import extract_variations


class KaggleMetadataSpider(scrapy.Spider):
    """
    Spider to scrape Kaggle model metadata
    
    Reads model URLs from a CSV file and extracts:
    - Short description
    - Download count
    - Tags
    - Model card
    - Transformers variations
    """
    
    name = 'kaggle_metadata'
    allowed_domains = ['kaggle.com']

    custom_settings = {
        'CONCURRENT_REQUESTS': 16,  # Process multiple requests in parallel (matches driver pool)
        'DOWNLOAD_DELAY': 0.25,  # Reduced delay for maximum performance
    }

    def __init__(self, input_file=None, *args, **kwargs):
        """
        Initialize spider

        Args:
            input_file: Path to JSON or CSV file with model URLs (default: looks for recent kaggle_links output)
        """
        super().__init__(*args, **kwargs)
        self.selectors = get_selectors_for_site('kaggle')

        # Determine input file path
        if input_file:
            self.input_file = input_file
        else:
            # Look for input file in common locations
            # Prioritize JSON files from kaggle_links spider
            import glob

            self.input_file = None

            # First look for recent JSON files from kaggle_links
            json_patterns = [
                'output/kaggle_links_*.json',
                '../output/kaggle_links_*.json',
            ]

            for pattern in json_patterns:
                matching_files = glob.glob(pattern)
                if matching_files:
                    # Get the most recent file
                    self.input_file = max(matching_files, key=os.path.getctime)
                    self.logger.info(f'Found recent kaggle_links JSON output: {self.input_file}')
                    break

            # Fallback to CSV files if no JSON found
            if not self.input_file:
                csv_paths = [
                    'output/kaggle_output.csv',
                    '../output/kaggle_output.csv',
                    '../../output/kaggle_output.csv',
                ]

                for path in csv_paths:
                    if os.path.exists(path):
                        self.input_file = path
                        self.logger.info(f'Found CSV file: {self.input_file}')
                        break

        if not self.input_file:
            raise ValueError(
                'Input file not found. Please:\n'
                '1. First run: python run.py kaggle_links -a max_pages=10\n'
                '2. Then run: python run.py kaggle_metadata\n'
                'Or provide input_file parameter: -a input_file=path/to/file.json'
            )

        self.logger.info(f'Using input file: {self.input_file}')
        self.model_counter = 0
    
    def start_requests(self):
        """Generate requests from input JSON or CSV file"""
        import json

        # Determine file type by extension
        is_json = self.input_file.endswith('.json')

        if is_json:
            # Read JSON file
            with open(self.input_file, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)

                # Handle both list and dict formats
                if isinstance(data, list):
                    items = data
                else:
                    items = [data]

                for item in items:
                    self.model_counter += 1

                    name = item.get('name', '')
                    url = item.get('kaggle_url', '')

                    if not url:
                        self.logger.warning(f'No URL for model: {name}')
                        continue

                    yield scrapy.Request(
                        url=url,
                        callback=self.parse,
                        meta={
                            'selenium': True,
                            'selenium_wait': 3,
                            'selenium_wait_selector': 'h2',
                            'model_name': name,
                            'model_id': self.model_counter
                        }
                    )
        else:
            # Read CSV file
            with open(self.input_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    self.model_counter += 1

                    name = row.get('name', '')
                    url = row.get('kaggle_url', '')

                    if not url:
                        self.logger.warning(f'No URL for model: {name}')
                        continue

                    yield scrapy.Request(
                        url=url,
                        callback=self.parse,
                        meta={
                            'selenium': True,
                            'selenium_wait': 3,
                            'selenium_wait_selector': 'h2',
                            'model_name': name,
                            'model_id': self.model_counter
                        }
                    )
    
    def parse(self, response):
        """
        Parse Kaggle model page for metadata

        Args:
            response: Scrapy response object

        Yields:
            KaggleMetadataItem with extracted metadata
        """
        model_name = response.meta.get('model_name', '')
        model_id = response.meta.get('model_id', 0)

        self.logger.info(f'Processing {model_id}: {model_name}')

        # Use the driver from the middleware (already loaded with the page)
        driver = response.meta.get('driver')

        if not driver:
            self.logger.error(f'No driver available for {model_name}')
            return

        try:
            # Parse tree from the response
            tree = parse_tree_from_response(response)

            # Create item
            item = KaggleMetadataItem()
            item['model_id'] = model_id
            item['name'] = model_name
            item['kaggle_url'] = response.url

            # Add timestamp when data is scraped
            item['scraped_on'] = datetime.now().isoformat()

            # Extract using driver from middleware pool
            item['short_description'] = extract_description(driver, tree, self.selectors, model_name)
            item['downloads'] = extract_downloads(driver, tree, self.selectors, model_name)
            item['usability'] = extract_usability(driver, tree, self.selectors, model_name)
            item['model_card'] = self.extract_model_card(driver, tree, self.selectors, model_name)
            item['tags'] = extract_tags(driver, tree, self.selectors, model_name)
            item['variations'] = extract_variations(
                driver, self.selectors, model_name, model_id
            )

            # Extract collaborators, authors, and provenance, then build model_metadata
            collaborators = extract_collaborators(driver, tree, self.selectors, model_name)
            authors = extract_authors(driver, tree, self.selectors, model_name)
            provenance = extract_provenance(driver, tree, self.selectors, model_name)
            item['model_metadata'] = {
                'collaborators': collaborators,
                'authors': authors,
                'provenance': provenance
            }

            # Log concise summary
            self.logger.info(f"✓ {model_name} - Downloads: {item['downloads']}")

            yield item

        except Exception as e:
            self.logger.error(f'Error processing {model_name}: {e}')
            import traceback
            traceback.print_exc()
    
    def extract_model_card(self, driver, tree, selectors: Dict, name: str) -> str:
        """
        Extract the model card text and links
        
        Args:
            driver: Selenium driver instance
            tree: lxml tree object
            selectors: Selectors configuration dictionary
            name: Model name for logging
            
        Returns:
            Model card text with links
        """
        result = {'text': '', 'links': []}
        
        # Try to click action button if configured
        action_selector = selectors.get('model_card_action')
        if action_selector:
            try:
                if click_element(driver, action_selector):
                    time.sleep(1)
                    # Refresh tree after click (using driver's page source)
                    tree = lxml_html.fromstring(driver.page_source)
            except Exception:
                pass
        
        # Try CSS selectors via Selenium first
        for sel in selectors.get('model_card_selectors', []):
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip()
                if text:
                    result['text'] = text

                    # Extract anchor hrefs
                    try:
                        anchors = el.find_elements(By.TAG_NAME, 'a')
                        for a in anchors:
                            href = a.get_attribute('href')
                            if href:
                                result['links'].append(href)
                    except Exception:
                        pass

                    break
            except Exception:
                pass
        
        # Fallback to XPath using lxml
        if not result['text']:
            fallback_xpaths = [
                '//div[contains(@class, "sc-lkCrJH")][1]',
                '//div[contains(@class, "sc-chzmIZ")]/div[1]'
            ]
            
            for xp in fallback_xpaths:
                try:
                    elems = tree.xpath(xp)
                    if elems:
                        text = elems[0].text_content().strip()
                        if text:
                            result['text'] = text

                            # Extract links
                            try:
                                anchor_nodes = elems[0].xpath('.//a')
                                for node in anchor_nodes:
                                    href = node.get('href')
                                    if href:
                                        result['links'].append(href)
                            except Exception:
                                pass

                            break
                except Exception:
                    pass
        
        if not result['text']:
            self.logger.warning(f"Could not find model_card for {name}")
        
        # Combine text and links
        model_card_text = result['text']
        if result['links']:
            model_card_text += '\n\nLinks:\n' + '\n'.join([f"- {l}" for l in result['links']])

        return model_card_text
