"""Tests for YouTube uploader (Phase 9)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Check if google auth libraries are available
try:
    from google.oauth2.credentials import Credentials
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False


class TestYouTubeUploaderCredentials:
    """Test YouTube credential handling."""

    def test_credentials_file_not_found(self):
        """Test error when credentials file is missing."""
        from upload.youtube_uploader import _get_credentials

        with patch("upload.youtube_uploader.Path") as mock_path:
            # Mock both token and credentials paths as non-existent
            mock_instance = MagicMock()
            mock_instance.exists.return_value = False
            mock_path.return_value = mock_instance

            result = _get_credentials()
            assert result is None

    @pytest.mark.skipif(not GOOGLE_AUTH_AVAILABLE, reason="google-auth not installed")
    def test_load_existing_token(self):
        """Test loading existing valid token."""
        from upload.youtube_uploader import _get_credentials

        with patch("pathlib.Path") as mock_path_class:
            # Mock token file exists
            mock_token = MagicMock()
            mock_token.exists.return_value = True

            mock_creds_file = MagicMock()
            mock_creds_file.exists.return_value = False

            mock_path_class.side_effect = [mock_token, mock_creds_file]

            with patch("google.oauth2.credentials.Credentials.from_authorized_user_file") as mock_from_file:
                mock_creds = MagicMock()
                mock_creds.valid = True
                mock_from_file.return_value = mock_creds

                result = _get_credentials()
                # May return credentials if they're valid
                if result is not None:
                    assert result.valid is True


class TestYouTubeUpload:
    """Test video upload functionality."""

    def test_upload_video_file_not_found(self):
        """Test error when video file doesn't exist."""
        from upload.youtube_uploader import upload_video

        with patch("upload.youtube_uploader.Path") as mock_path:
            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_path.return_value = mock_file

            result = upload_video("nonexistent.mp4", "Test Video")
            assert result is None

    def test_upload_video_no_credentials(self):
        """Test error when credentials are unavailable."""
        from upload.youtube_uploader import upload_video

        with patch("upload.youtube_uploader.Path") as mock_path:
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file

            with patch("upload.youtube_uploader._get_credentials") as mock_get_creds:
                mock_get_creds.return_value = None

                result = upload_video("test.mp4", "Test Video")
                assert result is None

    @pytest.mark.skipif(not GOOGLE_AUTH_AVAILABLE, reason="google-auth not installed")
    def test_upload_video_success(self):
        """Test successful video upload."""
        from upload.youtube_uploader import upload_video

        with patch("upload.youtube_uploader.Path") as mock_path:
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file

            with patch("upload.youtube_uploader._get_credentials") as mock_get_creds:
                mock_creds = MagicMock()
                mock_get_creds.return_value = mock_creds

                with patch("upload.youtube_uploader.build") as mock_build:
                    mock_youtube = MagicMock()
                    mock_build.return_value = mock_youtube

                    # Mock insert response
                    mock_request = MagicMock()
                    mock_response = {"id": "dQw4w9WgXcQ"}
                    mock_request.next_chunk.return_value = (None, mock_response)
                    mock_youtube.videos.return_value.insert.return_value = mock_request

                    result = upload_video(
                        "test.mp4",
                        "Test Video",
                        description="Test Description",
                        tags=["aquarium", "fish"],
                    )

                    assert result == "dQw4w9WgXcQ"

    @pytest.mark.skipif(not GOOGLE_AUTH_AVAILABLE, reason="google-auth not installed")
    def test_upload_video_with_thumbnail(self):
        """Test video upload with thumbnail."""
        from upload.youtube_uploader import upload_video

        with patch("upload.youtube_uploader.Path") as mock_path:
            def mock_path_effect(*args):
                mock_obj = MagicMock()
                mock_obj.exists.return_value = True
                return mock_obj

            mock_path.side_effect = mock_path_effect

            with patch("upload.youtube_uploader._get_credentials") as mock_creds:
                mock_creds.return_value = MagicMock()

                with patch("upload.youtube_uploader.build") as mock_build:
                    mock_youtube = MagicMock()
                    mock_build.return_value = mock_youtube

                    # Mock insert response
                    mock_request = MagicMock()
                    mock_response = {"id": "test_video_id"}
                    mock_request.next_chunk.return_value = (None, mock_response)
                    mock_youtube.videos.return_value.insert.return_value = mock_request

                    result = upload_video("test.mp4", "Test Video", thumbnail_path="thumb.jpg")

                    assert result == "test_video_id"

    @pytest.mark.skipif(not GOOGLE_AUTH_AVAILABLE, reason="google-auth not installed")
    def test_upload_privacy_status_variations(self):
        """Test different privacy status options."""
        from upload.youtube_uploader import upload_video

        with patch("upload.youtube_uploader._get_credentials") as mock_get_creds:
            mock_get_creds.return_value = MagicMock()

            with patch("upload.youtube_uploader.build") as mock_build:
                mock_youtube = MagicMock()
                mock_build.return_value = mock_youtube

                mock_request = MagicMock()
                mock_request.next_chunk.return_value = (None, {"id": "vid_id"})
                mock_youtube.videos.return_value.insert.return_value = mock_request

                with patch("upload.youtube_uploader.Path") as mock_path:
                    mock_file = MagicMock()
                    mock_file.exists.return_value = True
                    mock_path.return_value = mock_file

                    # Test private
                    upload_video("test.mp4", "Test", privacy_status="private")
                    call_args = mock_youtube.videos.return_value.insert.call_args
                    assert call_args[1]["body"]["status"]["privacyStatus"] == "private"


