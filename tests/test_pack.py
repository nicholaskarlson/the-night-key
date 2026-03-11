from __future__ import annotations

import hashlib
from pathlib import Path

from btg.engine import load_story_text
from btg.init_story import init_story
from btg.lint import lint_story
from btg.pack import build_pack, read_pack_scenes_text, unpack_pack


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_pack_deterministic(tmp_path: Path) -> None:
    story_dir = tmp_path / "story"
    init_story(story_dir, title="Pack Test")

    p1 = tmp_path / "a.pack.zip"
    p2 = tmp_path / "b.pack.zip"

    build_pack(story_dir, p1, force=True)
    build_pack(story_dir, p2, force=True)

    assert _sha256_file(p1) == _sha256_file(p2)


def test_pack_read_and_unpack(tmp_path: Path) -> None:
    story_dir = tmp_path / "story"
    init_story(story_dir, title="Pack Test")

    pack_path = tmp_path / "story.pack.zip"
    build_pack(story_dir, pack_path, force=True)

    text = read_pack_scenes_text(pack_path)
    story = load_story_text(text)
    assert lint_story(story) == []

    out_dir = tmp_path / "unpacked"
    unpack_pack(pack_path, out_dir, force=True)
    assert (out_dir / "scenes.yaml").exists()
