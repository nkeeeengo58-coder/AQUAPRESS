from __future__ import annotations

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class TestAquaPressVideoV01(unittest.TestCase):
    def test_sample_video_json_exists(self):
        self.assertTrue((PROJECT_ROOT / "input/sample_data/sample_video.json").exists())

    def test_video_style_yaml_exists(self):
        self.assertTrue((PROJECT_ROOT / "config/video_style.yaml").exists())

    def test_generator_importable(self):
        from video import generator  # noqa: F401

    def test_output_dir_creation(self):
        from utils.paths import ensure_output_dirs

        ensure_output_dirs()
        self.assertTrue((PROJECT_ROOT / "output/videos").exists())
        self.assertTrue((PROJECT_ROOT / "output/thumbnails").exists())
        self.assertTrue((PROJECT_ROOT / "output/metadata").exists())


if __name__ == "__main__":
    unittest.main()
