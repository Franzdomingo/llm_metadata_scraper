# NVIDIA Models Spider Usage Guide

## Overview

The NVIDIA Models Spider scrapes model metadata from https://build.nvidia.com/models, extracting:
- Model names
- Model URLs
- Tags (categories/features)
- Model cards (detailed documentation) - **OPTIONAL**

## Running Modes

### Mode 1: Fast Mode (Skip Model Cards) - RECOMMENDED

This mode scrapes **only the model list page** without fetching individual model card pages. This is much faster and can scrape all 200+ models in a few minutes.

```bash
cd scrapy_project
scrapy crawl nvidia_models -a skip_modelcard=True
```

**Advantages:**
- ✅ Much faster (10-20x speed improvement)
- ✅ Less likely to get rate limited or blocked
- ✅ Still captures model names, URLs, and tags
- ✅ Can scrape all models in one run

**What you get:**
- Model name
- NVIDIA URL path
- All visible tags
- Timestamp

**What you DON'T get:**
- Model card HTML content (detailed descriptions, architecture, etc.)

### Mode 2: Full Mode (With Model Cards) - SLOW

This mode fetches the full model card page for each model. This is significantly slower because it makes 2 requests per model (list page + model card page).

```bash
cd scrapy_project
scrapy crawl nvidia_models
```

**Advantages:**
- ✅ Complete data including model card documentation
- ✅ Detailed model information

**Disadvantages:**
- ❌ Much slower (can take 30+ minutes for 200 models)
- ❌ More likely to get rate limited or IP blocked
- ❌ May not complete all models in one run
- ❌ Uses more Selenium driver resources

**What you get:**
- Everything from Fast Mode, PLUS:
- Full model card HTML content

## Performance Comparison

| Mode | Time for 200 models | Risk of blocking | Data completeness |
|------|---------------------|------------------|-------------------|
| Fast Mode (skip_modelcard=True) | ~5-10 minutes | Low | Names, URLs, Tags |
| Full Mode (default) | ~30-60 minutes | High | Names, URLs, Tags, Model Cards |

## Recommended Workflow

### Option A: Two-Phase Scraping (Recommended)

1. **Phase 1: Fast scrape** to get all model names and URLs
   ```bash
   scrapy crawl nvidia_models -a skip_modelcard=True
   ```

2. **Phase 2: Selective model card fetching** (if needed)
   - Review the scraped data
   - Identify which models you need detailed info for
   - Write a separate script to fetch only those model cards

### Option B: Full Scraping with Proxies

If you need all model cards in one run:

1. **Set up proxy rotation** (see PROXY_SETUP.md)
2. **Enable proxies** in settings.py
3. **Run full mode:**
   ```bash
   scrapy crawl nvidia_models
   ```

## Output Files

The spider saves results to:
```
scrapy_project/output/nvidia_models_YYYYMMDD_HHMMSS.json
```

Each item contains:
```json
{
  "name": "Meta Llama 3.1 405B Instruct",
  "nvidia_url": "/meta/llama-3_1-405b-instruct",
  "tags": ["Text Generation", "Chat", "Code", "Reasoning"],
  "model_card": "<div class=\"prose\">...</div>",  // Empty if skip_modelcard=True
  "scraped_on": "2025-10-15T15:30:45.123456"
}
```

## Troubleshooting

### Problem: Only scraped 36-40 models instead of 200+

**Cause:** Running in Full Mode with model card extraction is too slow and may be getting rate limited.

**Solution:** Use Fast Mode instead:
```bash
scrapy crawl nvidia_models -a skip_modelcard=True
```

### Problem: Getting blocked/rate limited

**Symptoms:**
- "Card count dropped from 200 to 46"
- Lots of "Card index N out of range" warnings
- Scraping stops early

**Solutions:**
1. **Use Fast Mode** (skip_modelcard=True)
2. **Enable proxy rotation** (see PROXY_SETUP.md)
3. **Reduce concurrency** in spider settings
4. **Increase delays** between requests

### Problem: Stale element reference errors

**Cause:** DOM elements change while the spider is processing them.

**Solution:** Already handled with retry logic. If errors persist:
- Reduce concurrent requests
- Increase delays between processing cards

### Problem: Model cards are empty even in Full Mode

**Cause:** Different model card formats or pages taking too long to load.

**Solution:**
- Check the logs for "Could not find model card element" warnings
- The spider tries multiple selectors automatically
- Some models may not have model cards

## Advanced Configuration

### Custom Settings in Spider

Edit `nvidia_models_spider.py` to adjust:

```python
custom_settings = {
    'CONCURRENT_REQUESTS': 8,  # Number of parallel requests
    'DOWNLOAD_DELAY': 0.5,     # Delay between requests (seconds)
    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_START_DELAY': 0.5,
    'AUTOTHROTTLE_MAX_DELAY': 5.0,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 4.0,
}
```

**For faster scraping** (more aggressive):
- Increase CONCURRENT_REQUESTS to 12-16
- Decrease DOWNLOAD_DELAY to 0.25
- Higher risk of getting blocked

**For safer scraping** (less aggressive):
- Decrease CONCURRENT_REQUESTS to 2-4
- Increase DOWNLOAD_DELAY to 1.0-2.0
- Lower risk of getting blocked

### Running with Custom Settings

```bash
# Override delay via command line
scrapy crawl nvidia_models -a skip_modelcard=True -s DOWNLOAD_DELAY=0.25

# Override concurrency
scrapy crawl nvidia_models -a skip_modelcard=True -s CONCURRENT_REQUESTS=12
```

## Best Practices

1. **Start with Fast Mode** - Always try skip_modelcard=True first
2. **Monitor the logs** - Watch for rate limiting warnings
3. **Use proxies for Full Mode** - If you need model cards, use proxy rotation
4. **Scrape during off-peak hours** - Less likely to get blocked
5. **Don't run too frequently** - Wait at least 24 hours between full scrapes
6. **Save your data** - Output files are timestamped and won't be overwritten

## Examples

### Example 1: Quick scrape of all models (Fast Mode)
```bash
cd scrapy_project
scrapy crawl nvidia_models -a skip_modelcard=True
# Expected: ~200 models in 5-10 minutes
```

### Example 2: Full scrape with logging
```bash
cd scrapy_project
scrapy crawl nvidia_models -a skip_modelcard=True --loglevel=DEBUG
# Shows detailed debug information
```

### Example 3: Full mode with proxies
```bash
# 1. Edit settings.py and enable proxies
# 2. Run:
cd scrapy_project
scrapy crawl nvidia_models
# Expected: ~200 models in 30-60 minutes (with model cards)
```

### Example 4: Very conservative scraping
```bash
cd scrapy_project
scrapy crawl nvidia_models -a skip_modelcard=True -s CONCURRENT_REQUESTS=2 -s DOWNLOAD_DELAY=2.0
# Much slower but safest
```

## Summary

**For most use cases, use Fast Mode:**
```bash
scrapy crawl nvidia_models -a skip_modelcard=True
```

This will scrape all models quickly and reliably. You can always fetch specific model cards later if needed.
