from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    from moviepy.editor import ImageClip
except ImportError:  # moviepy v2 fallback
    from moviepy.video.VideoClip import ImageClip


def _load_font(font_size: int, font_path: str | Path | None = None) -> ImageFont.ImageFont:
    candidates: list[Path] = []
    if font_path:
        candidates.append(Path(font_path))

    candidates.extend(
        [
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), font_size)
            except OSError:
                continue

    warnings.warn("No preferred font found. Falling back to default font.")
    return ImageFont.load_default()


def create_text_imageclip(
    text: str,
    width: int,
    font_size: int,
    text_color: str = "white",
    bg_opacity: float = 0.55,
    padding: int = 24,
) -> ImageClip:
    lines = (text or "").split("\n")
    font = _load_font(font_size)

    dummy = Image.new("RGBA", (width, 10), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dummy)
    line_boxes = [draw.textbbox((0, 0), line or " ", font=font) for line in lines]
    line_heights = [box[3] - box[1] for box in line_boxes]
    max_line_width = max((box[2] - box[0] for box in line_boxes), default=0)

    line_spacing = max(8, int(font_size * 0.22))
    text_height = sum(line_heights) + line_spacing * max(0, len(lines) - 1)
    box_width = min(width, max_line_width + padding * 2)
    box_height = text_height + padding * 2

    image = Image.new("RGBA", (box_width, box_height), (0, 0, 0, int(255 * max(0.0, min(1.0, bg_opacity)))))
    draw = ImageDraw.Draw(image)

    y = padding
    for i, line in enumerate(lines):
        line_box = draw.textbbox((0, 0), line or " ", font=font)
        line_w = line_box[2] - line_box[0]
        x = max(padding, (box_width - line_w) // 2)
        draw.text((x, y), line, fill=text_color, font=font)
        y += line_heights[i] + line_spacing

    return ImageClip(np.array(image))
