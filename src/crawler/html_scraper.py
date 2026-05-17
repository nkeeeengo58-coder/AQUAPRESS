from __future__ import annotations

import time
from typing import Any
from urllib import error, request
from urllib.parse import urljoin

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
            selectors = config.get("selectors", {}) or {}

            item_selector = (selectors.get("item") or "").strip()
            title_selector = (selectors.get("title") or "").strip()
            description_selector = (selectors.get("description") or "").strip()
            link_selector = (selectors.get("link") or "").strip()
            image_selector = (selectors.get("image") or "").strip()

            if item_selector:
                elements = soup.select(item_selector)
            else:
                # Backward-compatible mode: if no item selector is provided,
                # keep using title selector entries as item roots.
                elements = soup.select(title_selector or "div.item")

            items = []
            for idx, element in enumerate(elements):
                if item_selector:
                    title = _extract_text(element, title_selector)
                    description = _extract_text(element, description_selector)
                    link = _extract_attr(element, link_selector, "href")
                    image_url = _extract_attr(element, image_selector, "src")
                else:
                    title = _extract_text(element, "") or _extract_text(element, title_selector)
                    description = _extract_text(element, description_selector)
                    if not description:
                        description = _extract_nth_text(soup, description_selector, idx)

                    link = _extract_attr(element, link_selector, "href")
                    if not link:
                        link = _extract_nth_attr(soup, link_selector, "href", idx)

                    image_url = _extract_attr(element, image_selector, "src")
                    if not image_url:
                        image_url = _extract_nth_attr(soup, image_selector, "src", idx)

                item = {
                    "title": title,
                    "description": description[:200],
                    "url": _normalize_url(url, link) or url,
                    "image_url": _normalize_url(url, image_url),
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


def _extract_nth_text(soup: BeautifulSoup, selector: str, idx: int) -> str:
    """Extract text from the Nth global match for selector."""
    if not selector:
        return ""
    matches = soup.select(selector)
    if 0 <= idx < len(matches):
        return matches[idx].get_text(strip=True)
    return ""


def _extract_nth_attr(soup: BeautifulSoup, selector: str, attr: str, idx: int) -> str | None:
    """Extract attribute from the Nth global match for selector."""
    if not selector:
        return None
    matches = soup.select(selector)
    if 0 <= idx < len(matches):
        return matches[idx].get(attr)
    return None


def _normalize_url(base_url: str, raw_url: str | None) -> str | None:
    """Normalize possibly relative URLs using page URL as base."""
    if raw_url is None:
        return None
    value = raw_url.strip()
    if not value:
        return None
    return urljoin(base_url, value)
