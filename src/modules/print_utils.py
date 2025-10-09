"""Small helpers to avoid dumping very large strings to stdout.

Use maybe_print or save_long_text to control large outputs.
"""
from typing import Optional
import os

def maybe_print(text: str, label: Optional[str] = None, max_chars: int = 1000) -> None:
    """Print a short preview of text. If text is longer than max_chars, print a preview and
    the location where the full text was saved (if saved).

    This avoids accidentally dumping entire HTML pages to stdout.
    """
    if text is None:
        return

    preview = text[:max_chars]
    if label:
        print(f"{label}: {preview!s}{'...' if len(text) > max_chars else ''}")
    else:
        print(f"{preview!s}{'...' if len(text) > max_chars else ''}")

def save_long_text(text: str, filename: str = 'debug_page_source.html', force: bool = False) -> str:
    """Save a long text to a file and return the path. By default, only saves when
    the environment variable SAVE_PAGE_SOURCE is set to '1' or force is True.
    """
    if not force and os.environ.get('SAVE_PAGE_SOURCE', '0') != '1':
        return ''

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)

    return filename
