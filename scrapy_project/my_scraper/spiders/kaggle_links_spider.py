"""
Kaggle Links Spider
Scrapes LLM model names and URLs from Kaggle models page
"""

import scrapy
from selenium.webdriver.common.by import By
from my_scraper.items import KaggleModelItem
from my_scraper.utils import extract_model_name_from_url, build_full_url
from my_scraper.selectors.site_selectors import get_selectors_for_site
from my_scraper.extractors.selenium_utils import get_driver_from_response, parse_tree_from_response, click_element


class KaggleLinksSpider(scrapy.Spider):
    """
    Spider to scrape Kaggle model links
    
    Extracts model names and URLs from Kaggle's models listing page
    """
    
    name = 'kaggle_links'
    allowed_domains = ['kaggle.com']
    start_urls = ['https://www.kaggle.com/models?owner-type=organization']

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
        self.selectors = get_selectors_for_site('kaggle')
    
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
        driver = get_driver_from_response(response)
        page_num = response.meta.get('page_num', 1)

        self.logger.info(f'Parsing page {page_num}')

        # Parse the page content
        tree = parse_tree_from_response(response)
        
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
            import time
            # Small delay to ensure page is fully loaded before checking for next button
            time.sleep(1)
            
            has_next = self.check_next_page(driver)
            
            if has_next:
                self.logger.info(f'Navigating to page {page_num + 1}')
                
                # Click next button
                if self.click_next_page(driver):
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
        # Try multiple selectors to find the next button
        selectors = [
            (By.XPATH, self.selectors.get('next_button_xpath')),
            (By.XPATH, self.selectors.get('next_button_alt_xpath')),
            (By.CSS_SELECTOR, 'button[aria-label="Go to next page"]'),
            (By.XPATH, '//button[@aria-label="Go to next page"]'),
            (By.CSS_SELECTOR, 'button.MuiPaginationItem-previousNext:not([disabled])'),
        ]
        
        for by_type, selector in selectors:
            try:
                next_button = driver.find_element(by_type, selector)
                # Check if button is enabled, displayed, and not disabled
                is_available = (
                    next_button.is_enabled() and 
                    next_button.is_displayed() and
                    'disabled' not in next_button.get_attribute('class').lower() and
                    next_button.get_attribute('disabled') != 'true'
                )
                if is_available:
                    self.logger.debug(f'Next button found and available using {by_type}: {selector}')
                    return True
            except Exception as e:
                self.logger.debug(f'Could not find next button with {by_type}: {selector} - {e}')
                continue
        
        self.logger.debug('No available next button found')
        return False
    
    def click_next_page(self, driver) -> bool:
        """
        Click the next page button
        
        Args:
            driver: Selenium driver instance
            
        Returns:
            True if clicked successfully, False otherwise
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from my_scraper.extractors.selenium_utils import scroll_element_into_view
        
        # Try multiple strategies to click the next button
        selectors = [
            # Primary selectors from config
            (By.XPATH, self.selectors.get('next_button_xpath')),
            (By.XPATH, self.selectors.get('next_button_alt_xpath')),
            # Additional fallback selectors
            (By.CSS_SELECTOR, 'button[aria-label="Go to next page"]'),
            (By.XPATH, '//button[@aria-label="Go to next page"]'),
            (By.CSS_SELECTOR, 'button.MuiPaginationItem-previousNext:not([disabled])'),
            (By.XPATH, '//nav//button[contains(@class, "MuiPaginationItem-previousNext") and not(@disabled)]'),
        ]
        
        for by_type, selector in selectors:
            try:
                # Wait for element to be present and clickable
                wait = WebDriverWait(driver, 5)
                element = wait.until(EC.element_to_be_clickable((by_type, selector)))
                
                # Scroll element into view
                scroll_element_into_view(driver, element, block='center')
                
                # Try regular click first
                try:
                    element.click()
                    self.logger.info(f'Successfully clicked next button using {by_type}: {selector}')
                    return True
                except Exception as click_error:
                    # Try JavaScript click as fallback
                    self.logger.debug(f'Regular click failed, trying JS click: {click_error}')
                    driver.execute_script("arguments[0].click();", element)
                    self.logger.info(f'Successfully clicked next button via JS using {by_type}: {selector}')
                    return True
                    
            except Exception as e:
                self.logger.debug(f'Failed to click with {by_type}: {selector} - {e}')
                continue
        
        # All strategies failed
        self.logger.error('All next button click strategies failed')
        return False
