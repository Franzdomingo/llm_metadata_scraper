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
    # CSS selectors first (for Selenium), then XPath (for lxml)
    # Updated 2025-10-13: Precise selectors targeting downloads section
    # Target: span element containing download count (NOT views)
    # NOTE: Excludes Engagement/Views section
    DOWNLOAD_SELECTORS: List[str] = [
        # CSS selectors (try these first with Selenium for dynamic content)
        # Most specific - user-provided selectors that correctly target downloads
        '.sc-jTpuXY > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)',
        'div.sc-gUYSAC:nth-child(2) > div:nth-child(2) > div:nth-child(2) > span:nth-child(1)',
        # Original selectors (fallback)
        'span.sc-kCuUfV.sc-hoocXy.iPCsnU.eqfbZr',  # Index [388]: '430' - exact match
        'span.sc-hoocXy.eqfbZr',  # Downloads-specific classes (excludes Engagement)
        '.sc-jTpuXY > div:nth-child(1) > div:nth-child(2) > div:nth-child(1)',
        # Fallback with class filtering
        'span.iPCsnU.eqfbZr',  # Partial class match - still excludes Engagement
        # XPath selectors (fallback for lxml parsing)
        '//span[contains(@class, "sc-kCuUfV") and contains(@class, "sc-hoocXy") and contains(@class, "iPCsnU") and contains(@class, "eqfbZr")]',
        '//span[contains(@class, "sc-hoocXy") and contains(@class, "eqfbZr")]',
        '//span[contains(@class, "iPCsnU") and contains(@class, "eqfbZr")]'
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

    # Collaborators action button (to expand/collapse the section if needed)
    COLLABORATORS_ACTION_BUTTON: str = 'div.sc-bBhMX:nth-child(1) > div:nth-child(1) > button:nth-child(2)'

    # Collaborators selectors - ordered by priority
    # Target: p elements with margin-left style containing collaborator names
    COLLABORATORS_SELECTORS: List[str] = [
        # Most specific - target p elements within each collaborator div
        'p.sc-gGKoUb.bEqAGC',
        # Alternative - target p elements with margin-left style
        'p[style*="margin-left"]',
        # Fallback - find all p elements within the collaborators container
        '.sc-cFFDlC p',
        # XPath fallback
        '//div[contains(@class, "sc-cFFDlC")]//p[contains(@class, "sc-gGKoUb")]'
    ]

    # Authors action button (to expand the authors section)
    AUTHORS_ACTION_BUTTON: str = 'div.sc-bBhMX:nth-child(2) > div:nth-child(1) > button:nth-child(2)'

    # Authors selectors - ordered by priority
    # Target: p element containing authors/contributors information
    AUTHORS_SELECTORS: List[str] = [
        # Most specific - target the authors container
        'div.sc-bBhMX:nth-child(2) > div:nth-child(2)',
        # Alternative - target p elements with authors class
        'p.sc-gGKoUb.bEqAGC',
        # Fallback - XPath
        '//div[contains(@class, "sc-bBhMX")][2]//p[contains(@class, "sc-gGKoUb")]'
    ]

    # Provenance action button (to expand the provenance section)
    PROVENANCE_ACTION_BUTTON: str = 'div.sc-bBhMX:nth-child(4) > div:nth-child(1) > button:nth-child(2)'

    # Provenance selectors - ordered by priority
    # Target: div containing provenance updates, sources, and citations
    PROVENANCE_SELECTORS: List[str] = [
        # Most specific - target the provenance container
        '.sc-fPzfn',
        'div.sc-cFFDlC.sc-fPzfn.esaBZM.hMDRMp',
        # Fallback - XPath
        '//div[contains(@class, "sc-fPzfn")]'
    ]

    # Model card selectors (CSS) - ordered by priority
    MODEL_CARD_SELECTORS: List[str] = [
        'div.sc-lkCrJH:nth-child(1)',
        '.sc-chzmIZ > div:nth-child(1)'
    ]

    # Optional action button to reveal model card (click before scraping)
    MODEL_CARD_ACTION_BUTTON: str = '.sc-kHBIib > span:nth-child(2)'
    
    # Transformers variation dropdown action selector (click to open the list)
    TRANSFORMERS_VARIATION_ACTION: str = '.MuiSelect-iconOutlined'
    
    # Transformers variation list item selector (the specific list item text to capture)
    TRANSFORMERS_VARIATION_ITEM: str = 'li.MuiButtonBase-root:nth-child(1) > div:nth-child(1) > p:nth-child(1)'
    
    # Fallback CSS selector for description (used with Selenium)
    DESCRIPTION_CSS_FALLBACK: str = '.sc-fhfEft > p:nth-child(2)'
    
    # Model links XPath
    MODEL_LINKS_XPATH: str = '//ul/li/div/a[contains(@href, "/models/")]'
    
    # Model name XPath (within link element)
    MODEL_NAME_XPATH: str = './/div/div[2]/div/text()'
    
    # Next button XPath
    NEXT_BUTTON_XPATH: str = '//button[.//svg[@data-testid="NavigateNextIcon"]]'
    
    # Alternative next button XPath
    NEXT_BUTTON_ALT_XPATH: str = '//nav//button[contains(@class, "MuiPaginationItem") and contains(@aria-label, "next")]'


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
            'transformers_variation_action': KaggleSelectors.TRANSFORMERS_VARIATION_ACTION,
            'transformers_variation_item': KaggleSelectors.TRANSFORMERS_VARIATION_ITEM,
            'tags': KaggleSelectors.TAG_SELECTORS,
            'tag_links': KaggleSelectors.TAG_LINK_SELECTOR,
            'collaborators': KaggleSelectors.COLLABORATORS_SELECTORS,
            'collaborators_action': KaggleSelectors.COLLABORATORS_ACTION_BUTTON,
            'authors': KaggleSelectors.AUTHORS_SELECTORS,
            'authors_action': KaggleSelectors.AUTHORS_ACTION_BUTTON,
            'provenance': KaggleSelectors.PROVENANCE_SELECTORS,
            'provenance_action': KaggleSelectors.PROVENANCE_ACTION_BUTTON,
            'model_links_xpath': KaggleSelectors.MODEL_LINKS_XPATH,
            'model_name_xpath': KaggleSelectors.MODEL_NAME_XPATH,
            'next_button_xpath': KaggleSelectors.NEXT_BUTTON_XPATH,
            'next_button_alt_xpath': KaggleSelectors.NEXT_BUTTON_ALT_XPATH,
        },
        'nvidia': {
            # Add Nvidia selectors when needed
        }
    }
    
    return selectors_map.get(site, {})
