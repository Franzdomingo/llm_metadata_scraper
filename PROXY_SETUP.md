# Proxy Rotation Setup Guide

This guide explains how to enable and configure proxy rotation to avoid IP-based rate limiting and blocking.

## Why Use Proxies?

When scraping large numbers of pages, websites may:
- Rate limit requests from a single IP
- Block your IP after too many requests
- Show different content based on geographic location

Rotating proxies helps avoid these issues by distributing requests across multiple IP addresses.

## Enabling Proxy Rotation

### 1. Edit Settings File

Open `scrapy_project/my_scraper/settings.py` and modify:

```python
# Change this to True
ENABLE_PROXY_ROTATION = True

# Add your proxy URLs here
ROTATING_PROXIES = [
    'http://proxy1.example.com:8080',
    'http://proxy2.example.com:8080',
    'http://username:password@proxy3.example.com:8080',
]
```

### 2. Proxy URL Formats

Proxies can be specified in various formats:

```python
# HTTP proxy without authentication
'http://proxy.example.com:8080'

# HTTP proxy with authentication
'http://username:password@proxy.example.com:8080'

# HTTPS proxy
'https://proxy.example.com:8080'

# SOCKS5 proxy (requires additional setup)
'socks5://proxy.example.com:1080'
```

## Where to Get Proxies

### Free Proxy Lists (Not Recommended for Production)
- https://free-proxy-list.net/
- https://www.proxy-list.download/
- https://www.sslproxies.org/

**Warning:** Free proxies are often:
- Slow and unreliable
- May log your traffic
- Frequently blocked by websites
- Short-lived

### Paid Proxy Services (Recommended)

For reliable scraping, consider paid proxy services:

1. **Bright Data (Luminati)** - https://brightdata.com/
   - Residential and datacenter proxies
   - Pay per GB or port
   - Reliable and fast

2. **Oxylabs** - https://oxylabs.io/
   - Residential, datacenter, and mobile proxies
   - Good for large-scale scraping

3. **ScraperAPI** - https://www.scraperapi.com/
   - Handles proxy rotation automatically
   - Includes CAPTCHA solving

4. **Smartproxy** - https://smartproxy.com/
   - Affordable residential proxies
   - Good for beginners

5. **IPRoyal** - https://iproyal.com/
   - Competitive pricing
   - Residential and datacenter options

## Configuration Examples

### Example 1: Using Free Proxies

```python
ENABLE_PROXY_ROTATION = True
ROTATING_PROXIES = [
    'http://45.76.151.141:8080',
    'http://103.159.46.34:83',
    'http://47.91.45.198:3128',
]
```

### Example 2: Using Bright Data

```python
ENABLE_PROXY_ROTATION = True
ROTATING_PROXIES = [
    'http://username-session-1:password@zproxy.lum-superproxy.io:22225',
    'http://username-session-2:password@zproxy.lum-superproxy.io:22225',
    'http://username-session-3:password@zproxy.lum-superproxy.io:22225',
]
```

### Example 3: Using ScraperAPI

With ScraperAPI, you don't need multiple proxies:

```python
ENABLE_PROXY_ROTATION = True
ROTATING_PROXIES = [
    'http://scraperapi:YOUR_API_KEY@proxy-server.scraperapi.com:8001',
]
```

## How Proxy Rotation Works

The `ProxyRotationMiddleware` uses **round-robin** rotation:
1. Request 1 uses proxy[0]
2. Request 2 uses proxy[1]
3. Request 3 uses proxy[2]
4. Request 4 uses proxy[0] (cycles back)

## Testing Your Proxies

Before running the full scraper, test your proxies:

```python
import requests

proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'http://proxy.example.com:8080',
}

try:
    response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
    print(f"Your IP: {response.json()['origin']}")
except Exception as e:
    print(f"Proxy failed: {e}")
```

## Additional Anti-Detection Measures

The spider now includes several anti-detection features:

1. **Random Delays** - Between 0.5-1.5 seconds between card processing
2. **Randomized Wait Times** - 2.0-3.5 seconds for model card loading
3. **Reduced Concurrency** - Only 4 concurrent requests instead of 8
4. **Auto-throttling** - Automatically slows down if errors occur
5. **User Agent Rotation** - Random user agents for each request

## Troubleshooting

### Proxies Not Working

1. **Check proxy connectivity:**
   ```bash
   curl -x http://proxy.example.com:8080 https://httpbin.org/ip
   ```

2. **Verify authentication:**
   - Ensure username/password are correct
   - Check if proxy uses IP whitelisting instead

3. **Check Scrapy logs:**
   - Look for "Using proxy:" messages
   - Check for connection errors

### Still Getting Blocked?

If you're still experiencing blocking:

1. **Increase delays:**
   ```python
   custom_settings = {
       'DOWNLOAD_DELAY': 2.0,  # Increase from 1.0
       'AUTOTHROTTLE_MAX_DELAY': 20.0,  # Increase from 10.0
   }
   ```

2. **Reduce concurrency:**
   ```python
   'CONCURRENT_REQUESTS': 2,  # Reduce from 4
   ```

3. **Use residential proxies** instead of datacenter proxies

4. **Implement session management** to maintain cookies

## Cost Considerations

Proxy costs vary widely:

- **Free proxies:** $0 (but unreliable)
- **Datacenter proxies:** $1-5 per IP/month
- **Residential proxies:** $5-15 per GB
- **ScraperAPI:** $29/month for 100K requests

For the NVIDIA models scraper (200+ models):
- With datacenter proxies: ~$5-10/month
- With residential proxies: ~$10-20/month
- With ScraperAPI: Free tier may be sufficient

## Best Practices

1. **Start without proxies** - Test if you actually need them
2. **Use the minimum number** - More proxies = higher cost
3. **Monitor proxy health** - Remove slow/dead proxies
4. **Rotate user agents** - Already enabled in this project
5. **Respect robots.txt** - Even with proxies (currently disabled)
6. **Add delays** - Already implemented with random delays
7. **Handle failures gracefully** - Implemented in middleware

## Disabling Proxy Rotation

To disable proxy rotation:

```python
ENABLE_PROXY_ROTATION = False
```

The scraper will work normally without proxies.
