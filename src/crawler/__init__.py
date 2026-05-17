from __future__ import annotations

from pathlib import Path

import yaml

from ai.language_config import get_google_news_queries, get_language_config
from utils.paths import get_project_root


def get_crawler_config() -> dict:
    """Load crawler configuration from YAML file."""
    config_path = get_project_root() / "config" / "crawler_sources.yaml"
    if not config_path.exists():
        print(f"[WARN] Crawler config not found: {config_path}")
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_language_specific_rss_feeds(language: str = "ja") -> list[dict]:
    """Generate RSS feed configs for language-specific Google News queries."""
    queries = get_google_news_queries(language)
    lang_config = get_language_config(language)
    
    feeds = []
    for query in queries:
        # Google News RSS feed format: https://news.google.com/rss/search?q=<query>
        # Language can be specified via parameters, but basic format works
        url = f"https://news.google.com/rss/search?q={query}"
        feeds.append({
            "name": f"Google News - {lang_config.name} - {query}",
            "url": url,
            "category": "news",
            "enabled": True,
            "language": language,
        })
    
    return feeds


def run_crawler(language: str = "ja") -> dict[str, list]:
    """Run all enabled crawler sources and return aggregated results.
    
    Args:
        language: Target language (ja, en, zh, th). Defaults to 'ja'.
    
    Returns:
        Dictionary with 'items' key containing normalized list of articles.
    """
    from crawler.rss_fetcher import fetch_rss_feeds
    from crawler.html_scraper import scrape_html_sources
    from crawler.image_downloader import download_image
    from crawler.data_normalizer import normalize_and_deduplicate

    config = get_crawler_config()
    all_items = []
    
    print(f"[INFO] Running crawler for language: {language}")

    # Use language-specific Google News feeds
    language_rss_feeds = _get_language_specific_rss_feeds(language)
    
    for feed_config in language_rss_feeds:
        if feed_config.get("enabled", True):
            try:
                items = fetch_rss_feeds([feed_config])
                all_items.extend(items)
            except Exception as exc:
                print(f"[WARN] RSS fetch failed for {feed_config.get('name', 'unknown')}: {exc}")

    # Also fetch configured RSS feeds if any
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
