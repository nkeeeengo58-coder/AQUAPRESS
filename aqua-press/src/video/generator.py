from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

try:
    from moviepy.editor import (
        AudioFileClip,
        ColorClip,
        CompositeAudioClip,
        CompositeVideoClip,
        ImageClip,
        concatenate_videoclips,
    )
except ImportError:  # moviepy v2 fallback
    from moviepy.audio.AudioClip import CompositeAudioClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.video.VideoClip import ColorClip, ImageClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip, concatenate_videoclips

from audio.bgm import load_bgm_clip
from utils.paths import ensure_output_dirs, resolve_path
from video.captions import create_text_imageclip


def _with_duration(clip, duration: float):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)


def _with_position(clip, position):
    if hasattr(clip, "with_position"):
        return clip.with_position(position)
    return clip.set_position(position)


def _with_audio(clip, audio_clip):
    if hasattr(clip, "with_audio"):
        return clip.with_audio(audio_clip)
    return clip.set_audio(audio_clip)


def _resize_clip(clip, width: int | None = None, height: int | None = None):
    if hasattr(clip, "resized"):
        return clip.resized(width=width, height=height)
    return clip.resize(width=width, height=height)


def load_style(config_path: str = "config/video_style.yaml") -> dict[str, Any]:
    config_file = resolve_path(config_path)
    if not config_file or not config_file.exists():
        raise FileNotFoundError(f"Style config not found: {config_path}")
    with config_file.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_video_data(json_path: str = "input/sample_data/sample_video.json") -> dict[str, Any]:
    data_file = resolve_path(json_path)
    if not data_file or not data_file.exists():
        raise FileNotFoundError(f"Video input json not found: {json_path}")
    with data_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def _placeholder_image_clip(style: dict[str, Any], duration: float) -> ImageClip:
    placeholder = create_text_imageclip(
        text="IMAGE\nNOT FOUND",
        width=style["image_max_width"],
        font_size=max(36, style["font_size_caption"] // 2),
        text_color=style["text_color"],
        bg_opacity=0.25,
    )
    placeholder = _with_duration(placeholder, duration)
    return placeholder


def _build_section_clip(style: dict[str, Any], section: dict[str, Any], duration: float) -> CompositeVideoClip:
    width, height = style["width"], style["height"]
    bg = ColorClip(size=(width, height), color=(0, 0, 0), duration=duration)

    clips = [bg]

    image_path = resolve_path(section.get("image"))
    image_clip = None
    if image_path and image_path.exists():
        try:
            image_clip = (
                ImageClip(str(image_path))
            )
            image_clip = _resize_clip(image_clip, height=style["image_max_height"])
            image_clip = _with_duration(image_clip, duration)
            image_clip = _with_position(image_clip, ("center", 300))
            if image_clip.w > style["image_max_width"]:
                image_clip = _resize_clip(image_clip, width=style["image_max_width"])
        except Exception as exc:  # pragma: no cover
            print(f"[WARN] Failed to load image {image_path}: {exc}")

    if image_clip is None:
        print(f"[WARN] Missing image: {section.get('image')}. Using placeholder.")
        image_clip = _with_position(_placeholder_image_clip(style, duration), ("center", 350))

    caption_clip = create_text_imageclip(
        text=section.get("caption", ""),
        width=style["width"] - 120,
        font_size=style["font_size_caption"],
        text_color=style["text_color"],
        bg_opacity=style["caption_box_opacity"],
    )
    caption_clip = _with_duration(caption_clip, duration)
    caption_clip = _with_position(caption_clip, ("center", height - 520))

    accent = ColorClip(size=(width - 120, 8), color=(220, 20, 60), duration=duration)
    accent = _with_position(accent, (60, 240))

    clips.extend([image_clip, caption_clip, accent])
    return _with_duration(CompositeVideoClip(clips, size=(width, height)), duration)


def _build_hook_clip(style: dict[str, Any], hook_text: str, duration: float) -> CompositeVideoClip:
    width, height = style["width"], style["height"]
    base = ColorClip(size=(width, height), color=(0, 0, 0), duration=duration)
    hook = create_text_imageclip(
        text=hook_text,
        width=width - 120,
        font_size=style["font_size_title"],
        text_color=style["text_color"],
        bg_opacity=0.35,
    )
    hook = _with_duration(hook, duration)
    hook = _with_position(hook, ("center", "center"))
    accent = ColorClip(size=(width - 120, 10), color=(220, 20, 60), duration=duration)
    accent = _with_position(accent, (60, height // 2 - 200))
    return _with_duration(CompositeVideoClip([base, hook, accent], size=(width, height)), duration)


def _section_durations(total_duration: float, count: int) -> list[float]:
    if count <= 0:
        return []
    if count == 3 and total_duration >= 40:
        return [13.0, 15.0, 10.0]

    each = max(1.0, (total_duration - 2.0) / count)
    durations = [each] * count
    durations[-1] = max(1.0, total_duration - 2.0 - sum(durations[:-1]))
    return durations


def _build_audio(video_clip, style: dict[str, Any], video_data: dict[str, Any]):
    audio_layers = []

    narration_path = resolve_path(video_data.get("narration_audio"))
    if narration_path and narration_path.exists():
        try:
            narration_clip = AudioFileClip(str(narration_path))
            narration_clip = _with_duration(narration_clip, video_clip.duration)
            audio_layers.append(narration_clip)
        except Exception as exc:  # pragma: no cover
            print(f"[WARN] Failed to load narration audio: {exc}")
    elif video_data.get("narration_audio"):
        print("[WARN] narration_audio path is set but file not found. Continue without narration.")

    bgm_clip = load_bgm_clip(resolve_path(video_data.get("bgm")), style.get("bgm_volume", 0.15))
    if bgm_clip is not None:
        audio_layers.append(_with_duration(bgm_clip, video_clip.duration))

    if not audio_layers:
        return video_clip

    return _with_audio(video_clip, CompositeAudioClip(audio_layers))


def generate_video(video_data: dict[str, Any], style: dict[str, Any]) -> Path:
    ensure_output_dirs()

    hook_clip = _build_hook_clip(style, video_data.get("hook", "AQUA PRESS"), duration=2.0)

    sections = video_data.get("sections", [])
    section_clips = []
    durations = _section_durations(style["duration_seconds"], len(sections))
    for section, duration in zip(sections, durations):
        section_clips.append(_build_section_clip(style, section, duration))

    final_clip = concatenate_videoclips([hook_clip, *section_clips], method="compose")
    final_clip = _build_audio(final_clip, style, video_data)

    output_path = resolve_path(video_data.get("output", "output/videos/aqua_press_sample.mp4"))
    if output_path is None:
        raise ValueError("Output path could not be resolved.")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    final_clip.write_videofile(
        str(output_path),
        fps=style["fps"],
        codec="libx264",
        audio_codec="aac",
    )
    final_clip.close()

    return output_path
