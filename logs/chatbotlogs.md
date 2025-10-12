# Chatbot Development Logs

## 2025-10-12: Fixed run_all_spiders to support sequential spider execution (Franz Phillip G. Domingo)

- Fixed critical bug where kaggle_metadata spider failed when running all spiders in sequence
- Replaced CrawlerProcess with CrawlerRunner in run_all_spiders() method to support multiple sequential spiders
- Added Twisted reactor integration using defer.inlineCallbacks for proper async execution
- Implemented automatic input file detection for kaggle_metadata spider (uses most recent kaggle_links output)
- Added intelligent spider dependency handling (kaggle_metadata now automatically receives kaggle_links output)
- Imported CrawlerRunner and Twisted reactor/defer modules to main.py
- Changed from individual process.start() calls to single reactor.run() with sequential crawling
- Fixed "ReactorNotRestartable" error that occurred when trying to run multiple spiders
- Enhanced spider sequencing to properly wait for each spider to complete before starting the next
- Added informative logging to show which input file is being used for dependent spiders

## 2025-10-08: Modularized selector configuration and refactored scraping logic (Franz Phillip G. Domingo)

- Created `selectors_config.py` module to centralize all CSS/XPath selectors used for web scraping
- Added `KaggleSelectors`, `NvidiaSelectors`, and `GeneralSelectors` configuration classes
- Refactored `scrape_kaggle_metadata.py` to use selectors from configuration file
- Extracted selector logic into separate helper functions: `_extract_description()`, `_extract_downloads()`, and `_is_numeric_value()`
- Added randomized user-agent selection from configuration
- Improved code maintainability and made selectors easily configurable
- Added proper author attribution and date stamps to all files

## 2025-10-08: Added tag extraction functionality (Franz Phillip G. Domingo)

- Added tag selectors to `KaggleSelectors` class in `selectors_config.py`:
  - `TAG_SELECTORS`: List containing `.sc-bgMVFw` CSS selector and XPath equivalent
  - `TAG_LINK_SELECTOR`: Specific selector `.sc-bgMVFw > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > a:nth-child(1)`
- Updated `get_selectors_for_site()` to include tag selectors in kaggle configuration
- Modified `scrape_kaggle_metadata.py` to extract tags:
  - Added 'tags' field to metadata dictionary structure
  - Created `_extract_tags()` helper function to handle tag extraction with multiple fallback strategies
  - Updated CSV fieldnames to include 'tags' column
  - Enhanced sample results display to show extracted tags
- Tag extraction supports both CSS and XPath selectors with intelligent fallbacks
- Tags are stored as comma-separated values in the CSV for easy parsing

## 2025-10-08: Fixed import issues and improved path handling (Franz Phillip G. Domingo)

- Fixed ImportError by adding fallback import mechanism for direct script execution
- Enhanced path handling to work from both project root and modules directory
- Added intelligent file discovery for input files with multiple fallback paths
- Improved error messages with detailed path information
- Successfully tested tag extraction functionality with live Kaggle data
- Script now works correctly when run directly from modules directory or project root

## 2025-10-12: Fixed downloads extraction in Scrapy project (Franz Phillip G. Domingo)

- Fixed downloads extraction bug where downloads field was not being populated correctly
- Updated `base_spider.py` extract_downloads() method to accept driver parameter for dynamic content
- Added Selenium-based extraction first (for JavaScript-rendered content) before falling back to XPath
- Enhanced download selectors in `site_selectors.py` with CSS selector equivalents:
  - Added span.iPCsnU, span.iURAhc, and other CSS class selectors
  - Maintained XPath selectors as fallback options
  - Ordered selectors by specificity (most specific first)
- Updated `kaggle_metadata_spider.py` to pass driver to extract_downloads() method
- Added comprehensive fallback logic: if selectors fail, searches all span elements for numeric values
- Added detailed debug logging to track selector matching and element text extraction
- Changed LOG_LEVEL to DEBUG in settings.py for troubleshooting
- Verified old code successfully extracted downloads (419, 17.7K, 287, 70 for test models)
- Downloads should now be correctly extracted from dynamically loaded Kaggle model pages
