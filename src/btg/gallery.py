from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .pack import build_pack

GALLERY_SCHEMA_VERSION = 1


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _stable_json(obj: dict[str, Any]) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")


def discover_story_dirs(stories_root: Path) -> list[tuple[str, Path]]:
    """Return [(slug, dir)] for direct children containing scenes.yaml."""
    stories_root = stories_root.expanduser().resolve()
    if not stories_root.exists():
        return []
    out: list[tuple[str, Path]] = []
    for child in sorted((p for p in stories_root.iterdir() if p.is_dir()), key=lambda p: p.name):
        if (child / "scenes.yaml").exists():
            out.append((child.name, child))
    return out


def build_gallery(stories_root: Path, out_dir: Path) -> Path:
    """Build deterministic packs into out_dir and write a stable index.json."""
    stories = discover_story_dirs(stories_root)
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    for slug, story_dir in stories:
        pack_path = out_dir / f"{slug}.pack.zip"
        res = build_pack(story_dir, pack_path, force=True)
        pack_sha = _sha256_file(pack_path)
        m = res.manifest
        entries.append(
            {
                "slug": slug,
                "pack": pack_path.name,
                "pack_sha256": pack_sha,
                "title": str(m.get("title", "")),
                "start": str(m.get("start", "")),
                "scenes_count": int(m.get("scenes_count", 0)),
                "choices_count": int(m.get("choices_count", 0)),
                "flags": list(m.get("flags", [])),
            }
        )

    entries.sort(key=lambda e: e["slug"])

    index: dict[str, Any] = {"schema_version": GALLERY_SCHEMA_VERSION, "stories": entries}
    index_path = out_dir / "index.json"
    index_path.write_bytes(_stable_json(index))
    return index_path
