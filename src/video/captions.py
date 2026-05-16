from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    from moviepy import ImageClip
except ImportError:  # pragma: no cover
    from moviepy.editor import ImageClip


def _get_font_candidates() -> list[str]:
    return [
        "C:/Windows/Fonts/yugothb.ttc",
        "C:/Windows/Fonts/yugothm.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]


def _load_font(font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in _get_font_candidates():
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), font_size)
            except Exception:
                continue
    try:
        return ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        return ImageFont.load_default()


def _clip_with_duration(clip, duration: float):
    method = getattr(clip, "with_duration", None)
    if method is not None:
        return method(duration)
    return clip.set_duration(duration)


def create_caption_clip(
    text: str,
    width: int,
    height: int,
    text_color: str = "white",
    background_opacity: float = 0.55,
    font_size: int = 58,
    duration: float = 5.0,
):
    # Use RGB (no alpha mask) to keep MoviePy compositing fast on Windows.
    canvas = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font = _load_font(font_size)

    lines = text.splitlines() if text else [""]
    padding_x = 48
    padding_y = 30
    line_spacing = 14
    bbox_heights = []
    max_text_width = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line or " ", font=font)
        bbox_heights.append(bbox[3] - bbox[1])
        max_text_width = max(max_text_width, bbox[2] - bbox[0])

    text_block_height = sum(bbox_heights) + line_spacing * max(0, len(lines) - 1)
    box_width = min(width - 120, max_text_width + padding_x * 2)
    box_height = text_block_height + padding_y * 2
    box_x = (width - box_width) // 2
    box_y = height - box_height - 160

    darkness = int(12 + 24 * max(0.0, min(1.0, background_opacity)))
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_width, box_y + box_height],
        radius=24,
        fill=(darkness, darkness, darkness),
    )

    text_y = box_y + padding_y
    for index, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line or " ", font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (width - text_width) // 2
        draw.text((text_x, text_y), line, font=font, fill=text_color)
        text_y += text_height + line_spacing

    return _clip_with_duration(ImageClip(np.array(canvas)), duration)


def create_title_card_clip(
    title: str,
    width: int,
    height: int,
    text_color: str = "white",
    accent_color: str = "red",
    font_size: int = 74,
    duration: float = 3.0,
):
    canvas = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font = _load_font(font_size)

    bbox = draw.multiline_textbbox((0, 0), title, font=font, spacing=12, align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2 - 80

    draw.line([(width * 0.18, height * 0.34), (width * 0.82, height * 0.34)], fill=accent_color, width=10)
    draw.multiline_text((text_x, text_y), title, font=font, fill=text_color, spacing=12, align="center")
    draw.line([(width * 0.18, height * 0.66), (width * 0.82, height * 0.66)], fill=accent_color, width=6)

    return _clip_with_duration(ImageClip(np.array(canvas)), duration)
