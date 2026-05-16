from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from utils.paths import ensure_output_folders
from video.captions import _load_font


def create_thumbnail(title: str, output_path: str | None = None, width: int = 1280, height: int = 720) -> Path:
    folders = ensure_output_folders()
    if output_path is None:
        output_path = folders["thumbnails"] / "aqua_press_thumbnail.png"
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(canvas)
    font = _load_font(72)

    bbox = draw.multiline_textbbox((0, 0), title, font=font, spacing=8, align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2

    draw.line([(width * 0.12, height * 0.22), (width * 0.88, height * 0.22)], fill="red", width=12)
    draw.multiline_text((text_x, text_y), title, font=font, fill="white", spacing=8, align="center")
    draw.line([(width * 0.12, height * 0.78), (width * 0.88, height * 0.78)], fill="red", width=8)

    canvas.save(output_file)
    return output_file
