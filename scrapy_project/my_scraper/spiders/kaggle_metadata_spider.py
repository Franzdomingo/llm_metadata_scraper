"""
Kaggle Metadata Spider
Scrapes detailed metadata from Kaggle model pages
"""

import scrapy
import time
import csv
import os
from typing import Dict, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html as lxml_html
from my_scraper.spiders.base_spider import BaseSpider
from my_scraper.items import KaggleMetadataItem, TransformersVariationItem
from my_scraper.utils import html_to_text


class KaggleMetadataSpider(BaseSpider):
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
    
    # Use Kaggle selectors
    site_key = 'kaggle'
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,  # Process one at a time to avoid rate limiting
        'DOWNLOAD_DELAY': 1.5,
    }
    
    def __init__(self, input_file=None, *args, **kwargs):
        """
        Initialize spider
        
        Args:
            input_file: Path to CSV file with model URLs (default: output/kaggle_output.csv)
        """
        super().__init__(*args, **kwargs)
        
        # Determine input file path
        if input_file:
            self.input_file = input_file
        else:
            # Look for input file in common locations
            possible_paths = [
                'output/kaggle_output.csv',
                '../output/kaggle_output.csv',
                '../../output/kaggle_output.csv',
                # Also look for recent kaggle_links output files
                'output/kaggle_links_*.csv',
            ]
            
            self.input_file = None
            
            # First try exact paths
            for path in possible_paths[:3]:
                if os.path.exists(path):
                    self.input_file = path
                    break
            
            # If not found, look for most recent kaggle_links output
            if not self.input_file:
                import glob
                pattern = 'output/kaggle_links_*.csv'
                matching_files = glob.glob(pattern)
                if matching_files:
                    # Get the most recent file
                    self.input_file = max(matching_files, key=os.path.getctime)
                    self.logger.info(f'Found recent kaggle_links output: {self.input_file}')
        
        if not self.input_file:
            raise ValueError(
                'Input file not found. Please:\n'
                '1. First run: python run.py kaggle_links -a max_pages=10\n'
                '2. Then run: python run.py kaggle_metadata\n'
                'Or provide input_file parameter: -a input_file=path/to/file.csv'
            )
        
        self.logger.info(f'Using input file: {self.input_file}')
        self.model_counter = 0
    
    def start_requests(self):
        """Generate requests from input CSV file"""
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
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        model_name = response.meta.get('model_name', '')
        model_id = response.meta.get('model_id', 0)

        self.logger.info(f'Processing {model_id}: {model_name}')

        # Create a temporary driver and navigate to the actual URL
        # This ensures extraction methods have access to fully-rendered dynamic content
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        temp_driver = webdriver.Chrome(options=chrome_options)

        try:
            # Navigate to the actual URL to get full dynamic content
            temp_driver.get(response.url)

            # Wait for page to load
            time.sleep(2)

            # Parse tree from the temp driver's page source
            tree = self.parse_tree_from_response(response)

            # Create item
            item = KaggleMetadataItem()
            item['model_id'] = model_id
            item['name'] = model_name
            item['kaggle_url'] = response.url

            # Extract using temp_driver which has the correct HTML loaded
            item['short_description'] = self.extract_description(temp_driver, tree, self.selectors, model_name)
            item['downloads'] = self.extract_downloads(temp_driver, tree, self.selectors, model_name)
            item['tags'] = self.extract_tags(temp_driver, tree, self.selectors, model_name)
            item['model_card'] = self.extract_model_card(temp_driver, tree, self.selectors, model_name)
            item['transformers_variations'] = self.extract_transformers_variations(
                temp_driver, self.selectors, model_name, model_id
            )

            # Log concise summary
            self.logger.info(f"✓ {model_name} - Downloads: {item['downloads']}")

            yield item

        finally:
            # Always close the temporary driver
            temp_driver.quit()
    
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
                if self.click_element(driver, action_selector):
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
    
    def extract_transformers_variations(self, driver, selectors: Dict, name: str, 
                                       model_id: int) -> List[Dict]:
        """
        Extract transformers variation entries
        
        Args:
            driver: Selenium driver instance
            selectors: Selectors configuration dictionary
            name: Model name for logging
            model_id: Model ID
            
        Returns:
            List of variation dictionaries
        """
        variations = []
        
        action_selector = selectors.get('transformers_variation_action')
        
        # Try to click the action that reveals the list
        if action_selector:
            try:
                if self.click_element(driver, action_selector):
                    time.sleep(0.5)
            except Exception:
                pass
        
        # Find list items
        elems = []
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, 'li.MuiButtonBase-root')
        except Exception:
            pass
        
        for el in elems:
            try:
                text = el.text.strip()
                if not text:
                    # Try inner p element
                    try:
                        p = el.find_element(By.CSS_SELECTOR, 'p')
                        text = p.text.strip()
                    except Exception:
                        text = ''
                
                if text:
                    variation = {
                        'model_id': model_id,
                        'transformers_variation': text,
                        'transformers_variation_version': '',
                        'transformers_variation_license': '',
                        'transformers_variation_downloads': '',
                        'transformers_model_card': '',
                        'transformers_description': ''
                    }
                    variations.append(variation)
            except Exception:
                continue
        
        return variations
