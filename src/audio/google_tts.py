"""Google Cloud Text-to-Speech integration for multi-language support (Phase 11)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None

from utils.paths import get_project_root


def synthesize_google_tts(
    text: str,
    language_code: str = "en-US",
    voice_id: str | None = None,
    output_path: str | None = None,
    speed: float = 1.0,
) -> str | None:
    """Synthesize speech using Google Cloud Text-to-Speech API.

    Args:
        text: Text to synthesize.
        language_code: Language code (e.g., "en-US", "zh-CN", "th-TH").
        voice_id: Voice identifier (e.g., "en-US-Neural2-A").
        output_path: Output WAV file path. If None, cache dir is used.
        speed: Speech speed (0.25 to 4.0).

    Returns:
        Path to generated WAV file, or None if synthesis failed.

    Raises:
        ValueError: If credentials not configured or API call fails.
    """
    if texttospeech is None:
        raise ValueError(
            "google-cloud-texttospeech not installed. "
            "Run: pip install google-cloud-texttospeech"
        )

    if not text or not text.strip():
        raise ValueError("text must not be empty")

    # Validate credentials
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
            "Please configure Google Cloud credentials."
        )

    if not os.path.exists(credentials_path):
        raise ValueError(f"Credentials file not found: {credentials_path}")

    # Generate cache path if not provided
    if not output_path:
        cache_dir = get_project_root() / "output" / "audio" / "google_tts_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Use text hash for deterministic caching
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        safe_voice_id = (voice_id or "default").replace("-", "_")
        output_path = str(cache_dir / f"{language_code}_{safe_voice_id}_{text_hash}.wav")

    # Check cache
    if os.path.exists(output_path):
        print(f"[INFO] Using cached Google TTS: {output_path}")
        return output_path

    try:
        # Initialize client
        client = texttospeech.TextToSpeechClient()

        # Build synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Voice selection
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_id if voice_id else None,
        )

        # Audio config
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=speed,
        )

        # Synthesize
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        # Write audio to file
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with output_path_obj.open("wb") as f:
            f.write(response.audio_content)

        print(f"[INFO] Google TTS synthesis saved: {output_path}")
        return output_path

    except Exception as exc:
        print(f"[ERROR] Google Cloud TTS synthesis failed: {exc}")
        return None


def get_available_voices(language_code: str = "en-US") -> list[dict[str, Any]]:
    """Get available voices for a language.

    Args:
        language_code: Language code (e.g., "en-US").

    Returns:
        List of available voice configurations.

    Raises:
        ValueError: If credentials not configured or API call fails.
    """
    if texttospeech is None:
        raise ValueError("google-cloud-texttospeech not installed")

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path or not os.path.exists(credentials_path):
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

    try:
        client = texttospeech.TextToSpeechClient()
        response = client.list_voices(language_code=language_code)

        voices = []
        for voice in response.voices:
            voices.append(
                {
                    "name": voice.name,
                    "language_codes": list(voice.language_codes),
                    "ssml_gender": voice.ssml_gender.name if voice.ssml_gender else "NEUTRAL",
                    "natural_sample_rate_hertz": voice.natural_sample_rate_hertz,
                }
            )
        return voices

    except Exception as exc:
        print(f"[WARN] Failed to list voices: {exc}")
        return []
