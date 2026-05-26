from __future__ import annotations

from pathlib import Path

try:
    from moviepy.editor import AudioFileClip
except ImportError:  # moviepy v2 fallback
    from moviepy.audio.io.AudioFileClip import AudioFileClip


def load_bgm_clip(path: Path | None, volume: float):
    if not path or not path.exists():
        print("[WARN] BGM file is missing. Continue without BGM.")
        return None

    try:
        clip = AudioFileClip(str(path))
        if hasattr(clip, "with_volume_scaled"):
            return clip.with_volume_scaled(volume)
        return clip.volumex(volume)
    except Exception as exc:  # pragma: no cover
        print(f"[WARN] Failed to load BGM: {exc}")
        return None
