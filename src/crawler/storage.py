from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from utils.paths import get_project_root


def get_crawler_data_dir() -> Path:
    """Get crawler data directory path."""
    data_dir = get_project_root() / "output" / "metadata" / "crawler_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def save_crawler_data(data: dict[str, Any], date_str: str | None = None) -> Path:
    """Save crawler data to JSON file with date prefix."""
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    data_dir = get_crawler_data_dir()
    output_path = data_dir / f"crawler_data_{date_str}.json"

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] Crawler data saved: {output_path}")
    return output_path


def load_crawler_data(date_str: str | None = None) -> dict[str, Any]:
    """Load crawler data from JSON file."""
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    data_dir = get_crawler_data_dir()
    input_path = data_dir / f"crawler_data_{date_str}.json"

    if not input_path.exists():
        print(f"[WARN] Crawler data not found: {input_path}")
        return {"items": []}

    with input_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_crawler_errors(errors: list[str], date_str: str | None = None) -> Path:
    """Save crawler errors to log file."""
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    data_dir = get_crawler_data_dir()
    log_path = data_dir / f"crawler_errors_{date_str}.log"

    with log_path.open("a", encoding="utf-8") as f:
        for error in errors:
            timestamp = datetime.utcnow().isoformat()
            f.write(f"[{timestamp}] {error}\n")

    return log_path


def cleanup_old_crawler_data(retention_days: int = 30) -> int:
    """Remove crawler data files older than retention days."""
    data_dir = get_crawler_data_dir()
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    count = 0

    for file_path in data_dir.glob("crawler_data_*.json"):
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff:
                file_path.unlink()
                count += 1
        except Exception as exc:
            print(f"[WARN] Failed to cleanup {file_path}: {exc}")

    if count > 0:
        print(f"[INFO] Cleaned up {count} old crawler data files")
    return count
