"""
Base spider class with common functionality
"""

import scrapy
import logging
import time
from typing import Optional, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html as lxml_html
from my_scraper.selectors.site_selectors import get_selectors_for_site
from my_scraper.utils import html_to_text, is_numeric_value


class BaseSpider(scrapy.Spider):
    """
    Base spider class with common scraping functionality
    
    Provides helper methods for:
    - Selenium interaction
    - Element extraction
    - Data parsing
    """
    
    # Override in subclasses
    name = 'base_spider'
    allowed_domains = []
    start_urls = []
    
    # Site selector key (e.g., 'kaggle', 'nvidia')
    site_key = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selectors = None
        if self.site_key:
            self.selectors = get_selectors_for_site(self.site_key)
    
    def get_driver_from_response(self, response) -> Optional[webdriver.Chrome]:
        """
        Get Selenium driver from response meta
        
        Args:
            response: Scrapy response object
            
        Returns:
            Selenium driver instance or None
        """
        return response.meta.get('driver')
    
    def parse_tree_from_response(self, response, driver: Optional[webdriver.Chrome] = None) -> lxml_html.HtmlElement:
        """
        Create lxml tree from response

        Args:
            response: Scrapy response object
            driver: Optional Selenium driver (not used, kept for backwards compatibility)

        Returns:
            lxml HtmlElement tree
        """
        # Always use response.text which contains the page source captured by middleware
        # at the correct time. DO NOT use driver.page_source as the driver may have
        # navigated to a different page by the time this method is called.
        return lxml_html.fromstring(response.text)
    
    def extract_description(self, driver: webdriver.Chrome, tree: lxml_html.HtmlElement, 
                          selectors: Dict, name: str) -> str:
        """
        Extract description using configured selectors
        
        Args:
            driver: Selenium driver instance
            tree: lxml tree object
            selectors: Selectors configuration dictionary
            name: Model name for logging
            
        Returns:
            Extracted description text or empty string
        """
        description = ""

        # First try CSS selectors (via Selenium) - these are more reliable for dynamic content
        for selector in selectors.get('description', []):
            if selector.startswith('.') or selector.startswith('#'):
                try:
                    self.logger.debug(f"Trying description CSS selector via Selenium: {selector}")
                    desc_element = driver.find_element(By.CSS_SELECTOR, selector)
                    outer = desc_element.get_attribute('outerHTML')
                    if outer and outer.strip():
                        self.logger.info(f"Found short_description using CSS selector: {selector}")
                        return html_to_text(outer)
                except Exception as e:
                    self.logger.debug(f"Description CSS selector {selector} not found: {e}")

        # Next try XPath selectors using lxml tree
        for selector in selectors.get('description', []):
            if selector.startswith('.') or selector.startswith('#'):
                continue
            try:
                self.logger.debug(f"Trying description XPath selector: {selector}")
                desc_elements = tree.xpath(selector)
                if desc_elements and desc_elements[0].text_content().strip():
                    self.logger.info(f"Found short_description using XPath selector: {selector}")
                    return desc_elements[0].text_content().strip()
            except Exception as e:
                self.logger.debug(f"Description XPath selector {selector} failed: {e}")

        # Final fallback: use configured CSS fallback
        if 'description_css_fallback' in selectors:
            try:
                desc_element = driver.find_element(By.CSS_SELECTOR, selectors['description_css_fallback'])
                outer = desc_element.get_attribute('outerHTML')
                if outer and outer.strip():
                    self.logger.info(f"Found short_description using fallback CSS selector")
                    return html_to_text(outer)
            except Exception:
                self.logger.warning(f"Could not find short_description for {name}")

        return description
    
    def extract_downloads(self, driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
                         selectors: Dict, name: str) -> str:
        """
        Extract download count using configured selectors

        Args:
            driver: Selenium driver instance (for dynamic content)
            tree: lxml tree object
            selectors: Selectors configuration dictionary
            name: Model name for logging

        Returns:
            Extracted download count or empty string
        """
        downloads = ""
        all_candidates = []

        # If no driver, can't extract downloads (requires JavaScript rendering)
        if not driver:
            self.logger.debug(f"No driver provided, skipping downloads extraction for {name}")
            return downloads
        
        # First try CSS selectors via Selenium for dynamic content
        for selector in selectors.get('downloads', []):
            # Check if it's a CSS selector (starts with . or #)
            if selector.startswith('.') or selector.startswith('#') or selector.startswith('span'):
                try:
                    self.logger.debug(f"Trying downloads CSS selector via Selenium: {selector}")
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    self.logger.debug(f"Found {len(elements)} elements with CSS selector")
                    
                    for elem in elements:
                        try:
                            text = elem.text.strip()
                            self.logger.debug(f"Checking element text: '{text}'")
                            if text and is_numeric_value(text):
                                # Filter out engagement values (small decimals < 1 without K/M/B suffix)
                                try:
                                    # Check if it's a small decimal that looks like engagement ratio
                                    if '.' in text and not any(x in text.upper() for x in ['K', 'M', 'B']):
                                        val = float(text.replace(',', ''))
                                        if val < 1:
                                            self.logger.debug(f"Skipping engagement-like value: {text}")
                                            continue
                                except (ValueError, TypeError):
                                    pass  # If conversion fails, keep it as candidate
                                
                                all_candidates.append(text)
                                self.logger.debug(f"Found candidate: {text}")
                        except Exception as e:
                            self.logger.debug(f"Error getting text from element: {e}")
                            continue
                except Exception as e:
                    self.logger.debug(f"Downloads CSS selector {selector} failed: {e}")
        
        # Try XPath selectors using lxml tree as fallback
        for selector in selectors.get('downloads', []):
            # Skip CSS selectors (already tried above)
            if selector.startswith('.') or selector.startswith('#') or selector.startswith('span'):
                continue
                
            try:
                self.logger.debug(f"Trying downloads XPath selector: {selector}")
                download_elements = tree.xpath(selector)
                self.logger.debug(f"Found {len(download_elements)} elements with XPath")
                
                if download_elements:
                    for elem in download_elements:
                        text = elem.text_content().strip()
                        self.logger.debug(f"Checking element text: '{text}'")
                        if text and is_numeric_value(text):
                            # Filter out engagement values (small decimals < 1 without K/M/B suffix)
                            try:
                                if '.' in text and not any(x in text.upper() for x in ['K', 'M', 'B']):
                                    val = float(text.replace(',', ''))
                                    if val < 1:
                                        self.logger.debug(f"Skipping engagement-like value: {text}")
                                        continue
                            except (ValueError, TypeError):
                                pass  # If conversion fails, keep it as candidate
                            
                            all_candidates.append(text)
                            self.logger.debug(f"Found candidate: {text}")
            except Exception as e:
                self.logger.debug(f"Downloads XPath selector {selector} failed: {e}")
                continue

        # Choose the best candidate from all found values
        # Prefer: 1) Values with K/M/B suffix (total downloads), 2) Largest plain number
        if all_candidates:
            self.logger.info(f"Found {len(all_candidates)} download candidates: {all_candidates}")
            
            # Separate candidates with suffix (K/M/B) from plain numbers
            with_suffix = [c for c in all_candidates if any(x in c.upper() for x in ['K', 'M', 'B'])]
            plain_numbers = [c for c in all_candidates if c not in with_suffix]
            
            # Prefer largest value with suffix, or largest plain number
            if with_suffix:
                # Sort by converting to numeric value for comparison
                def parse_suffix(val):
                    try:
                        val_upper = val.upper()
                        # Extract only digits and decimal point
                        num_str = ''.join(c for c in val if c.isdigit() or c == '.')
                        if not num_str or num_str == '.':
                            return 0
                        num = float(num_str)
                        if 'K' in val_upper:
                            return num * 1000
                        elif 'M' in val_upper:
                            return num * 1000000
                        elif 'B' in val_upper:
                            return num * 1000000000
                        return num
                    except (ValueError, TypeError):
                        return 0
                
                downloads = max(with_suffix, key=parse_suffix)
                self.logger.info(f"Selected downloads (with suffix): {downloads}")
            elif plain_numbers:
                # Convert to int for comparison (remove commas and extract only digits)
                def to_int(val):
                    try:
                        # Extract only digits
                        digits = ''.join(c for c in val if c.isdigit())
                        if not digits:
                            return 0
                        return int(digits)
                    except (ValueError, TypeError):
                        return 0
                downloads = max(plain_numbers, key=to_int)
                self.logger.info(f"Selected downloads (plain number): {downloads}")
            
            return downloads

        # Fallback: Search for numeric values near "DOWNLOADS" heading
        if not downloads:
            self.logger.debug(f"Trying fallback: searching for downloads near 'DOWNLOADS' heading")
            try:
                # Strategy 1: Find the DOWNLOADS heading and look for siblings/nearby elements
                downloads_heading = driver.find_elements(By.XPATH, "//*[contains(text(), 'DOWNLOADS') or contains(text(), 'Downloads')]")

                if downloads_heading:
                    self.logger.debug(f"Found {len(downloads_heading)} 'DOWNLOADS' headings")

                    # Look for parent container and find numeric value within it
                    for heading in downloads_heading[:2]:
                        try:
                            # Try to find parent div/section
                            parent = heading.find_element(By.XPATH, './ancestor::div[1]')
                            # Look for all text in the parent
                            text = parent.text
                            # Extract numbers from the text
                            import re
                            numbers = re.findall(r'\d+(?:[,.]\d+)?[KMB]?', text)
                            for num in numbers:
                                if is_numeric_value(num):
                                    all_candidates.append(num)
                                    self.logger.debug(f"Found candidate near DOWNLOADS heading: {num}")
                        except Exception:
                            continue

                # Strategy 2: Look for all spans with numeric values
                if not all_candidates:
                    all_spans = driver.find_elements(By.TAG_NAME, 'span')

                    for span in all_spans:
                        try:
                            text = span.text.strip()
                            if text and is_numeric_value(text):
                                # Skip very small decimals (engagement ratios)
                                try:
                                    if '.' in text and not any(x in text.upper() for x in ['K', 'M', 'B']):
                                        val = float(text.replace(',', ''))
                                        if val < 1:
                                            continue
                                except (ValueError, TypeError):
                                    pass

                                all_candidates.append(text)
                        except:
                            continue

                if all_candidates:
                    self.logger.info(f"Found {len(all_candidates)} download candidates: {all_candidates[:10]}")

                    # Prefer values with K/M/B suffix, then largest plain number
                    with_suffix = [c for c in all_candidates if any(x in c.upper() for x in ['K', 'M', 'B'])]
                    if with_suffix:
                        downloads = with_suffix[0]
                        self.logger.info(f"Using first value with suffix: {downloads}")
                    elif all_candidates:
                        # Find largest number (likely to be total downloads)
                        def to_int(val):
                            try:
                                digits = ''.join(c for c in val if c.isdigit())
                                return int(digits) if digits else 0
                            except:
                                return 0
                        downloads = max(all_candidates, key=to_int)
                        self.logger.info(f"Using largest number: {downloads}")

            except Exception as e:
                self.logger.error(f"Fallback download search failed: {e}")

        if not downloads:
            self.logger.warning(f"Could not find downloads for {name}")
        
        return downloads
    
    def extract_tags(self, driver: webdriver.Chrome, tree: lxml_html.HtmlElement,
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
            self.logger.debug(f"No driver provided, skipping tags extraction for {name}")
            return ''

        try:
            self.logger.debug(f"Starting tag extraction for {name}")

            # First try the specific tag link selector
            tag_link_selector = selectors.get('tag_links')
            if tag_link_selector:
                self.logger.debug(f"Trying specific tag link selector: {tag_link_selector}")
                try:
                    tag_links = driver.find_elements(By.CSS_SELECTOR, tag_link_selector)
                    self.logger.debug(f"Found {len(tag_links)} tag links")
                    
                    for link in tag_links:
                        try:
                            tag_text = link.text.strip()
                            if tag_text and tag_text not in tags:
                                tags.append(tag_text)
                        except Exception:
                            continue
                            
                    if tags:
                        self.logger.info(f"Found {len(tags)} tags using specific selector")
                        return ', '.join(tags)
                        
                except Exception as e:
                    self.logger.debug(f"Specific tag link selector failed: {e}")

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
                    self.logger.debug(f"Container selector {selector} failed: {e}")
                    continue

            # Fallback: Look for links near "TAGS" or "Tags" heading
            if not tags:
                self.logger.debug(f"Trying fallback: searching for links near 'TAGS' heading")
                try:
                    # Find TAGS heading
                    tags_heading = driver.find_elements(By.XPATH, "//*[contains(text(), 'TAGS') or contains(text(), 'Tags')]")

                    if tags_heading:
                        self.logger.debug(f"Found {len(tags_heading)} 'TAGS' headings")

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
                                            self.logger.debug(f"Found tag via fallback: {tag_text}")
                            except Exception:
                                continue

                        if tags:
                            self.logger.info(f"Found {len(tags)} tags using fallback method")
                    else:
                        self.logger.debug("No TAGS heading found")

                except Exception as e:
                    self.logger.debug(f"Fallback tags search failed: {e}")

            if tags:
                self.logger.info(f"Successfully extracted {len(tags)} tags for {name}")
            else:
                self.logger.warning(f"Could not find any tags for {name}")

        except Exception as e:
            self.logger.error(f"Error extracting tags for {name}: {e}")

        return ', '.join(tags) if tags else ''
    
    def wait_for_element(self, driver: webdriver.Chrome, selector: str, 
                        by: By = By.CSS_SELECTOR, timeout: int = 10) -> Optional[any]:
        """
        Wait for element to be present
        
        Args:
            driver: Selenium driver instance
            selector: Element selector
            by: Selenium By type (default: CSS_SELECTOR)
            timeout: Wait timeout in seconds
            
        Returns:
            WebElement or None
        """
        try:
            wait = WebDriverWait(driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, selector)))
            return element
        except Exception as e:
            self.logger.debug(f"Element not found: {selector} - {e}")
            return None
    
    def click_element(self, driver: webdriver.Chrome, selector: str, 
                     by: By = By.CSS_SELECTOR) -> bool:
        """
        Try to click an element (with JS fallback)
        
        Args:
            driver: Selenium driver instance
            selector: Element selector
            by: Selenium By type (default: CSS_SELECTOR)
            
        Returns:
            True if clicked successfully, False otherwise
        """
        try:
            element = driver.find_element(by, selector)
            try:
                element.click()
                self.logger.debug(f"Clicked element: {selector}")
                return True
            except Exception:
                # Try JavaScript click as fallback
                driver.execute_script("arguments[0].click();", element)
                self.logger.debug(f"Clicked element via JS: {selector}")
                return True
        except Exception as e:
            self.logger.debug(f"Could not click element: {selector} - {e}")
            return False
