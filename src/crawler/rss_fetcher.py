from __future__ import annotations

import time
from typing import Any
from urllib import error

import feedparser


def fetch_rss_feeds(feed_configs: list[dict]) -> list[dict[str, Any]]:
    """Fetch items from RSS feeds with error handling and retry logic."""
    all_items = []

    for config in feed_configs:
        url = config.get("url")
        if not url:
            print(f"[WARN] RSS config missing URL: {config}")
            continue

        items = _fetch_single_feed(url, config)
        all_items.extend(items)

    return all_items


def _fetch_single_feed(url: str, config: dict) -> list[dict[str, Any]]:
    """Fetch a single RSS feed with retries."""
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            feed = feedparser.parse(url)
            if feed.bozo and feed.bozo_exception:
                print(f"[WARN] RSS parsing error on {url}: {feed.bozo_exception}")

            items = []
            for entry in feed.entries[:10]:
                item = {
                    "title": entry.get("title", "").strip(),
                    "description": entry.get("summary", "").strip()[:200],
                    "url": entry.get("link", "").strip(),
                    "image_url": None,
                    "category": config.get("category", "news"),
                    "date": entry.get("published", "").strip(),
                }
                if item["title"]:
                    items.append(item)

            return items
        except (error.URLError, TimeoutError) as exc:
            wait_time = retry_delay * (2 ** attempt)
            if attempt < max_retries - 1:
                print(f"[WARN] RSS fetch attempt {attempt + 1}/{max_retries} failed for {url}: {exc}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] RSS fetch failed for {url} after {max_retries} attempts: {exc}")
                return []
        except Exception as exc:
            print(f"[ERROR] Unexpected error fetching RSS {url}: {exc}")
            return []

    return []
