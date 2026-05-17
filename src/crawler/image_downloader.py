"""Image downloader with caching for crawler results."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Optional

import requests

from utils.paths import get_project_root


def _get_cache_dir() -> Path:
    """Get or create image cache directory."""
    cache_dir = get_project_root() / "output" / "cache" / "images"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _extract_extension(url: str, content_type: str | None = None) -> str:
    """Extract file extension from URL or content-type."""
    # Try to extract from URL path
    url_path = url.split("?")[0].lower()  # Remove query params
    if url_path.endswith((".jpg", ".jpeg")):
        return "jpg"
    if url_path.endswith(".png"):
        return "png"
    if url_path.endswith(".gif"):
        return "gif"
    if url_path.endswith(".webp"):
        return "webp"

    # Try to extract from content-type header
    if content_type:
        ct = content_type.lower()
        if "jpeg" in ct or "jpg" in ct:
            return "jpg"
        if "png" in ct:
            return "png"
        if "gif" in ct:
            return "gif"
        if "webp" in ct:
            return "webp"

    # Default to jpg
    return "jpg"


def _generate_cache_filename(url: str) -> str:
    """Generate cache filename from URL hash."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"image_{url_hash}"


def download_image(url: str, max_retries: int = 3, timeout: float = 10.0) -> Optional[str]:
    """
    Download image from URL and cache locally.

    Args:
        url: Image URL to download
        max_retries: Max retry attempts on failure
        timeout: Request timeout in seconds

    Returns:
        Local cache path (relative to project root) if successful, None otherwise
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return None

    cache_dir = _get_cache_dir()
    cache_name = _generate_cache_filename(url)

    # Check if already cached
    for ext in ("jpg", "png", "gif", "webp"):
        cached_path = cache_dir / f"{cache_name}.{ext}"
        if cached_path.exists():
            try:
                return str(cached_path.relative_to(get_project_root()))
            except ValueError:
                # Fallback if relative_to fails (e.g., in tests)
                return str(cached_path)

    # Try to download with retries
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": "AQUA-PRESS/1.0"},
                allow_redirects=True,
            )
            response.raise_for_status()

            # Validate content type
            content_type = response.headers.get("content-type", "")
            if not any(t in content_type.lower() for t in ("image", "jpeg", "png", "gif", "webp")):
                return None

            # Determine extension
            extension = _extract_extension(url, content_type)
            cache_path = cache_dir / f"{cache_name}.{extension}"

            # Save to cache
            with cache_path.open("wb") as f:
                f.write(response.content)

            print(f"[INFO] Downloaded image: {url[:60]}... → {cache_path.name}")
            try:
                return str(cache_path.relative_to(get_project_root()))
            except ValueError:
                # Fallback if relative_to fails (e.g., in tests)
                return str(cache_path)

        except requests.Timeout:
            print(f"[WARN] Image download timeout (attempt {attempt + 1}/{max_retries}): {url[:50]}...")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            continue

        except requests.RequestException as exc:
            print(f"[WARN] Image download failed (attempt {attempt + 1}/{max_retries}): {exc}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue

        except Exception as exc:
            print(f"[WARN] Unexpected error downloading image (attempt {attempt + 1}/{max_retries}): {exc}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue

    return None
