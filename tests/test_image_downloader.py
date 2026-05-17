"""Tests for image downloader with caching."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from crawler.image_downloader import _extract_extension, _generate_cache_filename, download_image


class TestImageDownloaderExtension:
    """Test file extension extraction."""

    def test_extract_from_url_jpg(self):
        """Test JPG extension extraction from URL."""
        assert _extract_extension("https://example.com/image.jpg") == "jpg"
        assert _extract_extension("https://example.com/image.jpeg") == "jpg"
        assert _extract_extension("https://example.com/image.JPG?v=1") == "jpg"

    def test_extract_from_url_png(self):
        """Test PNG extension extraction from URL."""
        assert _extract_extension("https://example.com/image.png") == "png"
        assert _extract_extension("https://example.com/image.PNG?v=1") == "png"

    def test_extract_from_url_gif(self):
        """Test GIF extension extraction from URL."""
        assert _extract_extension("https://example.com/image.gif") == "gif"

    def test_extract_from_url_webp(self):
        """Test WEBP extension extraction from URL."""
        assert _extract_extension("https://example.com/image.webp") == "webp"

    def test_extract_from_content_type(self):
        """Test extension extraction from content-type header."""
        assert _extract_extension("https://example.com/image", "image/jpeg") == "jpg"
        assert _extract_extension("https://example.com/image", "image/png") == "png"
        assert _extract_extension("https://example.com/image", "image/gif") == "gif"
        assert _extract_extension("https://example.com/image", "image/webp") == "webp"

    def test_extract_fallback_to_jpg(self):
        """Test fallback to jpg when extension cannot be determined."""
        assert _extract_extension("https://example.com/unknown-file") == "jpg"
        assert _extract_extension("https://example.com/image", "text/html") == "jpg"


class TestCacheFilename:
    """Test cache filename generation."""

    def test_generate_cache_filename_deterministic(self):
        """Test that same URL generates same filename."""
        url = "https://example.com/image.jpg"
        name1 = _generate_cache_filename(url)
        name2 = _generate_cache_filename(url)
        assert name1 == name2
        assert name1.startswith("image_")
        assert len(name1.split("_")[1]) == 12  # 12-char hash

    def test_different_urls_different_filenames(self):
        """Test that different URLs generate different filenames."""
        url1 = "https://example.com/image1.jpg"
        url2 = "https://example.com/image2.jpg"
        name1 = _generate_cache_filename(url1)
        name2 = _generate_cache_filename(url2)
        assert name1 != name2


class TestDownloadImage:
    """Test image downloading and caching."""

    def test_download_image_none_url(self):
        """Test download with None URL returns None."""
        assert download_image(None) is None
        assert download_image("") is None
        assert download_image("   ") is None

    def test_download_image_invalid_url(self):
        """Test download with invalid URL returns None."""
        assert download_image("not-a-url") is None
        assert download_image("ftp://example.com/image.jpg") is None

    @patch("crawler.image_downloader.requests.get")
    def test_download_image_success(self, mock_get, tmp_path):
        """Test successful image download and caching."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_response.content = b"fake_image_data"
        mock_get.return_value = mock_response

        with patch("crawler.image_downloader._get_cache_dir", return_value=tmp_path):
            with patch("crawler.image_downloader.get_project_root", return_value=tmp_path):
                result = download_image("https://example.com/image.jpg")
                assert result is not None
                assert "image_" in result
                assert ".jpg" in result

                # Verify file was created
                cache_filename = result.split("/")[-1]
                cache_path = tmp_path / cache_filename
                assert cache_path.exists()
                assert cache_path.read_bytes() == b"fake_image_data"

    @patch("crawler.image_downloader.requests.get")
    def test_download_image_cache_hit(self, mock_get, tmp_path):
        """Test that cached images are not re-downloaded."""
        # Create a fake cached file with correct hash
        url = "https://example.com/image.jpg"
        cache_name = _generate_cache_filename(url)
        cache_file = tmp_path / f"{cache_name}.jpg"
        cache_file.write_bytes(b"cached_data")

        with patch("crawler.image_downloader._get_cache_dir", return_value=tmp_path):
            with patch("crawler.image_downloader.get_project_root", return_value=tmp_path):
                result = download_image(url)
                assert result is not None
                # Verify requests.get was NOT called (cache hit)
                mock_get.assert_not_called()

    @patch("crawler.image_downloader.requests.get")
    def test_download_image_request_exception(self, mock_get):
        """Test handling of request exceptions."""
        mock_get.side_effect = Exception("Connection error")

        result = download_image("https://example.com/image.jpg")
        assert result is None
        # Should have retried 3 times (now with retry logic for all exceptions)
        assert mock_get.call_count == 3

    @patch("crawler.image_downloader.requests.get")
    def test_download_image_timeout_retry(self, mock_get):
        """Test retry behavior on timeout."""
        import requests

        mock_get.side_effect = requests.Timeout("Request timeout")

        result = download_image("https://example.com/image.jpg", max_retries=2, timeout=1.0)
        assert result is None
        # Should have retried 2 times
        assert mock_get.call_count == 2

    @patch("crawler.image_downloader.requests.get")
    def test_download_image_invalid_content_type(self, mock_get):
        """Test rejection of non-image content types."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.content = b"<html>...</html>"
        mock_get.return_value = mock_response

        result = download_image("https://example.com/notimage.html")
        assert result is None


class TestImageDownloaderIntegration:
    """Integration tests for image downloader with crawler."""

    def test_crawler_image_download_integration(self, tmp_path):
        """Test that crawler items with image_url get image_path set after download."""
        from crawler.image_downloader import download_image

        # Simulate crawler items
        items = [
            {
                "title": "Item 1",
                "url": "https://example.com/1",
                "image_url": "https://example.com/image1.jpg",
            },
            {
                "title": "Item 2",
                "url": "https://example.com/2",
                "image_url": "https://example.com/image2.png",
            },
        ]

        with patch("crawler.image_downloader.requests.get") as mock_get:
            # Setup mock responses
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.content = b"image_data"
            mock_get.return_value = mock_response

            with patch("crawler.image_downloader._get_cache_dir", return_value=tmp_path):
                with patch("crawler.image_downloader.get_project_root", return_value=tmp_path):
                    # Simulate crawler image download
                    for item in items:
                        if item.get("image_url"):
                            local_path = download_image(item["image_url"])
                            if local_path:
                                item["image_path"] = local_path

            # Verify image_path is set
            assert items[0].get("image_path") is not None
            assert items[1].get("image_path") is not None
            assert "image_" in items[0]["image_path"]
            assert "image_" in items[1]["image_path"]
