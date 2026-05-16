from __future__ import annotations

from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_project_path(relative_path: str | Path) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        return path
    return get_project_root() / path


def ensure_output_folders() -> dict[str, Path]:
    root = get_project_root()
    folders = {
        "output": root / "output",
        "videos": root / "output" / "videos",
        "thumbnails": root / "output" / "thumbnails",
        "metadata": root / "output" / "metadata",
    }
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    return folders
