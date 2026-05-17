from __future__ import annotations

import os
import json
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw

try:
    from moviepy import AudioFileClip, ColorClip, CompositeAudioClip, ImageClip, concatenate_videoclips
except ImportError:  # pragma: no cover
    from moviepy.editor import AudioFileClip, ColorClip, CompositeAudioClip, ImageClip, concatenate_videoclips

from audio.bgm import load_bgm_clip
from audio.voicevox import DEFAULT_SPEAKER, DEFAULT_VOICEVOX_ENGINE_URL, synthesize_voicevox
from utils.paths import ensure_output_folders, get_project_root, resolve_project_path
from video.captions import _load_font, create_title_card_clip


def load_video_style(style_path: str | Path | None = None) -> dict:
    if style_path is None:
        style_path = get_project_root() / "config" / "video_style.yaml"
    path = Path(style_path)
    if not path.exists():
        print(f"[WARN] style config not found: {path}")
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_sample_data(sample_path: str | Path) -> dict:
    path = Path(sample_path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _with_duration(clip, duration: float):
    method = getattr(clip, "with_duration", None)
    if method is not None:
        return method(duration)
    return clip.set_duration(duration)


def _with_position(clip, position):
    method = getattr(clip, "with_position", None)
    if method is not None:
        return method(position)
    return clip.set_position(position)


def _resized(clip, **kwargs):
    method = getattr(clip, "resized", None)
    if method is not None:
        return method(**kwargs)
    return clip.resize(**kwargs)


def _color_to_rgb(color_name: str) -> tuple[int, int, int]:
    mapping = {
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "red": (200, 20, 20),
    }
    return mapping.get(str(color_name).lower(), (0, 0, 0))


def _build_section_clip(section: dict, style: dict, duration: float):
    width = int(style.get("width", 1080))
    height = int(style.get("height", 1920))
    text_color = style.get("text_color", "white")
    accent_color = style.get("accent_color", "red")
    background_color = style.get("background_color", "black")
    font_size_caption = int(style.get("font_size_caption", 58))
    image_max_width = int(style.get("image_max_width", 900))
    image_max_height = int(style.get("image_max_height", 900))

    canvas = Image.new("RGB", (width, height), _color_to_rgb(background_color))
    draw = ImageDraw.Draw(canvas)

    # Phase 7: Prioritize cached image_path from crawler, then fall back to generated image
    image_path = section.get("image_path") or section.get("image")
    if image_path:
        resolved = resolve_project_path(image_path)
        if resolved.exists():
            try:
                image = Image.open(resolved).convert("RGB")
                image.thumbnail((image_max_width, image_max_height), Image.Resampling.LANCZOS)
                image_x = (width - image.width) // 2
                image_y = int(height * 0.14)
                canvas.paste(image, (image_x, image_y))
            except Exception as exc:
                print(f"[WARN] Failed to load image '{resolved}': {exc}")
        else:
            print(f"[WARN] Image not found: {resolved}")

    accent_rgb = _color_to_rgb(accent_color)
    draw.rectangle([0, int(height * 0.08), width, int(height * 0.086)], fill=accent_rgb)
    draw.rectangle([0, int(height * 0.90), width, int(height * 0.903)], fill=accent_rgb)

    caption_text = section.get("caption", "")
    caption_height = max(180, int(height * 0.22))
    caption_y = height - caption_height - max(40, int(height * 0.06))
    draw.rounded_rectangle(
        [48, caption_y, width - 48, caption_y + caption_height],
        radius=22,
        fill=(20, 20, 20),
    )

    font = _load_font(font_size_caption)
    lines = caption_text.splitlines() if caption_text else [""]
    line_spacing = max(8, int(font_size_caption * 0.22))
    line_heights = [draw.textbbox((0, 0), line or " ", font=font)[3] - draw.textbbox((0, 0), line or " ", font=font)[1] for line in lines]
    block_height = sum(line_heights) + line_spacing * max(0, len(lines) - 1)
    text_y = caption_y + max(16, (caption_height - block_height) // 2)
    for idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line or " ", font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, text_y), line, font=font, fill=text_color)
        text_y += line_heights[idx] + line_spacing

    return _with_duration(ImageClip(np.array(canvas)), duration)


def _build_hook_clip(hook_text: str, style: dict, duration: float):
    width = int(style.get("width", 1080))
    height = int(style.get("height", 1920))
    background_color = style.get("background_color", "black")
    text_color = style.get("text_color", "white")
    accent_color = style.get("accent_color", "red")
    font_size_title = int(style.get("font_size_title", 74))

    title_clip = create_title_card_clip(
        hook_text,
        width=width,
        height=height,
        text_color=text_color,
        accent_color=accent_color,
        font_size=font_size_title,
        duration=duration,
    )
    return title_clip


