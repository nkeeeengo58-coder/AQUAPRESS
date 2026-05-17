from __future__ import annotations

from pathlib import Path

import yaml

from utils.paths import get_project_root


def get_crawler_config() -> dict:
    """Load crawler configuration from YAML file."""
    config_path = get_project_root() / "config" / "crawler_sources.yaml"
    if not config_path.exists():
        print(f"[WARN] Crawler config not found: {config_path}")
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_crawler() -> dict[str, list]:
    """Run all enabled crawler sources and return aggregated results."""
    from crawler.rss_fetcher import fetch_rss_feeds
    from crawler.html_scraper import scrape_html_sources
    from crawler.image_downloader import download_image
    from crawler.data_normalizer import normalize_and_deduplicate

    config = get_crawler_config()
    all_items = []

    rss_feeds = config.get("rss_feeds", [])
    for feed_config in rss_feeds:
        if feed_config.get("enabled", True):
            try:
                items = fetch_rss_feeds([feed_config])
                all_items.extend(items)
            except Exception as exc:
                print(f"[WARN] RSS fetch failed for {feed_config.get('name', 'unknown')}: {exc}")

    html_sources = config.get("html_sources", [])
    for source_config in html_sources:
        if source_config.get("enabled", False):
            try:
                items = scrape_html_sources([source_config])
                all_items.extend(items)
            except Exception as exc:
                print(f"[WARN] HTML scrape failed for {source_config.get('name', 'unknown')}: {exc}")

    # Phase 7: Download images and cache locally (if image_url present)
    image_download_enabled = config.get("crawler_settings", {}).get("download_images", True)
    if image_download_enabled:
        for item in all_items:
            if item.get("image_url"):
                local_path = download_image(item["image_url"])
                if local_path:
                    item["image_path"] = local_path

    normalized = normalize_and_deduplicate(all_items, config.get("crawler_settings", {}))
    return {"items": normalized}
