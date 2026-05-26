from __future__ import annotations

from video.generator import generate_video, load_style, load_video_data
from video.thumbnail import generate_thumbnail


def main() -> None:
    style = load_style("config/video_style.yaml")
    data = load_video_data("input/sample_data/sample_video.json")

    output_path = generate_video(data, style)
    thumbnail_path = generate_thumbnail(data.get("title", "AQUA PRESS"))

    print(f"[INFO] Video generated: {output_path}")
    print(f"[INFO] Thumbnail generated: {thumbnail_path}")


if __name__ == "__main__":
    main()
