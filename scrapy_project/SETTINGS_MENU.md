# Settings Menu Guide

## Overview
The interactive settings menu allows you to view, edit, and manage scraper performance settings with built-in validation and safety caps.

## How to Access

### From Main Menu
```bash
python main.py
# Select "Settings Menu" option
```

### Standalone
```bash
cd scrapy_project/my_scraper
python settings_menu.py
```

## Features

### 1. **View System Information**
- Displays CPU core count
- Shows system memory (RAM)
- Helps you understand your hardware capabilities

### 2. **View All Settings**
- Shows all configurable settings
- Displays current values
- Shows limits and recommended ranges
- Warning indicators (⚠) for values outside recommended range

### 3. **Edit a Setting**
- Interactive value editing
- Real-time validation
- Shows warnings for potentially problematic values
- Enforces hard limits to prevent invalid configurations

### 4. **Reset to Defaults**
- Restores all settings to default values
- Removes custom configuration file

### 5. **Save Settings**
- Saves current configuration to `scraper_config.json`
- Persists between sessions

### 6. **Load Settings**
- Loads previously saved configuration
- Automatically loads on startup if config file exists

### 7. **Apply Settings to settings.py**
- Updates the actual `settings.py` file with current values
- Makes settings permanent

### 8. **Auto-Configure (Recommended)**
Three preset configurations based on your system:

#### Conservative (Recommended for most users)
- `CONCURRENT_REQUESTS`: CPU_CORES × 4
- `SELENIUM_POOL_SIZE`: CPU_CORES × 1
- `DOWNLOAD_DELAY`: 0.5s
- **Best for**: Stability, avoiding blocks, learning

#### Balanced (Good performance with safety)
- `CONCURRENT_REQUESTS`: CPU_CORES × 8
- `SELENIUM_POOL_SIZE`: CPU_CORES × 2
- `DOWNLOAD_DELAY`: 0.25s
- **Best for**: Production use, regular scraping

#### Aggressive (Maximum performance, higher risk)
- `CONCURRENT_REQUESTS`: CPU_CORES × 16
- `SELENIUM_POOL_SIZE`: CPU_CORES × 3 (max 24)
- `DOWNLOAD_DELAY`: 0.1s
- **Best for**: One-time large scrapes, fast networks

## Configurable Settings

### Performance Settings

| Setting | Description | Typical Range |
|---------|-------------|---------------|
| `CONCURRENT_REQUESTS` | Max simultaneous requests | 4-256 |
| `CONCURRENT_REQUESTS_PER_DOMAIN` | Max requests per domain | 1-128 |
| `CONCURRENT_REQUESTS_PER_IP` | Max requests per IP | 1-128 |
| `DOWNLOAD_DELAY` | Delay between requests (seconds) | 0.0-10.0 |

### Selenium Settings

| Setting | Description | Typical Range |
|---------|-------------|---------------|
| `SELENIUM_POOL_SIZE` | Number of browser instances | 1-32 |

### AutoThrottle Settings

| Setting | Description | Typical Range |
|---------|-------------|---------------|
| `AUTOTHROTTLE_TARGET_CONCURRENCY` | Target concurrent requests | 1.0-100.0 |
| `AUTOTHROTTLE_START_DELAY` | Initial delay (seconds) | 0.0-10.0 |
| `AUTOTHROTTLE_MAX_DELAY` | Maximum delay (seconds) | 0.5-60.0 |

## Safety Features

### Hard Limits
The settings manager enforces absolute minimum and maximum values to prevent:
- Setting impossibly low/high values
- Configuration that would crash the system
- Invalid data types

### Recommended Ranges
Based on your system's CPU cores and memory:
- **CPU-based recommendations**: Scales settings with available cores
- **Memory-based warnings**: Alerts when Selenium pool may exhaust RAM
- Each driver uses ~150-200MB RAM

