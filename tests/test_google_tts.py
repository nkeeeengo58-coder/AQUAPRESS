"""Tests for Google Cloud Text-to-Speech integration (Phase 11)."""

import os
from pathlib import Path
from unittest import mock

import pytest

from audio.google_tts import synthesize_google_tts, get_available_voices


class TestGoogleTTSCredentials:
    """Test Google Cloud credentials handling."""

    @mock.patch("audio.google_tts.texttospeech")
    def test_synthesize_google_tts_requires_credentials(self, mock_tts, tmp_path, monkeypatch):
        """Test that synthesize_google_tts requires GOOGLE_APPLICATION_CREDENTIALS."""
        # Import after mocking
        from audio.google_tts import synthesize_google_tts

        # Remove credentials env var
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

        with pytest.raises(ValueError, match="GOOGLE_APPLICATION_CREDENTIALS"):
            synthesize_google_tts("Hello world", output_path=str(tmp_path / "test.wav"))

    @mock.patch("audio.google_tts.texttospeech")
    def test_synthesize_google_tts_invalid_credentials_path(self, mock_tts, monkeypatch):
        """Test handling of invalid credentials path."""
        from audio.google_tts import synthesize_google_tts

        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/nonexistent/path.json")

        with pytest.raises(ValueError, match="Credentials file not found"):
            synthesize_google_tts("Hello world")


class TestGoogleTTSBasic:
    """Test basic Google TTS synthesis functionality."""

    def test_synthesize_google_tts_requires_text(self, monkeypatch, tmp_path):
        """Test that synthesize_google_tts requires non-empty text."""
        # Set dummy credentials path
        creds_file = tmp_path / "dummy.json"
        creds_file.write_text("{}")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(creds_file))

        # Empty text should raise error
        with pytest.raises(ValueError, match="text must not be empty"):
            synthesize_google_tts("")

    @mock.patch("audio.google_tts.texttospeech")
    def test_synthesize_google_tts_english(self, mock_tts, monkeypatch, tmp_path):
        """Test English text synthesis with mocked Google TTS API."""
        # Set up mock credentials
        creds_file = tmp_path / "dummy.json"
        creds_file.write_text("{}")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(creds_file))

        # Mock the TextToSpeechClient and response
        mock_client = mock.MagicMock()
        mock_tts.TextToSpeechClient.return_value = mock_client

        # Create mock response
        mock_response = mock.MagicMock()
        mock_response.audio_content = b"fake_audio_data"
        mock_client.synthesize_speech.return_value = mock_response

        # Test synthesis
        output_path = str(tmp_path / "test.wav")
        result = synthesize_google_tts(
            "Hello world",
            language_code="en-US",
            voice_id="en-US-Neural2-A",
            output_path=output_path,
        )

        # Verify result
        assert result == output_path
        assert Path(output_path).exists()

        # Verify API was called with correct parameters
        mock_client.synthesize_speech.assert_called_once()

    @mock.patch("audio.google_tts.texttospeech")
    def test_synthesize_google_tts_caching(self, mock_tts, monkeypatch, tmp_path):
        """Test that synthesize_google_tts caches results."""
        # Set up mock credentials
        creds_file = tmp_path / "dummy.json"
        creds_file.write_text("{}")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(creds_file))

        # Mock the API
        mock_client = mock.MagicMock()
        mock_tts.TextToSpeechClient.return_value = mock_client
        mock_response = mock.MagicMock()
        mock_response.audio_content = b"fake_audio"
        mock_client.synthesize_speech.return_value = mock_response

        output_path = str(tmp_path / "test.wav")

        # First call
        result1 = synthesize_google_tts(
            "Hello",
            language_code="en-US",
            output_path=output_path,
        )

        # Reset mock to track second call
        mock_client.reset_mock()
        mock_tts.TextToSpeechClient.reset_mock()

        # Second call with same text
        result2 = synthesize_google_tts(
            "Hello",
            language_code="en-US",
            output_path=output_path,
        )

        # Verify cache hit (API not called again)
        assert result1 == result2
        mock_tts.TextToSpeechClient.assert_not_called()

    @mock.patch("audio.google_tts.texttospeech")
    def test_synthesize_google_tts_api_error(self, mock_tts, monkeypatch, tmp_path):
        """Test error handling when API call fails."""
        # Set up mock credentials
        creds_file = tmp_path / "dummy.json"
        creds_file.write_text("{}")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(creds_file))

        # Mock the API to raise an error
        mock_client = mock.MagicMock()
        mock_tts.TextToSpeechClient.return_value = mock_client
        mock_client.synthesize_speech.side_effect = RuntimeError("API Error")

        output_path = str(tmp_path / "test.wav")
        result = synthesize_google_tts(
            "Hello",
            language_code="en-US",
            output_path=output_path,
        )

        # Verify error handling (returns None)
        assert result is None


