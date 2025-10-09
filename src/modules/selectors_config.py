#!/usr/bin/env python3
"""
Selectors Configuration
Contains all CSS/XPath selectors used for web scraping
Author: Franz Phillip G. Domingo
Date: 2025-10-08
"""

from typing import Dict, List

class KaggleSelectors:
    """Configuration class for Kaggle scraping selectors"""
    
    # Description selectors - ordered by priority (most specific first)
    DESCRIPTION_SELECTORS: List[str] = [
        '//p[@class="sc-gGKoUb jJPcnF"]',
        '//div[@class="sc-fhfEft"]//p[2]',
        './/span/p[1]',
        '.sc-fhfEft > p:nth-child(2)'  # CSS selector for Selenium fallback
    ]
    
    # Download count selectors - ordered by priority
    DOWNLOAD_SELECTORS: List[str] = [
        '//span[@class="sc-kCuUfV sc-lmgiAw iPCsnU iURAhc"]',
        '//div[@class="sc-kuWjmJ fwCGxc"]//span[contains(@class, "iPCsnU")]',
        '//div[contains(@class, "sc-hYrTYH")]//span[contains(@class, "sc-kCuUfV")]',
        '//span[contains(@class, "sc-kCuUfV")]'  # Broader fallback
    ]
    
    # Tag selectors - ordered by priority (based on actual HTML structure)
    TAG_SELECTORS: List[str] = [
        '.sc-hfCsLp.hNfILY',  # Main container for tags section
        '//div[contains(@class, "sc-hfCsLp") and contains(@class, "hNfILY")]',  # XPath equivalent
        '.sc-hfCsLp',  # Fallback: broader tag container
        '//div[contains(@class, "sc-hfCsLp")]'  # XPath fallback
    ]
    
    # Individual tag link selector
    TAG_LINK_SELECTOR: str = 'a.sc-hZpmlk.kpuQUO'
    # Model card selectors (CSS) - ordered by priority
    MODEL_CARD_SELECTORS: List[str] = [
        'div.sc-lkCrJH:nth-child(1)',
        '.sc-chzmIZ > div:nth-child(1)'
    ]

    # Optional action button to reveal model card (click before scraping)
    MODEL_CARD_ACTION_BUTTON: str = '.sc-kHBIib > span:nth-child(2)'
    
    # Fallback CSS selector for description (used with Selenium)
    DESCRIPTION_CSS_FALLBACK: str = '.sc-fhfEft > p:nth-child(2)'

class NvidiaSelectors:
    """Configuration class for Nvidia scraping selectors (placeholder for future use)"""
    
    # Add Nvidia-specific selectors here if needed
    pass

class GeneralSelectors:
    """Configuration class for general scraping selectors"""
    
    # Common patterns for numeric values that might represent downloads
    NUMERIC_PATTERNS: List[str] = [
        r'\d+[KkMm]?',  # Numbers with optional K/M suffix
        r'\d+[\.\,]\d+[KkMm]?',  # Decimal numbers with K/M suffix
    ]
    
    # Common user-agent strings
    USER_AGENTS: List[str] = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
    ]

def get_selectors_for_site(site: str) -> Dict:
    """
    Get selectors configuration for a specific site
    
    Args:
        site: The site name ('kaggle', 'nvidia', etc.)
        
    Returns:
        Dictionary containing selectors for the specified site
    """
    selectors_map = {
        'kaggle': {
            'description': KaggleSelectors.DESCRIPTION_SELECTORS,
            'downloads': KaggleSelectors.DOWNLOAD_SELECTORS,
            'description_css_fallback': KaggleSelectors.DESCRIPTION_CSS_FALLBACK,
            'model_card_selectors': KaggleSelectors.MODEL_CARD_SELECTORS,
            'model_card_action': KaggleSelectors.MODEL_CARD_ACTION_BUTTON,
            'tags': KaggleSelectors.TAG_SELECTORS,
            'tag_links': KaggleSelectors.TAG_LINK_SELECTOR
        },
        'nvidia': {
            # Add Nvidia selectors when needed
        }
    }
    
    return selectors_map.get(site.lower(), {})