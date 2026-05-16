from __future__ import annotations

import importlib

from utils.paths import ensure_output_folders, get_project_root


def test_sample_data_exists():
    root = get_project_root()
    assert (root / "input" / "sample_data" / "sample_video.json").exists()


def test_style_config_exists():
    root = get_project_root()
    assert (root / "config" / "video_style.yaml").exists()


def test_generator_module_imports():
    module = importlib.import_module("video.generator")
    assert module is not None


def test_ensure_output_folders_creates_directories():
    folders = ensure_output_folders()
    assert folders["videos"].exists()
    assert folders["thumbnails"].exists()
    assert folders["metadata"].exists()
