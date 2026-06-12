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

### 3. LLM-Guided Browser Automation (browser-use)
- Use `browser-use` when scraping requires rendering complex JavaScript, performing clicks, scrolls, or dealing with multi-step interactive workflows (e.g. checkout, forms).
- Standardize agent tasks clearly and configure appropriate limits to prevent infinite loops.
- Use langchain-compatible model adapters to pass commands to the browser:
  ```python
  from browser_use import Agent
  from langchain_openai import ChatOpenAI

  agent = Agent(
      task="Go to https://terebro-gnb.com and extract site performance elements",
      llm=ChatOpenAI(model="gpt-4o")
  )
  ```

## ⚠️ Common Pitfalls & Anti-patterns
- **Prohibited**: Do not import or use `bs4`, `BeautifulSoup`, or `lxml`.
- **Prohibited**: Do not use `requests` or `urllib.request` for scraping public pages.
- **Error**: Accessing `.text()` directly on a `.css_first()` call without a `None` check (will crash with `AttributeError` if the element is missing).

## 🔄 Verification Checklist
1. All parser imports reference `selectolax.lexbor`.
2. All `css_first` calls are wrapped in conditional checks.
3. Network calls use `curl_cffi` with `impersonate="chrome"`.
4. Run `make test` to verify parser code matches expected fixture data.
