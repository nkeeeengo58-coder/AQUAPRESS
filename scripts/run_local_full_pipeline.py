from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from crawler import run_crawler
from crawler.storage import save_crawler_data
from utils.paths import ensure_output_folders, get_project_root
from video.generator import generate_video, load_video_style
from video.thumbnail import create_thumbnail


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split(" ")
    if not words:
        return [text]

    lines: list[str] = []
    current = words[0]
    for w in words[1:]:
        candidate = f"{current} {w}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return lines


def _create_info_image(image_path: Path, title: str, category: str) -> None:
    width, height = 1080, 1920
    image = Image.new("RGB", (width, height), (8, 12, 18))
    draw = ImageDraw.Draw(image)

    accent = (210, 38, 38)
    text_color = (240, 240, 240)

    draw.rectangle([0, 120, width, 140], fill=accent)
    draw.rectangle([0, 1780, width, 1795], fill=accent)

    try:
        title_font = ImageFont.truetype("arial.ttf", 76)
        body_font = ImageFont.truetype("arial.ttf", 52)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    badge = f"AQUA PRESS / {category.upper()}"
    draw.text((80, 220), badge, font=body_font, fill=(255, 210, 210))

    wrapped = _fit_text(draw, title, title_font, max_width=920)
    y = 380
    for line in wrapped[:8]:
        draw.text((80, y), line, font=title_font, fill=text_color)
        y += 96

    image.save(image_path, format="JPEG", quality=92)


def main() -> int:
    print("[INFO] Running crawler...")
    crawler_result = run_crawler()
    items = crawler_result.get("items", [])
    if not items:
        print("[ERROR] No crawler items found")
        return 1

    save_path = save_crawler_data(crawler_result)
    print(f"[INFO] Crawler data saved: {save_path}")

    folders = ensure_output_folders()
    root = get_project_root()
    generated_images_dir = root / "output" / "generated" / "images"
    generated_images_dir.mkdir(parents=True, exist_ok=True)

    top_items = items[:3]
    sections = []
    for i, item in enumerate(top_items, start=1):
        img_path = generated_images_dir / f"crawler_auto_{i}.jpg"
        _create_info_image(
            image_path=img_path,
            title=(item.get("title") or "Aquarium Update")[:180],
            category=item.get("category") or "news",
        )
        sections.append(
            {
                "image": str(img_path.relative_to(root)).replace("\\", "/"),
                "caption": (item.get("title") or "最新情報")[:90],
            }
        )

    while len(sections) < 3:
        sections.append({"image": None, "caption": "本日の注目情報をチェック"})

    narration_lines = [
        "AQUA PRESS 速報です。",
        "Googleニュースから本日の注目情報をお届けします。",
    ]
    for item in top_items[:2]:
        title = (item.get("title") or "最新情報").replace("\n", " ")
        narration_lines.append(f"注目: {title[:70]}")

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_output = f"output/videos/preview_aqua_press_auto_{now}.mp4"

    # Phase 8: Use VOICEVOX_ENGINE_URL from environment (GitHub Actions VOICEVOX Docker)
    voicevox_enabled = os.getenv("AQUAPRESS_VOICEVOX", "0") == "1"
    voicevox_engine_url = os.getenv("VOICEVOX_ENGINE_URL", "http://127.0.0.1:50021")

    data = {
        "title": "AQUA PRESS 自動速報",
        "description": "Google情報収集から自動生成したアクアリウム速報動画",
        "hook": "【AQUA PRESS】\n本日のアクアリウム速報",
        "sections": sections,
        "narration_audio": None,
        "narration_text": "\n".join(narration_lines),
        "voicevox": {
            "enabled": voicevox_enabled,
            "engine_url": voicevox_engine_url,
            "speaker": 3,
            "output": f"auto_narration_{now}.wav",
        },
        "bgm": None,
        "output": video_output,
    }

    generated_script_path = folders["metadata"] / f"generated_script_from_crawler_local_{now}.json"
    generated_script_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] Local script saved: {generated_script_path}")

    style = load_video_style()
    style["width"] = 540
    style["height"] = 960
    style["fps"] = 12
    style["duration_seconds"] = 12
    style["font_size_title"] = 44
    style["font_size_caption"] = 34

    output_path = generate_video(data, style=style)
    thumb_path = create_thumbnail(data.get("title", "AQUA PRESS"))

    print(f"[OK] Video generated: {output_path}")
    print(f"[OK] Thumbnail generated: {thumb_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
