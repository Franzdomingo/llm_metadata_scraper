"""
Utility functions for web scraping
Contains text cleaning, HTML parsing, and common helper functions
"""

import re
import logging
from lxml import html
from typing import Optional, List
from my_scraper.selectors.site_selectors import GeneralSelectors


def html_to_text(html_snippet: str) -> str:
    """
    Convert an HTML snippet (outerHTML) into cleaned plain text.

    Uses lxml to parse and extract text_content(), then collapses whitespace.
    
    Args:
        html_snippet: HTML string to convert
        
    Returns:
        Cleaned plain text
    """
    if not html_snippet:
        return ''

    try:
        node = html.fromstring(html_snippet)
        text = node.text_content() or ''
    except Exception:
        # Fallback: remove tags with a simple regex
        text = re.sub(r'<[^>]+>', ' ', html_snippet)

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_numeric_value(text: str) -> bool:
    """
    Check if text represents a numeric value (including K/M suffixes)
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be a numeric value
    """
    # Simple digit check
    if text.isdigit():
        return True
    
    # Check against numeric patterns from config
    for pattern in GeneralSelectors.NUMERIC_PATTERNS:
        if re.match(pattern, text):
            return True
    
    # Fallback: check for common download indicators
    return bool(re.match(r'\d+[KkMmBb]?', text) or 
               ('K' in text and any(char.isdigit() for char in text)) or
               ('M' in text and any(char.isdigit() for char in text)))


def clean_text(text: str) -> str:
    """
    Clean text by removing excessive whitespace and special characters
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ''
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_model_name_from_url(url: str) -> str:
    """
    Extract a readable model name from a URL
    
    Args:
        url: Model URL
        
    Returns:
        Extracted model name
    """
    parts = url.strip('/').split('/')
    if len(parts) >= 2:
        return parts[-1].replace('-', ' ').title()
    return ''


def setup_logging(level: int = logging.INFO) -> None:
    """
    Setup logging configuration
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )


def safe_extract(elements: List, index: int = 0, default: str = '') -> str:
    """
    Safely extract text from a list of elements
    
    Args:
        elements: List of elements
        index: Index to extract from (default: 0)
        default: Default value if extraction fails
        
    Returns:
        Extracted text or default value
    """
    try:
        if elements and len(elements) > index:
            return elements[index].strip() if hasattr(elements[index], 'strip') else str(elements[index])
    except Exception:
        pass
    return default


def build_full_url(base_url: str, href: str) -> str:
    """
    Build a full URL from a base URL and href
    
    Args:
        base_url: Base URL (e.g., 'https://www.kaggle.com')
        href: Relative or absolute URL
        
    Returns:
        Full URL
    """
    if href.startswith('http'):
        return href
    
    if href.startswith('/'):
        return f"{base_url.rstrip('/')}{href}"
    
    return f"{base_url.rstrip('/')}/{href.lstrip('/')}"
