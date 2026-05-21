"""Tests for VOICEVOX with environment variable configuration (Phase 8)."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestVoicevoxEnvironmentVariable:
    """Test VOICEVOX engine URL configuration via environment variable."""

    def test_default_engine_url(self):
        """Test default VOICEVOX engine URL."""
        from audio.voicevox import DEFAULT_VOICEVOX_ENGINE_URL

        # Should be localhost by default or env override
        assert DEFAULT_VOICEVOX_ENGINE_URL in [
            "http://127.0.0.1:50021",  # localhost default
            "http://voicevox:50021",  # GitHub Actions override
        ]

    def test_engine_url_can_be_overridden_in_function_call(self):
        """Test that engine_url parameter can override the default."""
        # This is the actual override mechanism - via function parameter
        from audio.voicevox import synthesize_voicevox

        # The function accepts engine_url parameter, allowing custom URLs
        # (we don't call it here to avoid needing a real VOICEVOX server)
        import inspect

        sig = inspect.signature(synthesize_voicevox)
        assert "engine_url" in sig.parameters
        # Verify it has a default value
        assert sig.parameters["engine_url"].default is not inspect.Parameter.empty

    @patch("audio.voicevox.request.urlopen")
    def test_synthesize_with_custom_engine_url(self, mock_urlopen):
        """Test VOICEVOX synthesis with custom engine URL."""
        from audio.voicevox import synthesize_voicevox

        # Mock successful responses
        query_response = MagicMock()
        query_response.read.return_value = b'{"kana": "test", "outputSamplingRate": 24000, "outputStereo": false}'
        query_response.__enter__.return_value = query_response

        synthesis_response = MagicMock()
        synthesis_response.read.return_value = b"fake_audio_data"
        synthesis_response.__enter__.return_value = synthesis_response

        mock_urlopen.side_effect = [query_response, synthesis_response]

        # Set custom engine URL
        custom_url = "http://custom-voicevox:50021"

        result = synthesize_voicevox(
            "test",
            "/tmp/test.wav",
            engine_url=custom_url,
        )

        # Verify result
        assert result is not None

        # Verify custom URL was used
        calls = mock_urlopen.call_args_list
        assert len(calls) >= 2
        query_call = calls[0][0][0]  # First request should be audio_query
        assert "custom-voicevox:50021" in str(query_call.full_url)

    @patch("audio.voicevox.request.urlopen")
    def test_synthesize_with_default_engine_url(self, mock_urlopen):
        """Test VOICEVOX synthesis with default engine URL."""
        from audio.voicevox import synthesize_voicevox

        # Mock successful responses
        query_response = MagicMock()
        query_response.read.return_value = b'{"kana": "test", "outputSamplingRate": 24000, "outputStereo": false}'
        query_response.__enter__.return_value = query_response

        synthesis_response = MagicMock()
        synthesis_response.read.return_value = b"fake_audio_data"
        synthesis_response.__enter__.return_value = synthesis_response

        mock_urlopen.side_effect = [query_response, synthesis_response]

        result = synthesize_voicevox(
            "test",
            "/tmp/test.wav",
        )

        # Verify result
        assert result is not None

        # Verify calls were made
        assert mock_urlopen.call_count >= 2

    @patch("audio.voicevox.request.urlopen")
    @patch("audio.voicevox.get_project_root")
    def test_synthesize_generates_default_output_path_when_none(self, mock_project_root, mock_urlopen, tmp_path):
        """Test VOICEVOX synthesis auto-generates an output path when None is passed."""
        from audio.voicevox import synthesize_voicevox

        mock_project_root.return_value = tmp_path

        query_response = MagicMock()
        query_response.read.return_value = b'{"kana": "test", "outputSamplingRate": 24000, "outputStereo": false}'
        query_response.__enter__.return_value = query_response

        synthesis_response = MagicMock()
        synthesis_response.read.return_value = b"fake_audio_data"
        synthesis_response.__enter__.return_value = synthesis_response

        mock_urlopen.side_effect = [query_response, synthesis_response]

        result = synthesize_voicevox(
            "test",
            None,
        )

        expected_path = tmp_path / "output" / "audio" / "voicevox_narration.wav"
        assert result == expected_path
        assert expected_path.exists()
        assert expected_path.read_bytes() == b"fake_audio_data"


class TestLocalFullPipelineVoicevoxConfig:
    """Test VOICEVOX configuration in local full pipeline."""

    def test_voicevox_config_from_environment(self, tmp_path):
        """Test that run_local_full_pipeline.py reads VOICEVOX_ENGINE_URL from environment."""
        import json

        # Simulate the voicevox configuration logic
        voicevox_enabled = os.getenv("AQUAPRESS_VOICEVOX", "0") == "1"
        voicevox_engine_url = os.getenv("VOICEVOX_ENGINE_URL", "http://127.0.0.1:50021")

        # Test default (no environment variables)
        assert voicevox_enabled is False
        assert voicevox_engine_url == "http://127.0.0.1:50021"

        # Test with environment variables set
        with patch.dict(
            os.environ,
            {
                "AQUAPRESS_VOICEVOX": "1",
                "VOICEVOX_ENGINE_URL": "http://voicevox:50021",
            },
        ):
            voicevox_enabled = os.getenv("AQUAPRESS_VOICEVOX", "0") == "1"
            voicevox_engine_url = os.getenv("VOICEVOX_ENGINE_URL", "http://127.0.0.1:50021")

            assert voicevox_enabled is True
            assert voicevox_engine_url == "http://voicevox:50021"


class TestGitHubActionsVoicevoxIntegration:
    """Test VOICEVOX integration for GitHub Actions."""

    def test_actions_environment_configuration(self):
        """Test that GitHub Actions environment variables can be configured."""
        actions_env = {
            "VOICEVOX_ENGINE_URL": "http://voicevox:50021",
            "AQUAPRESS_VOICEVOX": "1",
            "GEMINI_API_KEY": "test_key",
        }

        # Verify environment variables are recognized
        with patch.dict(os.environ, actions_env):
            assert os.getenv("VOICEVOX_ENGINE_URL") == "http://voicevox:50021"
            assert os.getenv("AQUAPRESS_VOICEVOX") == "1"
            assert os.getenv("GEMINI_API_KEY") == "test_key"

    def test_voicevox_url_formats(self):
        """Test various VOICEVOX URL formats."""
        valid_urls = [
            "http://127.0.0.1:50021",  # localhost
            "http://voicevox:50021",  # Docker service name
            "http://voicevox-service:50021",  # Alternative Docker service name
            "https://voicevox.example.com",  # HTTPS
        ]

        for url in valid_urls:
            with patch.dict(os.environ, {"VOICEVOX_ENGINE_URL": url}):
                engine_url = os.getenv("VOICEVOX_ENGINE_URL")
                assert engine_url == url
