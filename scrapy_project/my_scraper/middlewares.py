"""
Custom middlewares for Scrapy spiders

This module contains custom middlewares for:
- Selenium integration for dynamic content
- Random user agent rotation
"""

import random
import logging
from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from my_scraper.selectors.site_selectors import GeneralSelectors


class SeleniumMiddleware:
    """
    Scrapy middleware for Selenium integration
    
    Handles requests that require JavaScript rendering or dynamic content loading
    """
    
    def __init__(self, driver_name='chrome', driver_executable_path=None, driver_arguments=None):
        """
        Initialize the Selenium middleware
        
        Args:
            driver_name: Name of the browser driver (default: 'chrome')
            driver_executable_path: Path to the driver executable (optional)
            driver_arguments: List of command-line arguments for the driver
        """
        self.driver_name = driver_name
        self.driver_executable_path = driver_executable_path
        self.driver_arguments = driver_arguments or []
        self.driver = None
        
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler settings"""
        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME', 'chrome')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS', [])
        
        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            driver_arguments=driver_arguments
        )
        
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        
        return middleware
    
    def spider_opened(self, spider):
        """Initialize the Selenium driver when spider opens"""
        logging.info(f'Initializing Selenium {self.driver_name} driver')
        
        if self.driver_name == 'chrome':
            chrome_options = Options()
            
            # Add configured arguments
            for arg in self.driver_arguments:
                chrome_options.add_argument(arg)
            
            # Add random user agent
            try:
                user_agent = random.choice(GeneralSelectors.USER_AGENTS)
                chrome_options.add_argument(f'user-agent={user_agent}')
            except Exception:
                logging.debug('No user agents configured, using default browser UA')
            
            # Create driver
            if self.driver_executable_path:
                self.driver = webdriver.Chrome(
                    executable_path=self.driver_executable_path,
                    options=chrome_options
                )
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
                
        else:
            raise NotImplementedError(f'Driver {self.driver_name} is not supported')
            
        logging.info('Selenium driver initialized successfully')
    
    def spider_closed(self, spider):
        """Close the Selenium driver when spider closes"""
        if self.driver:
            logging.info('Closing Selenium driver')
            self.driver.quit()
    
    def process_request(self, request, spider):
        """
        Process requests that need Selenium
        
        Only processes requests with meta['selenium'] = True
        """
        if not request.meta.get('selenium'):
            return None
        
        logging.debug(f'Selenium processing: {request.url}')
        
        try:
            # Load the page
            self.driver.get(request.url)
            
            # Wait for page to load (configurable via meta)
            wait_time = request.meta.get('selenium_wait', 3)
            wait_selector = request.meta.get('selenium_wait_selector')
            
            if wait_selector:
                wait = WebDriverWait(self.driver, wait_time)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector)))
            else:
                import time
                time.sleep(wait_time)
            
            # Get page source and create response
            body = self.driver.page_source.encode('utf-8')
            
            # Store driver in meta for spider to use if needed
            request.meta['driver'] = self.driver
            
            return HtmlResponse(
                url=request.url,
                body=body,
                encoding='utf-8',
                request=request
            )
            
        except Exception as e:
            logging.error(f'Selenium error processing {request.url}: {e}')
            return None


class RandomUserAgentMiddleware:
    """
    Middleware to rotate user agents randomly
    """
    
    def __init__(self, user_agents=None):
        """
        Initialize with a list of user agents
        
        Args:
            user_agents: List of user agent strings (optional)
        """
        self.user_agents = user_agents or GeneralSelectors.USER_AGENTS
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler settings"""
        return cls()
    
    def process_request(self, request, spider):
        """Set a random user agent for the request"""
        if self.user_agents:
            user_agent = random.choice(self.user_agents)
            request.headers['User-Agent'] = user_agent
