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

    # Usability score selectors - ordered by priority
    # CSS selectors first (for Selenium), then XPath (for lxml)
    # Target: p element containing usability score
    USABILITY_SELECTORS: List[str] = [
        # CSS selector - user-provided selector
        'p.sc-hwddKA:nth-child(5)',
        # Fallback - broader class match
        'p.sc-hwddKA',
        # XPath fallback
        '//p[contains(@class, "sc-hwddKA")]'
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

    # Tags "more" button selectors (for expanding hidden tags)
    TAG_MORE_BUTTON_TEXT_SPAN: str = 'span.eWEDa-d'  # Span containing "X more" text
    TAG_MORE_POPUP_CONTAINER: str = '.eqXpEC'  # Popup container that appears when "more" is clicked
    TAG_POPUP_CHECKBOX_BUTTON: str = 'button[role="checkbox"]'  # Tag buttons within popup
    TAG_POPUP_TEXT_SPAN: str = 'span.bMbEZO'  # Span containing tag text within popup buttons

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
    # NOTE: Authors section is typically div.sc-bBhMX:nth-child(2)
    # Avoid using 'p.sc-gGKoUb.bEqAGC' as fallback - it matches collaborators!
    AUTHORS_SELECTORS: List[str] = [
        # Most specific - target the authors container (2nd sc-bBhMX div)
        'div.sc-bBhMX:nth-child(2) > div:nth-child(2)',
        # Alternative - target p elements ONLY within 2nd sc-bBhMX div
        'div.sc-bBhMX:nth-child(2) p.sc-gGKoUb',
        # Fallback - XPath targeting specifically the 2nd sc-bBhMX section
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
    
    # All tab buttons (to extract all tabs for processing)
    # Target: All tab buttons with role="tab" containing tab names
    # The text is within: <div class="sc-biDvOf cFgyMf">Transformers</div>
    VARIATION_TABS_ALL: str = 'button[role="tab"]'

    # Tab text selector (within each tab button)
    # Target: The div containing the tab name text
    VARIATION_TAB_TEXT: str = 'div.sc-biDvOf'

    # Transformers variation dropdown action selector (click to open the list)
    # Target: The combobox button with aria-label="Select Variation"
    TRANSFORMERS_VARIATION_ACTION: str = 'div[role="combobox"][aria-label="Select Variation"]'

    # Transformers variation list container (the opened dropdown)
    # Target: ul element with role="listbox" that contains all variation options
    TRANSFORMERS_VARIATION_LIST_CONTAINER: str = 'ul[role="listbox"]'

    # Transformers variation list item selector (all list items in the dropdown)
    # Target: li elements with role="option" within the opened listbox
    TRANSFORMERS_VARIATION_LIST_ITEMS: str = 'li[role="option"]'

    # Transformers variation name selector (text within each list item in dropdown)
    # Target: div with class "sc-jaGrhB hYa-DAr" containing the variation name
    TRANSFORMERS_VARIATION_NAME: str = 'div.sc-jaGrhB.hYa-DAr'

    # Transformers variation details selectors (after clicking a variation)
    # These appear after selecting a variation from the dropdown

    # Selected variation name (appears in the selected state)
    TRANSFORMERS_VARIATION_SELECTED_NAME: str = 'div.sc-jaGrhB.hYa-DAr'

    # Version selector (appears after selecting a variation)
    # Target: a element with class "sc-eVqvcJ iRcjJz" containing version info
    TRANSFORMERS_VARIATION_VERSION: str = 'a.sc-eVqvcJ.iRcjJz'

    # Downloads selector (appears after selecting a variation)
    # Target: span element with classes for download count
    # IMPORTANT: This must be the variation-specific downloads, NOT the main model downloads
    # The correct element is: <span class="sc-kCuUfV sc-hoocXy iPCsnU eqfbZr">398</span>
    # within the variation details section only
    TRANSFORMERS_VARIATION_DOWNLOADS: str = '.sc-sphZQ > div:nth-child(2) > p:nth-child(2) > div:nth-child(1) > span:nth-child(1)'

    # License selectors (appears after selecting a variation)
    # License can appear in different formats (link or plain text)
    TRANSFORMERS_VARIATION_LICENSE_SELECTORS: List[str] = [
        'a.sc-bbbBoY.hzCdJV',  # Link format (e.g., "Apache 2.0")
        'p.sc-gGKoUb.bEqAGC',  # Plain text format (e.g., "Gemma")
    ]

    # Model card selector for variation (appears after selecting a variation)
    # Target: div.sc-lkCrJH element containing the model card (Model Overview section)
    # This is the third child div within the variation container
    TRANSFORMERS_VARIATION_MODEL_CARD_SELECTORS: List[str] = [
        'div.sc-lkCrJH:nth-child(3)',  # Third child div containing model card content
    ]

    # Is Finetunable selector for variation (appears after selecting a variation)
    # Target: p element with "Yes" or "No" indicating if the model is finetunable
    # Note: Uses same class as license plain text, need to differentiate by context/position
    TRANSFORMERS_IS_FINETUNABLE_SELECTORS: List[str] = [
        'p.sc-gGKoUb.bEqAGC[style*="margin-top"]',  # With margin-top style
        'p.sc-gGKoUb.bEqAGC',  # Fallback - may match multiple, need to filter
    ]

    # Example Usage selector for variation (appears after selecting a variation)
    # Target: Parent container that holds both the header and content
    # The structure is: parent div.sc-cfYtRh.eiwGaI contains:
    #   - div#example-use (header)
    #   - div.sc-lkCrJH.ghmUBs (actual content) OR p.sc-hwddKA.dIsQKt (no guide message)
    # If it contains "This variation does not have a usage guide yet.", the field should be empty
    TRANSFORMERS_EXAMPLE_USAGE_SELECTORS: List[str] = [
        'div.sc-cfYtRh.eiwGaI',  # Main container with example usage
        'div:has(> div#example-use)',  # Parent div containing example-use
    ]
    
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
    """Configuration class for Nvidia scraping selectors"""

    # Model card selectors on the main page
    # Target: All model cards on the page
    MODEL_CARDS: str = 'a[data-linkbox-overlay="true"]'

    # Model name selector within each card
    # Target: The title attribute containing the model name
    MODEL_NAME_ATTRIBUTE: str = 'title'

    # Model URL selector (href attribute)
    # Target: The href attribute containing the relative URL
    MODEL_URL_ATTRIBUTE: str = 'href'

    # Initial visible tags container
    # Target: div containing the first set of visible tag buttons
    # Example: <div class="flex items-center gap-2 overflow-hidden">
    VISIBLE_TAGS_CONTAINER: str = 'div.flex.items-center.gap-2.overflow-hidden'

    # Individual visible tag buttons/links
    # Target: button elements containing tag links
    # Example: <button class="inline-flex min-w-fit..."><a href="/search?q=tool+calling">tool calling</a></button>
    VISIBLE_TAG_BUTTONS: str = 'button.inline-flex.min-w-fit'

    # Tag link within button (to get tag text)
    TAG_LINK: str = 'a'

    # "More tags" button selector (e.g., "+3" button)
    # Target: button that opens popover with additional tags
    # Example: <button data-testid="nv-popover-trigger" type="button"...>+3</button>
    MORE_TAGS_BUTTON: str = 'button[data-testid="nv-popover-trigger"]'

    # Popover container (appears after clicking more tags button)
    # Target: div containing the additional tags in the popover
    # Example: <div class="flex w-fit max-w-[calc(...)] flex-wrap items-center gap-2...">
    POPOVER_TAGS_CONTAINER: str = 'div.flex.w-fit.max-w-\\[calc\\(var\\(--radix-popover-content-available-width\\)_-_32px\\)\\]'

    # Alternative simpler popover selector
    POPOVER_TAGS_CONTAINER_ALT: str = 'div[class*="flex"][class*="w-fit"][class*="flex-wrap"]'

    # Tag buttons within popover
    # Same structure as visible tags
    POPOVER_TAG_BUTTONS: str = 'button.inline-flex.min-w-fit'

    # Model card content selector (from /modelcard page)
    # Target: div containing the full model card markdown content
    # Example: <div class="prose prose-markdown-compat max-w-[85ch]">...</div>
    MODEL_CARD_CONTENT: str = 'div.prose.prose-markdown-compat'


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
            'usability': KaggleSelectors.USABILITY_SELECTORS,
            'description_css_fallback': KaggleSelectors.DESCRIPTION_CSS_FALLBACK,
            'model_card_selectors': KaggleSelectors.MODEL_CARD_SELECTORS,
            'model_card_action': KaggleSelectors.MODEL_CARD_ACTION_BUTTON,
            'variation_tabs_all': KaggleSelectors.VARIATION_TABS_ALL,
            'variation_tab_text': KaggleSelectors.VARIATION_TAB_TEXT,
            'variation_action': KaggleSelectors.TRANSFORMERS_VARIATION_ACTION,
            'variation_list_container': KaggleSelectors.TRANSFORMERS_VARIATION_LIST_CONTAINER,
            'variation_list_items': KaggleSelectors.TRANSFORMERS_VARIATION_LIST_ITEMS,
            'variation_name': KaggleSelectors.TRANSFORMERS_VARIATION_NAME,
            'variation_selected_name': KaggleSelectors.TRANSFORMERS_VARIATION_SELECTED_NAME,
            'variation_version': KaggleSelectors.TRANSFORMERS_VARIATION_VERSION,
            'variation_downloads': KaggleSelectors.TRANSFORMERS_VARIATION_DOWNLOADS,
            'variation_license': KaggleSelectors.TRANSFORMERS_VARIATION_LICENSE_SELECTORS,
            'variation_model_card': KaggleSelectors.TRANSFORMERS_VARIATION_MODEL_CARD_SELECTORS,
            'is_finetunable': KaggleSelectors.TRANSFORMERS_IS_FINETUNABLE_SELECTORS,
            'example_usage': KaggleSelectors.TRANSFORMERS_EXAMPLE_USAGE_SELECTORS,
            'tags': KaggleSelectors.TAG_SELECTORS,
            'tag_links': KaggleSelectors.TAG_LINK_SELECTOR,
            'tag_more_button_span': KaggleSelectors.TAG_MORE_BUTTON_TEXT_SPAN,
            'tag_more_popup': KaggleSelectors.TAG_MORE_POPUP_CONTAINER,
            'tag_popup_checkbox': KaggleSelectors.TAG_POPUP_CHECKBOX_BUTTON,
            'tag_popup_text_span': KaggleSelectors.TAG_POPUP_TEXT_SPAN,
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
            'model_cards': NvidiaSelectors.MODEL_CARDS,
            'model_name_attr': NvidiaSelectors.MODEL_NAME_ATTRIBUTE,
            'model_url_attr': NvidiaSelectors.MODEL_URL_ATTRIBUTE,
            'visible_tags_container': NvidiaSelectors.VISIBLE_TAGS_CONTAINER,
            'visible_tag_buttons': NvidiaSelectors.VISIBLE_TAG_BUTTONS,
            'tag_link': NvidiaSelectors.TAG_LINK,
            'more_tags_button': NvidiaSelectors.MORE_TAGS_BUTTON,
            'popover_tags_container': NvidiaSelectors.POPOVER_TAGS_CONTAINER,
            'popover_tags_container_alt': NvidiaSelectors.POPOVER_TAGS_CONTAINER_ALT,
            'popover_tag_buttons': NvidiaSelectors.POPOVER_TAG_BUTTONS,
            'model_card_content': NvidiaSelectors.MODEL_CARD_CONTENT,
        }
    }
    
    return selectors_map.get(site, {})
