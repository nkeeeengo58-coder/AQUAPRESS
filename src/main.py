from __future__ import annotations

import os
from pathlib import Path

from utils.paths import ensure_output_folders, get_project_root
from video.generator import generate_video, load_sample_data, load_video_style
from video.thumbnail import create_thumbnail


def main() -> int:
    ensure_output_folders()
    root = get_project_root()
    sample_path = root / "input" / "sample_data" / "sample_video.json"

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
    if os.getenv("AQUAPRESS_PREVIEW") == "1":
        output_name = Path(data.get("output", "output/videos/aqua_press_sample.mp4")).name
        data["output"] = f"output/videos/preview_{output_name}"

    output_path = generate_video(data, style=style)
    create_thumbnail(data.get("title", "AQUA PRESS"))
    print(f"[OK] Video generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
