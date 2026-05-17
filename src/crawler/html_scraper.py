from __future__ import annotations

import time
from typing import Any
from urllib import error, request

from bs4 import BeautifulSoup


def scrape_html_sources(source_configs: list[dict]) -> list[dict[str, Any]]:
    """Scrape HTML sources using CSS selectors with error handling."""
    all_items = []

    for config in source_configs:
        url = config.get("url")
        if not url:
            print(f"[WARN] HTML scraper config missing URL: {config}")
            continue

        items = _scrape_single_source(url, config)
        all_items.extend(items)

    return all_items


def _scrape_single_source(url: str, config: dict) -> list[dict[str, Any]]:
    """Scrape a single HTML source with retries."""
    max_retries = 3
    retry_delay = 1
    timeout = config.get("timeout", 10)

    for attempt in range(max_retries):
        try:
            req = request.Request(url, headers={"User-Agent": "AQUAPRESS Crawler/1.0"})
            with request.urlopen(req, timeout=timeout) as response:
                html = response.read().decode("utf-8", errors="replace")

            soup = BeautifulSoup(html, "html.parser")
            selectors = config.get("selectors", {})

            items = []
            for element in soup.select(selectors.get("title", "div.item")):
                item = {
                    "title": _extract_text(element, selectors.get("title", "")),
                    "description": _extract_text(element, selectors.get("description", ""))[:200],
                    "url": _extract_attr(element, selectors.get("link", ""), "href") or url,
                    "image_url": _extract_attr(element, selectors.get("image", ""), "src"),
                    "category": config.get("category", "news"),
                    "date": None,
                }
                if item["title"]:
                    items.append(item)

            return items[:10]
        except (error.URLError, TimeoutError) as exc:
            wait_time = retry_delay * (2 ** attempt)
            if attempt < max_retries - 1:
                print(f"[WARN] HTML scrape attempt {attempt + 1}/{max_retries} failed for {url}: {exc}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] HTML scrape failed for {url} after {max_retries} attempts: {exc}")
                return []
        except Exception as exc:
            print(f"[ERROR] Unexpected error scraping {url}: {exc}")
            return []

    return []


def _extract_text(element, selector: str) -> str:
    """Extract text content using CSS selector."""
    if not selector:
        return element.get_text(strip=True)
    sub = element.select_one(selector)
    return sub.get_text(strip=True) if sub else ""


def _extract_attr(element, selector: str, attr: str) -> str | None:
    """Extract attribute value using CSS selector."""
    if not selector:
        return element.get(attr)
    sub = element.select_one(selector)
    return sub.get(attr) if sub else None
