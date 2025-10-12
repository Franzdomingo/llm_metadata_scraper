"""
Kaggle Links Spider
Scrapes LLM model names and URLs from Kaggle models page
"""

import scrapy
from selenium.webdriver.common.by import By
from my_scraper.spiders.base_spider import BaseSpider
from my_scraper.items import KaggleModelItem
from my_scraper.utils import extract_model_name_from_url, build_full_url


class KaggleLinksSpider(BaseSpider):
    """
    Spider to scrape Kaggle model links
    
    Extracts model names and URLs from Kaggle's models listing page
    """
    
    name = 'kaggle_links'
    allowed_domains = ['kaggle.com']
    start_urls = ['https://www.kaggle.com/models?owner-type=organization']
    
    # Use Kaggle selectors
    site_key = 'kaggle'
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,  # Single request at a time for pagination
        'DOWNLOAD_DELAY': 2.0,
    }
    
    def __init__(self, max_pages=100, *args, **kwargs):
        """
        Initialize spider
        
        Args:
            max_pages: Maximum number of pages to scrape (default: 100)
        """
        super().__init__(*args, **kwargs)
        self.max_pages = int(max_pages)
        self.current_page = 1
        self.seen_urls = set()
    
    def start_requests(self):
        """Generate initial request with Selenium enabled"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'selenium': True,
                    'selenium_wait': 3,
                    'selenium_wait_selector': 'ul li div a[href*="/models/"]',
                    'page_num': self.current_page
                },
                dont_filter=True
            )
    
    def parse(self, response):
        """
        Parse Kaggle models listing page
        
        Args:
            response: Scrapy response object
            
        Yields:
            KaggleModelItem for each model found
            Request for next page if available
        """
        driver = self.get_driver_from_response(response)
        page_num = response.meta.get('page_num', 1)
        
        self.logger.info(f'Parsing page {page_num}')
        
        # Parse the page content
        tree = self.parse_tree_from_response(response)
        
        # Extract model links using configured selector
        model_links_xpath = self.selectors.get('model_links_xpath')
        list_items = tree.xpath(model_links_xpath)
        
        self.logger.info(f'Page {page_num}: Found {len(list_items)} model links')
        
        # Extract data from each link
        for link in list_items:
            href = link.get('href', '')
            
            if not href or href == '/models':
                continue
            
            # Build full URL
            full_url = build_full_url('https://www.kaggle.com', href)
            
            # Skip if already seen
            if full_url in self.seen_urls:
                continue
            
            self.seen_urls.add(full_url)
            
            # Extract model name
            model_name_xpath = self.selectors.get('model_name_xpath')
            name_elements = link.xpath(model_name_xpath)
            
            if name_elements:
                model_name = name_elements[0].strip()
            else:
                # Fallback: extract from link text or URL
                model_name = link.text_content().strip()
                if not model_name:
                    model_name = extract_model_name_from_url(href)
            
            if model_name:
                # Create and yield item
                item = KaggleModelItem()
                item['name'] = model_name
                item['kaggle_url'] = full_url
                
                yield item
        
        # Check if there's a next page and we haven't reached max_pages
        if page_num < self.max_pages:
            has_next = self.check_next_page(driver)
            
            if has_next:
                self.logger.info(f'Navigating to page {page_num + 1}')
                
                # Click next button
                if self.click_next_page(driver):
                    import time
                    time.sleep(2)  # Wait for page to load
                    
                    # Create new request for the next page
                    yield scrapy.Request(
                        url=driver.current_url,
                        callback=self.parse,
                        meta={
                            'selenium': True,
                            'selenium_wait': 3,
                            'selenium_wait_selector': 'ul li div a[href*="/models/"]',
                            'page_num': page_num + 1,
                            'driver': driver  # Reuse existing driver
                        },
                        dont_filter=True
                    )
                else:
                    self.logger.warning(f'Could not click next button on page {page_num}')
            else:
                self.logger.info(f'No more pages after page {page_num}')
        else:
            self.logger.info(f'Reached max_pages limit: {self.max_pages}')
    
    def check_next_page(self, driver) -> bool:
        """
        Check if there's a next page available
        
        Args:
            driver: Selenium driver instance
            
        Returns:
            True if next page is available, False otherwise
        """
        try:
            # Try primary next button selector
            next_button_xpath = self.selectors.get('next_button_xpath')
            next_button = driver.find_element(By.XPATH, next_button_xpath)
            return next_button.is_enabled() and next_button.is_displayed()
        except Exception:
            try:
                # Try alternative next button selector
                next_button_alt_xpath = self.selectors.get('next_button_alt_xpath')
                next_button = driver.find_element(By.XPATH, next_button_alt_xpath)
                return next_button.is_enabled() and next_button.is_displayed()
            except Exception:
                return False
    
    def click_next_page(self, driver) -> bool:
        """
        Click the next page button
        
        Args:
            driver: Selenium driver instance
            
        Returns:
            True if clicked successfully, False otherwise
        """
        try:
            # Try primary next button selector
            next_button_xpath = self.selectors.get('next_button_xpath')
            return self.click_element(driver, next_button_xpath, By.XPATH)
        except Exception:
            try:
                # Try alternative next button selector
                next_button_alt_xpath = self.selectors.get('next_button_alt_xpath')
                return self.click_element(driver, next_button_alt_xpath, By.XPATH)
            except Exception:
                return False