### Warnings
The system warns you when:
- Values exceed recommended maximums
- Settings might cause rate limiting/blocking
- Memory usage may be too high
- Configuration seems risky

### Validation Examples

```
Setting SELENIUM_POOL_SIZE to 50 on a 4-core system:

⚠ WARNING: Above recommended maximum of 8
⚠ WARNING: Each driver uses significant memory (~100-200MB).
   High values may exhaust system memory
⚠ 50 drivers may use ~7.5GB RAM (you have 16.0GB total)

Do you want to continue anyway? (y/n):
```

## Configuration File

Settings are saved to: `scrapy_project/my_scraper/scraper_config.json`

Example:
```json
{
  "CONCURRENT_REQUESTS": 64,
  "CONCURRENT_REQUESTS_PER_DOMAIN": 24,
  "SELENIUM_POOL_SIZE": 16,
  "DOWNLOAD_DELAY": 0.25
}
```

## Best Practices

### For Development
1. Use **Conservative** auto-config
2. Increase gradually based on results
3. Monitor system resources

### For Production
1. Start with **Balanced** auto-config
2. Test thoroughly before scaling up
3. Save working configurations
4. Monitor for blocks/errors

### Performance Tuning
1. View system info first
2. Consider your target website's limits
3. Monitor active drivers during runtime
4. Adjust based on actual performance

## Runtime Monitoring

When running spiders, you'll see real-time stats:
```
[15:30:22] INFO: Acquired driver from pool | Active: 8/16 | Available: 8 | Total Processed: 150
```

This shows:
- **Active**: Currently in-use drivers
- **Available**: Free drivers in pool
- **Total Processed**: Cumulative requests

## Troubleshooting

### Settings not applying?
1. Save settings in menu
2. Apply to settings.py
3. Restart spider

### Getting blocked/rate limited?
1. Increase `DOWNLOAD_DELAY`
2. Reduce `CONCURRENT_REQUESTS_PER_DOMAIN`
3. Enable proxy rotation

### System running slow/crashing?
1. Reduce `SELENIUM_POOL_SIZE`
2. Reduce `CONCURRENT_REQUESTS`
3. Use Conservative auto-config

### Memory issues?
- Each Selenium driver uses ~150-200MB RAM
- Calculate: `SELENIUM_POOL_SIZE × 150MB`
- Keep total under 70% of available RAM

## Examples

### Example 1: First Time Setup
```
1. Run: python main.py
2. Select "Settings Menu"
3. Select "Auto-Configure"
4. Choose "Conservative"
5. Save Settings
6. Apply to settings.py
7. Exit and run spider
```

### Example 2: Tuning for Speed
```
1. Open Settings Menu
2. View System Information (note CPU count)
3. Edit CONCURRENT_REQUESTS → 128
4. Edit SELENIUM_POOL_SIZE → 24
5. Edit DOWNLOAD_DELAY → 0.1
6. Review warnings
7. Save if acceptable
```

### Example 3: Fixing Rate Limiting
```
1. Open Settings Menu
2. Edit DOWNLOAD_DELAY → 1.0
3. Edit CONCURRENT_REQUESTS_PER_DOMAIN → 8
4. Save Settings
5. Apply to settings.py
```

## Tips

- **Always save** after making changes
- **Test incrementally** - don't max everything at once
- **Monitor logs** for errors and warnings
- **Respect target sites** - aggressive settings can get you blocked
- **Check memory usage** when increasing Selenium pool
- Use **auto-configure** as a starting point, then tune

## Advanced: Programmatic Access

```python
from my_scraper.settings_manager import SettingsManager

# Create manager
manager = SettingsManager('scraper_config.json')

# Get value
pool_size = manager.get_setting('SELENIUM_POOL_SIZE')

# Set value with validation
manager.set_setting('CONCURRENT_REQUESTS', 128)

# Save
manager.save_config()

# Get all as dict
all_settings = manager.get_settings_dict()
```