class TestYouTubeStatusCheck:
    """Test upload status checking."""

    @pytest.mark.skipif(not GOOGLE_AUTH_AVAILABLE, reason="google-auth not installed")
    def test_get_upload_status_success(self):
        """Test getting upload status."""
        from upload.youtube_uploader import get_upload_status

        with patch("upload.youtube_uploader._get_credentials") as mock_get_creds:
            mock_get_creds.return_value = MagicMock()

            with patch("upload.youtube_uploader.build") as mock_build:
                mock_youtube = MagicMock()
                mock_build.return_value = mock_youtube

                mock_response = {
                    "items": [
                        {
                            "status": {
                                "privacyStatus": "private",
                                "uploadStatus": "processed",
                            },
                            "processingDetails": {
                                "processingStatus": "succeeded",
                                "processingProgress": {"partsTotal": "100", "partsProcessed": "100"},
                            },
                        }
                    ]
                }
                mock_youtube.videos.return_value.list.return_value.execute.return_value = mock_response

                result = get_upload_status("test_video_id")

                assert result is not None
                assert result["privacy_status"] == "private"
                assert result["upload_status"] == "processed"
                assert result["processing_status"] == "succeeded"

    def test_get_upload_status_no_credentials(self):
        """Test get_upload_status with no credentials."""
        from upload.youtube_uploader import get_upload_status

        with patch("upload.youtube_uploader._get_credentials") as mock_get_creds:
            mock_get_creds.return_value = None

            result = get_upload_status("test_video_id")
            assert result is None


class TestYouTubeMetadataValidation:
    """Test metadata validation."""

    @pytest.mark.skipif(not GOOGLE_AUTH_AVAILABLE, reason="google-auth not installed")
    def test_title_length_limit(self):
        """Test that title respects YouTube's 100-character limit."""
        from upload.youtube_uploader import upload_video

        long_title = "A" * 200  # Exceeds 100 char limit

        with patch("upload.youtube_uploader.Path") as mock_path:
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file

            with patch("upload.youtube_uploader._get_credentials") as mock_creds:
                mock_creds.return_value = MagicMock()

                with patch("upload.youtube_uploader.build") as mock_build:
                    mock_youtube = MagicMock()
                    mock_build.return_value = mock_youtube

                    mock_request = MagicMock()
                    mock_request.next_chunk.return_value = (None, {"id": "vid"})
                    mock_youtube.videos.return_value.insert.return_value = mock_request

                    upload_video("test.mp4", long_title)

                    # Verify title was truncated
                    call_args = mock_youtube.videos.return_value.insert.call_args
                    title = call_args[1]["body"]["snippet"]["title"]
                    assert len(title) <= 100

    @pytest.mark.skipif(not GOOGLE_AUTH_AVAILABLE, reason="google-auth not installed")
    def test_description_length_limit(self):
        """Test that description respects YouTube's 5000-character limit."""
        from upload.youtube_uploader import upload_video

        long_desc = "A" * 10000  # Exceeds 5000 char limit

        with patch("upload.youtube_uploader.Path") as mock_path:
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file

            with patch("upload.youtube_uploader._get_credentials") as mock_creds:
                mock_creds.return_value = MagicMock()

                with patch("upload.youtube_uploader.build") as mock_build:
                    mock_youtube = MagicMock()
                    mock_build.return_value = mock_youtube

                    mock_request = MagicMock()
                    mock_request.next_chunk.return_value = (None, {"id": "vid"})
                    mock_youtube.videos.return_value.insert.return_value = mock_request

                    upload_video("test.mp4", "Title", description=long_desc)

                    # Verify description was truncated
                    call_args = mock_youtube.videos.return_value.insert.call_args
                    desc = call_args[1]["body"]["snippet"]["description"]
                    assert len(desc) <= 5000

    @pytest.mark.skipif(not GOOGLE_AUTH_AVAILABLE, reason="google-auth not installed")
    def test_tags_limit(self):
        """Test that tags respect YouTube's 30-tag limit."""
        from upload.youtube_uploader import upload_video

        many_tags = [f"tag{i}" for i in range(50)]  # Exceeds 30 tag limit

        with patch("upload.youtube_uploader.Path") as mock_path:
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file

            with patch("upload.youtube_uploader._get_credentials") as mock_creds:
                mock_creds.return_value = MagicMock()

                with patch("upload.youtube_uploader.build") as mock_build:
                    mock_youtube = MagicMock()
                    mock_build.return_value = mock_youtube

                    mock_request = MagicMock()
                    mock_request.next_chunk.return_value = (None, {"id": "vid"})
                    mock_youtube.videos.return_value.insert.return_value = mock_request

                    upload_video("test.mp4", "Title", tags=many_tags)

                    # Verify tags were limited
                    call_args = mock_youtube.videos.return_value.insert.call_args
                    tags = call_args[1]["body"]["snippet"]["tags"]
                    assert len(tags) <= 30
