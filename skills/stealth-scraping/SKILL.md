---
name: html-parsing-and-stealth-scraping
description: Guidelines for high-performance HTML parsing with Selectolax and bypassing anti-bot systems with curl_cffi.
---

# High-Performance HTML Parsing & Stealth Scraping

## 🛠️ Stack & Config
- **Parser Engine**: `selectolax.lexbor` (`LexborHTMLParser`)
- **HTTP Client**: `curl_cffi` (Chrome TLS/JA3 impersonation)

## 📐 Best Practices & Code Patterns

### 1. High-Performance HTML Parsing (Selectolax)
- **Always** use `LexborHTMLParser` instead of BeautifulSoup/lxml.
- Use CSS selectors with `.css()` (to find multiple elements) and `.css_first()` (to find a single element).
- **Safety Rule**: `css_first()` returns `None` if the element does not exist. Always perform a safety check before calling text/attribute extractors:
  ```python
  from selectolax.lexbor import LexborHTMLParser

  parser = LexborHTMLParser(html_content)
  title_node = parser.css_first("h1.main-title")
  
  # Safe extraction
  title = title_node.text(strip=True) if title_node else ""
  ```
- **Attributes Extraction**: Access attributes safely using the `.attrs` dictionary:
  ```python
  link_node = parser.css_first("a.target-link")
  href = link_node.attrs.get("href", "") if link_node else ""
  ```

### 2. Stealth Network Requests (curl_cffi)
- **Always** use `curl_cffi.requests` instead of standard `requests` or `urllib` to bypass anti-bot protections like Cloudflare.
- Initialize a `Session` with `impersonate="chrome"` to ensure TLS/JA3 fingerprints match a real Chrome browser:
  ```python
  from curl_cffi import requests

  session = requests.Session()
  response = session.get("https://example.com", impersonate="chrome")
  html = response.text
  ```
- Reuse session instances where possible to keep cookies and session state.

### 3. Hybrid Scraping Architecture (Playwright + HTTPX/curl_cffi)
When scraping sites with heavy anti-bot security (Cloudflare, JS-challenges, captcha, signature tokens like Xiaohongshu/Douyin):
*   **Do NOT** route all requests through Playwright/Selenium (this is extremely slow and resource-heavy).
*   **Do NOT** attempt to reverse complex JS signature obfuscation algorithms.
*   **Instead, use the Hybrid Schema**:
    1. Spin up Playwright headless/headful to complete the initial login, bypass the Cloudflare challenge, or fetch cookies.
    2. Extract cookies and session headers from the Playwright context.
    3. Close the browser context or keep it in the background for updates only.
    4. Transfer the session cookies to a fast HTTP client (`curl_cffi.requests` or `httpx` with proxy) to fetch raw JSON/HTML endpoints directly.

#### Code Pattern: Cookie Transfer
```python
import asyncio
from playwright.async_api import async_playwright
from curl_cffi import requests

async def get_session_cookies(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate and solve anti-bot challenge
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        
        # Extract cookies
        playwright_cookies = await context.cookies()
        await browser.close()
        
        # Format cookies for requests/curl_cffi
        return {cookie["name"]: cookie["value"] for cookie in playwright_cookies}

def fetch_data_with_cookies(url: str, cookies: dict):
    # Initialize curl_cffi with Chrome TLS signature
    session = requests.Session()
    session.cookies.update(cookies)
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Fast HTTP call bypasses anti-bot with browser cookies + JA3 TLS fingerprint
    response = session.get(url, headers=headers, impersonate="chrome")
    return response.json() if "json" in response.headers.get("content-type", "") else response.text
```

### 4. LLM-Guided Browser Automation (browser-use)
- Use `browser-use` when scraping requires rendering complex JavaScript, performing clicks, scrolls, or dealing with multi-step interactive workflows (e.g. checkout, forms).
- Standardize agent tasks clearly and configure appropriate limits to prevent infinite loops.

## ⚠️ Common Pitfalls & Anti-patterns
- **Prohibited**: Do not import or use `bs4`, `BeautifulSoup`, or `lxml`.
- **Prohibited**: Do not use `requests` or `urllib.request` for scraping public pages.
- **Error**: Accessing `.text()` directly on a `.css_first()` call without a `None` check (will crash with `AttributeError` if the element is missing).

## 🔄 Verification Checklist
1. All parser imports reference `selectolax.lexbor`.
2. All `css_first` calls are wrapped in conditional checks.
3. Network calls use `curl_cffi` with `impersonate="chrome"`.
4. Run `make test` to verify parser code matches expected fixture data.