class TestGoogleTTSAvailableVoices:
    """Test voice listing functionality."""

    @mock.patch("audio.google_tts.texttospeech")
    def test_get_available_voices_english(self, mock_tts, monkeypatch, tmp_path):
        """Test getting available voices for English."""
        # Set up mock credentials
        creds_file = tmp_path / "dummy.json"
        creds_file.write_text("{}")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(creds_file))

        # Mock the API
        mock_client = mock.MagicMock()
        mock_tts.TextToSpeechClient.return_value = mock_client

        # Create mock voices with proper ssml_gender structure
        mock_gender = mock.MagicMock()
        mock_gender.name = "FEMALE"
        
        mock_voice1 = mock.MagicMock()
        mock_voice1.name = "en-US-Neural2-A"
        mock_voice1.language_codes = ["en-US"]
        mock_voice1.ssml_gender = mock_gender
        mock_voice1.natural_sample_rate_hertz = 24000

        mock_response = mock.MagicMock()
        mock_response.voices = [mock_voice1]
        mock_client.list_voices.return_value = mock_response

        # Get voices
        voices = get_available_voices("en-US")

        # Verify
        assert len(voices) == 1
        assert voices[0]["name"] == "en-US-Neural2-A"
        assert "en-US" in voices[0]["language_codes"]
        assert voices[0]["ssml_gender"] == "FEMALE"

    def test_get_available_voices_requires_credentials(self, monkeypatch):
        """Test that get_available_voices requires credentials."""
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

        with pytest.raises(ValueError, match="GOOGLE_APPLICATION_CREDENTIALS"):
            get_available_voices()


class TestGoogleTTSLanguageCodes:
    """Test different language codes."""

    @mock.patch("audio.google_tts.texttospeech")
    def test_synthesize_chinese(self, mock_tts, monkeypatch, tmp_path):
        """Test Chinese language synthesis."""
        creds_file = tmp_path / "dummy.json"
        creds_file.write_text("{}")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(creds_file))

        mock_client = mock.MagicMock()
        mock_tts.TextToSpeechClient.return_value = mock_client
        mock_response = mock.MagicMock()
        mock_response.audio_content = b"fake_audio"
        mock_client.synthesize_speech.return_value = mock_response

        output_path = str(tmp_path / "test.wav")
        result = synthesize_google_tts(
            "你好",
            language_code="zh-CN",
            output_path=output_path,
        )

        assert result == output_path

    @mock.patch("audio.google_tts.texttospeech")
    def test_synthesize_thai(self, mock_tts, monkeypatch, tmp_path):
        """Test Thai language synthesis."""
        creds_file = tmp_path / "dummy.json"
        creds_file.write_text("{}")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(creds_file))

        mock_client = mock.MagicMock()
        mock_tts.TextToSpeechClient.return_value = mock_client
        mock_response = mock.MagicMock()
        mock_response.audio_content = b"fake_audio"
        mock_client.synthesize_speech.return_value = mock_response

        output_path = str(tmp_path / "test.wav")
        result = synthesize_google_tts(
            "สวัสดี",
            language_code="th-TH",
            output_path=output_path,
        )

        assert result == output_path