def generate_video(data: dict, style: dict | None = None) -> Path:
    print("[INFO] Video generation started", flush=True)
    style = style or load_video_style()
    folders = ensure_output_folders()

    width = int(style.get("width", 1080))
    height = int(style.get("height", 1920))
    fps = int(style.get("fps", 30))
    total_duration = float(style.get("duration_seconds", 40))
    bgm_volume = float(style.get("bgm_volume", 0.15))

    sections = data.get("sections", []) or []
    hook_duration = 3.0
    remaining_duration = max(total_duration - hook_duration, 1.0)
    section_duration = remaining_duration / max(len(sections), 1)

    clips = [_with_duration(_build_hook_clip(data.get("hook", data.get("title", "AQUA PRESS")), style, hook_duration), hook_duration)]
    for section in sections:
        clips.append(_with_duration(_build_section_clip(section, style, section_duration), section_duration))

    final_video = concatenate_videoclips(clips, method="chain") if len(clips) > 1 else clips[0]

    if final_video.duration < total_duration:
        tail = _with_duration(ColorClip(size=(width, height), color=_color_to_rgb(style.get("background_color", "black"))), total_duration - final_video.duration)
        final_video = concatenate_videoclips([final_video, tail], method="chain")
    elif final_video.duration > total_duration:
        subclip = getattr(final_video, "subclipped", None)
        if subclip is not None:
            final_video = subclip(0, total_duration)
        else:
            final_video = final_video.subclip(0, total_duration)

    narration_audio_path = data.get("narration_audio")
    narration_text = data.get("narration_text") or data.get("narration")
    voicevox_settings = data.get("voicevox", {}) or {}
    bgm_audio_path = data.get("bgm")
    audio_tracks = []

    if narration_audio_path:
        narration_path = resolve_project_path(narration_audio_path)
        if narration_path.exists():
            try:
                audio_tracks.append(AudioFileClip(str(narration_path)))
            except Exception as exc:
                print(f"[WARN] Failed to load narration audio '{narration_path}': {exc}")
        else:
            print(f"[WARN] Narration audio not found: {narration_path}")
    elif narration_text and (voicevox_settings.get("enabled") is True or os.getenv("AQUAPRESS_VOICEVOX") == "1"):
        narration_path = _synthesize_narration_audio(narration_text, folders, voicevox_settings)
        if narration_path is not None:
            try:
                audio_tracks.append(AudioFileClip(str(narration_path)))
            except Exception as exc:
                print(f"[WARN] Failed to load synthesized narration '{narration_path}': {exc}")
    elif narration_text:
        print("[INFO] VOICEVOX narration is configured but disabled; set AQUAPRESS_VOICEVOX=1 to enable.")

    bgm_clip = load_bgm_clip(str(resolve_project_path(bgm_audio_path)) if bgm_audio_path else None, volume=bgm_volume)
    if bgm_clip is not None:
        audio_tracks.append(bgm_clip)

    if audio_tracks:
        final_audio = CompositeAudioClip(audio_tracks)
        final_audio = _with_duration(final_audio, final_video.duration)
        if hasattr(final_video, "with_audio"):
            final_video = final_video.with_audio(final_audio)
        else:
            final_video = final_video.set_audio(final_audio)

    output_path = resolve_project_path(data.get("output", folders["videos"] / "aqua_press_sample.mp4"))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Encoding video: {output_path}", flush=True)
    final_video.write_videofile(
        str(output_path),
        fps=fps,
        codec="libx264",
        preset="ultrafast",
        audio_codec="aac",
        temp_audiofile=str(output_path.with_suffix(".temp-audio.m4a")),
        remove_temp=True,
        logger=None,
    )
    print("[INFO] Video encoding complete", flush=True)

    _close_clips(clips + [final_video], audio_tracks)
    return output_path


def _synthesize_narration_audio(text: str, folders: dict[str, Path], voicevox_settings: dict) -> Path | None:
    engine_url = str(voicevox_settings.get("engine_url", DEFAULT_VOICEVOX_ENGINE_URL))
    speaker = int(voicevox_settings.get("speaker", DEFAULT_SPEAKER))
    output_name = str(voicevox_settings.get("output", "narration_voicevox.wav"))
    output_path = folders["metadata"] / output_name
    print(f"[INFO] Synthesizing VOICEVOX narration: {output_path}", flush=True)
    return synthesize_voicevox(
        text=text,
        output_path=output_path,
        speaker=speaker,
        engine_url=engine_url,
        speed_scale=float(voicevox_settings.get("speed_scale", 1.0)),
        pitch_scale=float(voicevox_settings.get("pitch_scale", 0.0)),
        intonation_scale=float(voicevox_settings.get("intonation_scale", 1.0)),
        volume_scale=float(voicevox_settings.get("volume_scale", 1.0)),
        pre_phoneme_length=float(voicevox_settings.get("pre_phoneme_length", 0.1)),
        post_phoneme_length=float(voicevox_settings.get("post_phoneme_length", 0.1)),
        silence_length=float(voicevox_settings.get("silence_length", 0.0)),
    )


def _close_clips(video_clips: list, audio_clips: list) -> None:
    for clip in video_clips:
        try:
            clip.close()
        except Exception:
            pass
    for clip in audio_clips:
        try:
            clip.close()
        except Exception:
            pass
