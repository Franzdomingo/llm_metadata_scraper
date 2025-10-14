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
        self.seen_page_content_hashes = set()  # Track page content by hash
        self.selectors = get_selectors_for_site('kaggle')
        self.previous_first_model = None  # Track first model URL to detect page change
    
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
        # For page 1, use response.text (initial page load)
        # For subsequent pages, use driver.page_source (after navigation)
        if page_num == 1:
            tree = parse_tree_from_response(response)
        else:
            # After navigation, parse from driver's current page source
            tree = parse_tree_from_response(response, driver=driver)
        
        # Extract model links using configured selector
        model_links_xpath = self.selectors.get('model_links_xpath')
        list_items = tree.xpath(model_links_xpath)
        
        self.logger.info(f'Page {page_num}: Found {len(list_items)} model links')
        
        # Track if we found any new models on this page
        new_models_count = 0
        first_model_url = None  # Track first model on this page
        duplicate_count = 0  # Track duplicates for debugging
        
        # Extract data from each link
        for link in list_items:
            href = link.get('href', '')
            
            if not href or href == '/models':
                continue
            
            # Build full URL
            full_url = build_full_url('https://www.kaggle.com', href)
            
            # Track first model URL on this page for content change detection
            if first_model_url is None:
                first_model_url = full_url
            
            # Skip if already seen
            if full_url in self.seen_urls:
                duplicate_count += 1
                self.logger.debug(f'Page {page_num}: Duplicate URL: {full_url}')
                continue
            
            self.seen_urls.add(full_url)
            new_models_count += 1
            
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
        
        # Log results
        self.logger.info(f'Page {page_num}: Scraped {new_models_count} new models (total seen: {len(self.seen_urls)})')
        
        # Set the first model for page 1 (for comparison after clicking next)
        if page_num == 1 and first_model_url:
            self.previous_first_model = first_model_url
            self.logger.info(f'Page 1: Set first model reference: {first_model_url}')
        
        # If we found zero new models, we're likely re-scraping the same page
        if new_models_count == 0 and page_num > 1:
            self.logger.warning(f'Page {page_num}: Found 0 new models - likely on last page or duplicate')
            self.logger.info('Stopping pagination - no new content found')
            return
        
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
                    # Wait for page to load and content to update
                    self.logger.info(f'Waiting for page {page_num + 1} content to load...')
                    
                    # Store the first model link before navigation to detect change
                    old_first_model = self.previous_first_model
                    
                    # Wait for content to actually change by monitoring multiple indicators
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    max_wait_seconds = 15
                    content_changed = False
                    
                    # Initial wait for click action to propagate
                    time.sleep(2)
                    
                    for attempt in range(max_wait_seconds):
                        try:
                            # Primary check: Verify the first model link has changed
                            first_link_elements = driver.find_elements(By.XPATH, '//ul/li/div/a[contains(@href, "/models/")]')
                            if first_link_elements:
                                current_first_model = first_link_elements[0].get_attribute('href')
                                
                                # Also check page indicator to ensure we're on the right page
                                selected_page_elements = driver.find_elements(By.CSS_SELECTOR, 'button[aria-current="true"][data-testid="selectedPage"]')
                                current_page_indicator = None
                                if selected_page_elements:
                                    current_page_indicator = selected_page_elements[0].text.strip()
                                
                                expected_page = str(page_num + 1)
                                
                                # Content has changed if:
                                # 1. First model URL is different from before
                                # 2. Page indicator shows expected page (optional check)
                                if current_first_model != old_first_model:
                                    if current_page_indicator == expected_page:
                                        self.logger.info(f'Content changed detected after {attempt + 2} seconds')
                                        self.logger.info(f'Old first model: {old_first_model}')
                                        self.logger.info(f'New first model: {current_first_model}')
                                        self.logger.info(f'Page indicator: {current_page_indicator}')
                                        # Update previous_first_model NOW, before parsing
                                        self.previous_first_model = current_first_model
                                        content_changed = True
                                        break
                                    else:
                                        self.logger.info(f'First model changed but page indicator mismatch: expected={expected_page}, got={current_page_indicator}')
                                else:
                                    if current_page_indicator:
                                        self.logger.info(f'Attempt {attempt + 1}: Page indicator={current_page_indicator}, but content unchanged (first model still: {current_first_model})')
                                    else:
                                        self.logger.info(f'Attempt {attempt + 1}: Content still loading...')
                            
                            # Wait before next check
                            time.sleep(1)
                            
                        except Exception as e:
                            self.logger.debug(f'Error checking for content change: {e}')
                            time.sleep(1)
                    
                    if not content_changed:
                        self.logger.warning(f'Page {page_num}: Content did not change after clicking next button (waited {max_wait_seconds + 2}s)')
                        self.logger.info('Stopping pagination - likely on last page or pagination failed')
                        return
                    
                    # Additional buffer for all content to fully load and render
                    time.sleep(2)
                    
                    # DON'T yield a new Request - that would reload the page!
                    # Instead, recursively call parse with updated metadata
                    # Create a mock response object with updated page_num
                    response.meta['page_num'] = page_num + 1
                    
                    # Recursively parse the next page (driver is already on the new page)
                    yield from self.parse(response)
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
        # Prioritize more reliable selectors first
        selectors = [
            # Most reliable - CSS selector with aria-label
            (By.CSS_SELECTOR, 'button[aria-label="Go to next page"]'),
            # Second most reliable - CSS with class
            (By.CSS_SELECTOR, 'button.MuiPaginationItem-previousNext:not([disabled])'),
            # XPath alternatives
            (By.XPATH, '//button[@aria-label="Go to next page"]'),
            (By.XPATH, '//nav//button[contains(@class, "MuiPaginationItem-previousNext") and not(@disabled)]'),
            # Config selectors as fallback
            (By.XPATH, self.selectors.get('next_button_xpath')),
            (By.XPATH, self.selectors.get('next_button_alt_xpath')),
        ]
        
        for by_type, selector in selectors:
            try:
                next_button = driver.find_element(by_type, selector)
                
                # Get button attributes for detailed checking
                button_classes = next_button.get_attribute('class') or ''
                button_disabled = next_button.get_attribute('disabled')
                button_aria_disabled = next_button.get_attribute('aria-disabled')
                
                # Check if button is enabled, displayed, and not disabled
                is_available = (
                    next_button.is_enabled() and 
                    next_button.is_displayed() and
                    'disabled' not in button_classes.lower() and
                    button_disabled != 'true' and
                    button_aria_disabled != 'true'
                )
                
                if is_available:
                    self.logger.info(f'Next button found and available using {by_type}: {selector}')
                    return True
                else:
                    self.logger.info(f'Next button found but disabled: {by_type}: {selector}')
                    
            except Exception as e:
                self.logger.info(f'Could not find next button with {by_type}: {selector} - {e}')
                continue
        
        self.logger.info('No available next button found')
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
        # Prioritize more reliable selectors first
        selectors = [
            # Most reliable - CSS selector with aria-label
            (By.CSS_SELECTOR, 'button[aria-label="Go to next page"]'),
            # Second most reliable - CSS with class
            (By.CSS_SELECTOR, 'button.MuiPaginationItem-previousNext:not([disabled])'),
            # XPath alternatives
            (By.XPATH, '//button[@aria-label="Go to next page"]'),
            (By.XPATH, '//nav//button[contains(@class, "MuiPaginationItem-previousNext") and not(@disabled)]'),
            # Config selectors as fallback
            (By.XPATH, self.selectors.get('next_button_xpath')),
            (By.XPATH, self.selectors.get('next_button_alt_xpath')),
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
