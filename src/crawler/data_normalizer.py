from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def normalize_and_deduplicate(items: list[dict[str, Any]], settings: dict) -> list[dict[str, Any]]:
    """Normalize items to unified schema and deduplicate by URL within TTL."""
    ttl_hours = settings.get("duplicate_ttl_hours", 24)
    seen_urls = {}
    normalized = []

    for item in items:
        if not isinstance(item, dict):
            continue

        url = (item.get("url") or "").strip()
        if not url:
            continue

        now = datetime.utcnow()
        if url in seen_urls:
            last_seen = seen_urls[url]
            if (now - last_seen).total_seconds() < ttl_hours * 3600:
                continue

        seen_urls[url] = now

        normalized_item = {
            "title": (item.get("title") or "").strip(),
            "description": (item.get("description") or "").strip(),
            "url": url,
            "image_url": (item.get("image_url") or "").strip() or None,
            "category": (item.get("category") or "news").strip(),
            "date": (item.get("date") or "").strip() or datetime.utcnow().isoformat(),
        }

        if normalized_item["title"] and normalized_item["category"] in ["arrival", "sale", "news"]:
            normalized.append(normalized_item)

    priority_order = {"arrival": 0, "sale": 1, "news": 2}
    normalized.sort(key=lambda x: (priority_order.get(x["category"], 99), x["date"]))

    return normalized
