"""
Custom middlewares for Scrapy spiders

This module contains custom middlewares for:
- Selenium integration for dynamic content
- Random user agent rotation
"""

import random
import logging
import threading
from queue import Queue, Empty
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
    Scrapy middleware for Selenium integration with thread-safe driver pool

    Handles requests that require JavaScript rendering or dynamic content loading.
    Uses a pool of Selenium drivers to support concurrent requests.
    """

    def __init__(self, driver_name='chrome', driver_executable_path=None, driver_arguments=None, pool_size=8):
        """
        Initialize the Selenium middleware

        Args:
            driver_name: Name of the browser driver (default: 'chrome')
            driver_executable_path: Path to the driver executable (optional)
            driver_arguments: List of command-line arguments for the driver
            pool_size: Number of driver instances in the pool (default: 8)
        """
        self.driver_name = driver_name
        self.driver_executable_path = driver_executable_path
        self.driver_arguments = driver_arguments or []
        self.pool_size = pool_size
        self.driver_pool = Queue()
        self.lock = threading.Lock()
        self.active_drivers = 0
        self.total_requests_processed = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler settings"""
        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME', 'chrome')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS', [])
        pool_size = crawler.settings.get('SELENIUM_POOL_SIZE', 8)

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            driver_arguments=driver_arguments,
            pool_size=pool_size
        )

        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)

        return middleware
    
    def _create_driver(self):
        """Create a new Selenium driver instance"""
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
                return webdriver.Chrome(
                    executable_path=self.driver_executable_path,
                    options=chrome_options
                )
            else:
                return webdriver.Chrome(options=chrome_options)

        else:
            raise NotImplementedError(f'Driver {self.driver_name} is not supported')

    def spider_opened(self, spider):
        """Initialize the Selenium driver pool when spider opens"""
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()

        logging.info("="*70)
        logging.info("SELENIUM DRIVER POOL INITIALIZATION")
        logging.info("="*70)
        logging.info(f'System CPU Cores: {cpu_count}')
        logging.info(f'Initializing {self.pool_size} {self.driver_name} drivers ({self.pool_size/cpu_count*100:.1f}% of CPU cores)')
        logging.info("-"*70)

        for i in range(self.pool_size):
            try:
                driver = self._create_driver()
                self.driver_pool.put(driver)
                logging.info(f'Driver {i+1}/{self.pool_size} initialized successfully')
            except Exception as e:
                logging.error(f'Failed to initialize driver {i+1}: {e}')

        initialized_count = self.driver_pool.qsize()
        logging.info("="*70)
        logging.info(f'Driver Pool Ready: {initialized_count}/{self.pool_size} drivers available')
        logging.info(f'Active Drivers: {self.active_drivers}')
        logging.info("="*70)
    
    def spider_closed(self, spider):
        """Close all Selenium drivers in the pool when spider closes"""
        logging.info("="*70)
        logging.info("SELENIUM DRIVER POOL SHUTDOWN")
        logging.info("="*70)
        logging.info(f'Total Requests Processed: {self.total_requests_processed}')
        logging.info(f'Active Drivers at Shutdown: {self.active_drivers}')
        logging.info(f'Available Drivers in Pool: {self.driver_pool.qsize()}')
        logging.info("-"*70)

        closed_count = 0
        while not self.driver_pool.empty():
            try:
                driver = self.driver_pool.get_nowait()
                driver.quit()
                closed_count += 1
                logging.info(f'Closed driver {closed_count}/{self.pool_size}')
            except Empty:
                break
            except Exception as e:
                logging.error(f'Error closing driver: {e}')

        logging.info("="*70)
        logging.info(f'Driver Pool Shutdown Complete: {closed_count} drivers closed')
        logging.info("="*70)
    
    def process_request(self, request, spider):
        """
        Process requests that need Selenium using driver pool

        Only processes requests with meta['selenium'] = True
        """
        if not request.meta.get('selenium'):
            return None

        logging.debug(f'Selenium processing: {request.url}')

        driver = None
        try:
            # Get a driver from the pool (blocks if pool is empty)
            available_before = self.driver_pool.qsize()
            driver = self.driver_pool.get(timeout=30)

            with self.lock:
                self.active_drivers += 1
                self.total_requests_processed += 1

            available_after = self.driver_pool.qsize()
            logging.debug(f'Acquired driver from pool | Active: {self.active_drivers}/{self.pool_size} | Available: {available_after} | Total Processed: {self.total_requests_processed}')

            # Load the page
            logging.debug(f'Loading URL in driver: {request.url}')
            driver.get(request.url)

            # Wait for page to load (configurable via meta)
            wait_time = request.meta.get('selenium_wait', 3)
            wait_selector = request.meta.get('selenium_wait_selector')

            if wait_selector:
                wait = WebDriverWait(driver, wait_time)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector)))
            else:
                import time
                time.sleep(wait_time)

            # Verify the driver is on the correct page
            current_url = driver.current_url
            logging.debug(f'Driver current URL: {current_url}')
            if current_url != request.url:
                logging.warning(f'URL mismatch! Requested: {request.url}, Current: {current_url}')

            # Get page source and create response
            body = driver.page_source.encode('utf-8')

            # Store driver in meta for spider to use if needed
            request.meta['driver'] = driver
            # Store flag to return driver to pool
            request.meta['driver_from_pool'] = True

            return HtmlResponse(
                url=request.url,
                body=body,
                encoding='utf-8',
                request=request
            )

        except Empty:
            logging.error(f'Timeout waiting for driver from pool for {request.url}')
            return None
        except Exception as e:
            logging.error(f'Selenium error processing {request.url}: {e}')
            # Return driver to pool if we acquired it
            if driver:
                with self.lock:
                    self.active_drivers -= 1
                self.driver_pool.put(driver)
            return None

    def process_response(self, request, response, spider):
        """Return driver to pool after processing"""
        if request.meta.get('driver_from_pool') and request.meta.get('driver'):
            driver = request.meta['driver']

            with self.lock:
                self.active_drivers -= 1

            self.driver_pool.put(driver)
            available = self.driver_pool.qsize()
            logging.debug(f'Returned driver to pool | Active: {self.active_drivers}/{self.pool_size} | Available: {available}')
        return response


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


