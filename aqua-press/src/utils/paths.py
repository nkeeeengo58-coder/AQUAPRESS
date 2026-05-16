from __future__ import annotations

from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_path(path_str: str | None) -> Path | None:
    if not path_str:
        return None
    path = Path(path_str)
    if path.is_absolute():
        return path
    return get_project_root() / path


def ensure_output_dirs() -> None:
    root = get_project_root()
    for rel in ("output/videos", "output/thumbnails", "output/metadata"):
        (root / rel).mkdir(parents=True, exist_ok=True)
