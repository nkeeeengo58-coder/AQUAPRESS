"""TTS factory pattern for language-aware audio synthesis (Phase 11)."""

from __future__ import annotations

from ai.language_config import get_language_config
from audio.google_tts import synthesize_google_tts
from audio.voicevox import synthesize_voicevox


def synthesize_narration(
    text: str,
    language: str = "ja",
    output_path: str | None = None,
    api_key: str | None = None,
) -> str | None:
    """Synthesize narration using language-appropriate TTS engine.

    Automatically routes to the correct TTS engine based on language configuration:
    - Japanese (ja): VOICEVOX
    - English (en): Google Cloud TTS
    - Chinese (zh), Thai (th): Placeholder (returns None with warning)

    Args:
        text: Text to synthesize.
        language: Target language (ja, en, zh, th).
        output_path: Output WAV file path. If None, auto-generated.
        api_key: API key for TTS service (if needed).

    Returns:
        Path to synthesized WAV file, or None if synthesis failed.
    """
    if not text or not text.strip():
        raise ValueError("text must not be empty")

    try:
        lang_config = get_language_config(language)
    except ValueError as exc:
        print(f"[ERROR] Invalid language: {exc}")
        return None

    tts_engine = lang_config.tts_engine

    # Route to appropriate TTS engine
    if tts_engine == "voicevox":
        # Japanese: use VOICEVOX
        print(f"[INFO] Synthesizing narration with VOICEVOX (language: {language})")
        return synthesize_voicevox(
            text,
            output_path=output_path,
            speaker=lang_config.voicevox_speaker,
        )

    elif tts_engine == "google":
        # English, Chinese, Thai: use Google Cloud TTS
        print(f"[INFO] Synthesizing narration with Google Cloud TTS (language: {language})")
        return synthesize_google_tts(
            text,
            language_code=lang_config.tts_language_code,
            voice_id=lang_config.tts_voice_id,
            output_path=output_path,
        )

    else:
        # Unsupported language
        print(f"[WARN] No TTS engine configured for language: {language}")
        print(f"[WARN] Skipping audio synthesis. Video will have no narration.")
        return None
