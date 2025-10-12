"""
Selectors module initialization
"""

from .site_selectors import KaggleSelectors, NvidiaSelectors, GeneralSelectors, get_selectors_for_site

__all__ = ['KaggleSelectors', 'NvidiaSelectors', 'GeneralSelectors', 'get_selectors_for_site']
