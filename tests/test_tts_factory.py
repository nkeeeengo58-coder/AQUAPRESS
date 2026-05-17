"""Tests for TTS factory pattern (Phase 11)."""

from unittest import mock

import pytest

from audio.tts_factory import synthesize_narration


class TestSynthesizeNarrationLanguageRouting:
    """Test language routing in TTS factory."""

    def test_synthesize_narration_japanese(self):
        """Test that Japanese routing uses VOICEVOX."""
        with mock.patch("audio.tts_factory.synthesize_voicevox") as mock_voicevox:
            mock_voicevox.return_value = "path/to/narration.wav"

            result = synthesize_narration(
                "これはテストです。",
                language="ja",
                output_path="output/test.wav",
            )

            # Verify VOICEVOX was called
            assert mock_voicevox.called
            assert result == "path/to/narration.wav"

    def test_synthesize_narration_english(self):
        """Test that English routing uses Google Cloud TTS."""
        with mock.patch("audio.tts_factory.synthesize_google_tts") as mock_google:
            mock_google.return_value = "path/to/narration.wav"

            result = synthesize_narration(
                "This is a test.",
                language="en",
                output_path="output/test.wav",
            )

            # Verify Google TTS was called
            assert mock_google.called
            assert result == "path/to/narration.wav"

            # Verify correct parameters
            call_args = mock_google.call_args
            assert call_args[0][0] == "This is a test."
            assert call_args[1]["language_code"] == "en-US"

    def test_synthesize_narration_chinese_unsupported(self):
        """Test that Chinese (unsupported) returns None with warning."""
        result = synthesize_narration(
            "这是一个测试。",
            language="zh",
            output_path="output/test.wav",
        )

        # Should return None for unsupported languages
        assert result is None

    def test_synthesize_narration_thai_unsupported(self):
        """Test that Thai (unsupported) returns None with warning."""
        result = synthesize_narration(
            "นี่คือการทดสอบ",
            language="th",
            output_path="output/test.wav",
        )

        # Should return None for unsupported languages
        assert result is None


class TestSynthesizeNarrationValidation:
    """Test input validation."""

    def test_synthesize_narration_empty_text(self):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="text must not be empty"):
            synthesize_narration("", language="ja")

    def test_synthesize_narration_whitespace_only(self):
        """Test that whitespace-only text raises ValueError."""
        with pytest.raises(ValueError, match="text must not be empty"):
            synthesize_narration("   ", language="ja")

    def test_synthesize_narration_invalid_language(self):
        """Test that invalid language returns None."""
        result = synthesize_narration(
            "Test text",
            language="invalid",
        )

        # Should return None for invalid languages
        assert result is None


class TestSynthesizeNarrationParameters:
    """Test parameter passing to TTS engines."""

    def test_japanese_uses_voicevox_speaker(self):
        """Test that Japanese uses VOICEVOX with correct speaker."""
        with mock.patch("audio.tts_factory.synthesize_voicevox") as mock_voicevox:
            mock_voicevox.return_value = "path/to/narration.wav"

            synthesize_narration(
                "日本語テスト",
                language="ja",
            )

            # Verify VOICEVOX was called with speaker 3
            call_kwargs = mock_voicevox.call_args[1]
            assert call_kwargs["speaker"] == 3

    def test_english_uses_correct_voice_id(self):
        """Test that English uses correct Google TTS voice."""
        with mock.patch("audio.tts_factory.synthesize_google_tts") as mock_google:
            mock_google.return_value = "path/to/narration.wav"

            synthesize_narration(
                "English test",
                language="en",
            )

            # Verify Google TTS was called with correct voice
            call_kwargs = mock_google.call_args[1]
            assert call_kwargs["language_code"] == "en-US"
            assert call_kwargs["voice_id"] == "en-US-Neural2-A"

    def test_output_path_parameter(self):
        """Test that output_path is passed through."""
        with mock.patch("audio.tts_factory.synthesize_voicevox") as mock_voicevox:
            mock_voicevox.return_value = "custom/path/narration.wav"

            result = synthesize_narration(
                "テスト",
                language="ja",
                output_path="custom/path/narration.wav",
            )

            # Verify output path was used
            call_kwargs = mock_voicevox.call_args[1]
            assert call_kwargs["output_path"] == "custom/path/narration.wav"
            assert result == "custom/path/narration.wav"


class TestSynthesizeNarrationErrorHandling:
    """Test error handling in TTS factory."""

    def test_synthesize_narration_engine_error(self):
        """Test handling when TTS engine fails."""
        with mock.patch("audio.tts_factory.synthesize_voicevox") as mock_voicevox:
            mock_voicevox.return_value = None  # Simulate failure

            result = synthesize_narration(
                "テスト",
                language="ja",
            )

            # Should return None when engine fails
            assert result is None

    def test_synthesize_narration_google_failure(self):
        """Test handling when Google TTS fails."""
        with mock.patch("audio.tts_factory.synthesize_google_tts") as mock_google:
            mock_google.return_value = None  # Simulate failure

            result = synthesize_narration(
                "Test",
                language="en",
            )

            # Should return None when engine fails
            assert result is None


class TestSynthesizeNarrationDefaults:
    """Test default behavior."""

    def test_default_language_is_japanese(self):
        """Test that default language is Japanese."""
        with mock.patch("audio.tts_factory.synthesize_voicevox") as mock_voicevox:
            mock_voicevox.return_value = "path/to/narration.wav"

            synthesize_narration("テスト")

            # Should use VOICEVOX (Japanese)
            assert mock_voicevox.called
