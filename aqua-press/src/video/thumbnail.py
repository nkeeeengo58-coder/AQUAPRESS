from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from utils.paths import ensure_output_dirs, get_project_root


def _load_font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def generate_thumbnail(title: str, output_path: str = "output/thumbnails/aqua_press_thumbnail.png") -> Path:
    ensure_output_dirs()
    root = get_project_root()
    out = root / output_path
    out.parent.mkdir(parents=True, exist_ok=True)

    width, height = 1080, 1920
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)

    draw.rectangle([(80, height // 2 - 250), (1000, height // 2 - 235)], fill="red")

    font = _load_font(72)
    text = title or "AQUA PRESS"
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=14)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.multiline_text(
        ((width - text_w) // 2, (height - text_h) // 2 - 100),
        text,
        fill="white",
        font=font,
        align="center",
        spacing=14,
    )

    image.save(out)
    return out