class ProxyRotationMiddleware:
    """
    Middleware to rotate proxies for requests

    Supports both HTTP/HTTPS proxies and can use free proxy lists
    or paid proxy services.
    """

    def __init__(self, proxies=None, enable_rotation=False):
        """
        Initialize with a list of proxies

        Args:
            proxies: List of proxy URLs (optional)
            enable_rotation: Whether to enable proxy rotation
        """
        self.proxies = proxies or []
        self.enable_rotation = enable_rotation
        self.proxy_index = 0
        self.logger = logging.getLogger(__name__)

        if self.enable_rotation and not self.proxies:
            self.logger.warning('Proxy rotation enabled but no proxies configured')

    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler settings"""
        proxies = crawler.settings.get('ROTATING_PROXIES', [])
        enable_rotation = crawler.settings.get('ENABLE_PROXY_ROTATION', False)
        return cls(proxies=proxies, enable_rotation=enable_rotation)

    def process_request(self, request, spider):
        """Set a proxy for the request"""
        if not self.enable_rotation or not self.proxies:
            return None

        # Skip proxy for Selenium requests (handle in Selenium driver)
        if request.meta.get('selenium'):
            return None

        # Round-robin proxy selection
        proxy = self.proxies[self.proxy_index % len(self.proxies)]
        self.proxy_index += 1

        request.meta['proxy'] = proxy
        self.logger.debug(f'Using proxy: {proxy}')

    def process_exception(self, request, exception, spider):
        """Handle proxy failures"""
        if request.meta.get('proxy'):
            self.logger.warning(f'Proxy {request.meta["proxy"]} failed: {exception}')
        return None
