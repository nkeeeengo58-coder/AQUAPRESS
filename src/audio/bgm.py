from __future__ import annotations

from pathlib import Path

try:
    from moviepy import AudioFileClip
except ImportError:  # pragma: no cover
    from moviepy.editor import AudioFileClip


def load_bgm_clip(bgm_path: str | None, volume: float = 0.15):
    if not bgm_path:
        return None

    path = Path(bgm_path)
    if not path.exists():
        print(f"[WARN] BGM file not found: {path}")
        return None

    try:
        clip = AudioFileClip(str(path))
        return _call_clip_method(clip, "volumex", volume)
    except Exception as exc:
        print(f"[WARN] Failed to load BGM '{path}': {exc}")
        return None


def _call_clip_method(clip, method_name: str, *args, **kwargs):
    method = getattr(clip, method_name, None)
    if method is not None:
        return method(*args, **kwargs)
    if method_name == "volumex":
        alt = getattr(clip, "with_volume_scaled", None)
        if alt is not None:
            return alt(*args, **kwargs)
    return clip
