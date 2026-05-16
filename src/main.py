from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ai.gemini_script import generate_script_from_text, merge_script_into_video_data
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
    if args.info:
        try:
            script_data = generate_script_from_text(args.info)
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


if __name__ == "__main__":
    raise SystemExit(main())
