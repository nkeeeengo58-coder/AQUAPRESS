from __future__ import annotations

import json
from datetime import datetime

import pytest

from crawler import get_crawler_config
from crawler.data_normalizer import normalize_and_deduplicate
from crawler.rss_fetcher import fetch_rss_feeds
from crawler.storage import load_crawler_data, save_crawler_data


def test_crawler_config_loading() -> None:
    config = get_crawler_config()
    assert isinstance(config, dict)
    assert "rss_feeds" in config or "html_sources" in config or config == {}


def test_normalize_and_deduplicate_handles_empty_list() -> None:
    result = normalize_and_deduplicate([], {})
    assert result == []


def test_normalize_and_deduplicate_filters_invalid_categories() -> None:
    items = [
        {
            "title": "Test",
            "url": "http://example.com",
            "category": "invalid",
        },
    ]
    result = normalize_and_deduplicate(items, {})
    assert len(result) == 0


def test_normalize_and_deduplicate_validates_required_fields() -> None:
    items = [
        {
            "title": "Test",
            "description": "Desc",
            "url": "http://example.com/1",
            "category": "news",
        },
        {
            "title": "",
            "url": "http://example.com/2",
            "category": "arrival",
        },
    ]
    result = normalize_and_deduplicate(items, {})
    assert len(result) == 1
    assert result[0]["title"] == "Test"


def test_normalize_and_deduplicate_deduplicates_urls() -> None:
    items = [
        {
            "title": "Title1",
            "url": "http://example.com/same",
            "category": "news",
        },
        {
            "title": "Title2",
            "url": "http://example.com/same",
            "category": "sale",
        },
    ]
    result = normalize_and_deduplicate(items, {"duplicate_ttl_hours": 24})
    assert len(result) == 1


def test_normalize_and_deduplicate_sorts_by_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    items = [
        {
            "title": "News item",
            "url": "http://example.com/news",
            "category": "news",
        },
        {
            "title": "Arrival item",
            "url": "http://example.com/arrival",
            "category": "arrival",
        },
        {
            "title": "Sale item",
            "url": "http://example.com/sale",
            "category": "sale",
        },
    ]
    result = normalize_and_deduplicate(items, {})
    assert result[0]["category"] == "arrival"
    assert result[1]["category"] == "sale"
    assert result[2]["category"] == "news"


def test_save_and_load_crawler_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from pathlib import Path

    from utils import paths

    monkeypatch.setattr(paths, "get_project_root", lambda: tmp_path)

    data = {
        "items": [
            {
                "title": "Test",
                "description": "Desc",
                "url": "http://example.com",
                "category": "news",
            }
        ]
    }
    path = save_crawler_data(data, "2026-05-17")
    assert path.exists()

    loaded = load_crawler_data("2026-05-17")
    assert len(loaded["items"]) == 1
    assert loaded["items"][0]["title"] == "Test"


def test_fetch_rss_feeds_handles_missing_url() -> None:
    configs = [{"name": "Bad Config"}]
    result = fetch_rss_feeds(configs)
    assert result == []
