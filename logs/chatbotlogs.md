# Chatbot Development Logs

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