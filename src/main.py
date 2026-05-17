from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ai.gemini_script import generate_script_from_text, merge_script_into_video_data
from crawler import run_crawler
from crawler.storage import load_crawler_data, save_crawler_data
from utils.paths import ensure_output_folders, get_project_root
from video.generator import generate_video, load_sample_data, load_video_style
from video.thumbnail import create_thumbnail


def main() -> int:
    ensure_output_folders()
    root = get_project_root()
    default_sample_path = root / "input" / "sample_data" / "sample_video.json"

    parser = argparse.ArgumentParser(description="Generate AQUA PRESS short video")
    parser.add_argument(
        "sample",
        nargs="?",
        default=str(default_sample_path),
        help="Input JSON path for video data",
    )
    parser.add_argument(
        "--info",
        help="Generate script data with Gemini from free text, then merge into input JSON schema",
    )
    parser.add_argument(
        "--crawler",
        action="store_true",
        help="Run crawler to fetch fresh data, then generate script with Gemini",
    )
    parser.add_argument(
        "--crawler-date",
        help="Use crawler data from specified date (YYYY-MM-DD), then generate script with Gemini",
    )
    parser.add_argument(
        "--language",
        default="ja",
        choices=["ja", "en", "zh", "th"],
        help="Target language (ja, en, zh, th). Defaults to ja.",
    )
    args = parser.parse_args()
    sample_path = Path(args.sample)
    if not sample_path.is_absolute():
        sample_path = root / sample_path

    if not sample_path.exists():
        print(f"[ERROR] Sample data not found: {sample_path}")
        return 1

    style = load_video_style()
    if os.getenv("AQUAPRESS_PREVIEW") == "1":
        # Fast render profile for Phase 1 visual checks.
        style["width"] = 540
        style["height"] = 960
        style["fps"] = 12
        style["duration_seconds"] = 12
        style["font_size_title"] = 44
        style["font_size_caption"] = 34
        print("[INFO] Preview mode enabled (540x960, 12fps, 12s)")

    data = load_sample_data(sample_path)
    
    if args.crawler:
        try:
            print(f"[INFO] Running crawler to fetch fresh data for language: {args.language}...")
            crawler_result = run_crawler(language=args.language)
            save_crawler_data(crawler_result)
            info_text = _convert_crawler_to_info_text(crawler_result, language=args.language)
            script_data = generate_script_from_text(info_text, language=args.language)
            data = merge_script_into_video_data(data, script_data)
            generated_path = root / "output" / "metadata" / "generated_script.json"
            generated_path.parent.mkdir(parents=True, exist_ok=True)
            generated_path.write_text(json.dumps(script_data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[INFO] Crawler + Gemini script generated: {generated_path}")
        except ValueError as exc:
            print(f"[ERROR] Crawler/Gemini generation failed: {exc}")
            return 1
    elif args.crawler_date:
        try:
            print(f"[INFO] Loading crawler data from {args.crawler_date} for language: {args.language}...")
            crawler_result = load_crawler_data(args.crawler_date)
            if not crawler_result.get("items"):
                print(f"[WARN] No crawler data found for {args.crawler_date}")
            else:
                info_text = _convert_crawler_to_info_text(crawler_result, language=args.language)
                script_data = generate_script_from_text(info_text, language=args.language)
                data = merge_script_into_video_data(data, script_data)
                generated_path = root / "output" / "metadata" / "generated_script.json"
                generated_path.parent.mkdir(parents=True, exist_ok=True)
                generated_path.write_text(json.dumps(script_data, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"[INFO] Crawler + Gemini script generated: {generated_path}")
        except ValueError as exc:
            print(f"[ERROR] Crawler/Gemini generation failed: {exc}")
            return 1
    elif args.info:
        try:
            script_data = generate_script_from_text(args.info, language=args.language)
            data = merge_script_into_video_data(data, script_data)
            generated_path = root / "output" / "metadata" / "generated_script.json"
            generated_path.parent.mkdir(parents=True, exist_ok=True)
            generated_path.write_text(json.dumps(script_data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[INFO] Gemini script generated: {generated_path}")
        except ValueError as exc:
            print(f"[ERROR] Gemini script generation failed: {exc}")
            return 1

    if os.getenv("AQUAPRESS_PREVIEW") == "1":
        output_name = Path(data.get("output", "output/videos/aqua_press_sample.mp4")).name
        data["output"] = f"output/videos/preview_{output_name}"

    output_path = generate_video(data, style=style)
    create_thumbnail(data.get("title", "AQUA PRESS"))
    print(f"[OK] Video generated: {output_path}")
    return 0


def _convert_crawler_to_info_text(crawler_result: dict, language: str = "ja") -> str:
    """Convert crawler data to text format for Gemini input.
    
    Args:
        crawler_result: Dictionary with 'items' key from crawler.
        language: Target language (ja, en, zh, th).
        
    Returns:
        Text formatted for Gemini input.
    """
    items = crawler_result.get("items", [])
    if not items:
        raise ValueError("Crawler result contains no items")

    # Language-specific headers
    headers = {
        "ja": "アクアリウム最新情報:\n",
        "en": "Latest aquarium news:\n",
        "zh": "最新水族馆信息:\n",
        "th": "ข่าวตัวอักษรล่าสุด:\n",
    }
    
    lines = [headers.get(language, headers["ja"])]
    for item in items[:5]:
        title = item.get("title", "").strip()
        desc = item.get("description", "").strip()
        category = item.get("category", "").strip()
        if title:
            lines.append(f"【{category.upper()}】{title}")
            if desc:
                lines.append(f"  {desc}")
            lines.append("")

    default_text = {
        "ja": "アクアリウム情報",
        "en": "Aquarium information",
        "zh": "水族馆信息",
        "th": "ข้อมูลตัวอักษร",
    }
    
    return "\n".join(lines) or default_text.get(language, default_text["ja"])





if __name__ == "__main__":
    raise SystemExit(main())
