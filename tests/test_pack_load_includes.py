from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from btg.engine import load_story_text
from btg.pack import read_pack_story_text


def _write_zip(p: Path, files: dict[str, str]) -> None:
    with ZipFile(p, "w", compression=ZIP_DEFLATED) as z:
        for name, text in files.items():
            z.writestr(name, text)


def test_read_pack_story_text_merges_includes(tmp_path: Path) -> None:
    pack_path = tmp_path / "s.pack.zip"
    _write_zip(
        pack_path,
        {
            "scenes.yaml": """
schema_version: 1
title: "Pack Includes"
start: a
includes:
  - scenes/act1.yaml
scenes:
  - id: root_scene
    text: "root"
    terminal: true
""",
            "scenes/act1.yaml": """
- id: a
  text: "act1"
  terminal: true
""",
        },
    )

    merged = read_pack_story_text(pack_path)
    story = load_story_text(merged, source="pack:test")
    assert story.start == "a"
    assert set(story.scenes.keys()) == {"root_scene", "a"}


def test_read_pack_story_text_glob_and_missing(tmp_path: Path) -> None:
    pack_path = tmp_path / "g.pack.zip"
    _write_zip(
        pack_path,
        {
            "scenes.yaml": """
schema_version: 1
title: "Glob"
start: a
includes:
  - scenes/*.yaml
scenes: []
""",
            "scenes/b.yaml": 'scenes: [{id: b, text: "b", terminal: true}]\n',
            "scenes/a.yaml": 'scenes: [{id: a, text: "a", terminal: true}]\n',
        },
    )
    merged = read_pack_story_text(pack_path)
    story = load_story_text(merged, source="pack:test")
    assert "a" in story.scenes
    assert "b" in story.scenes

    pack_path2 = tmp_path / "m.pack.zip"
    _write_zip(
        pack_path2,
        {
            "scenes.yaml": """
schema_version: 1
title: "Missing"
start: a
includes:
  - scenes/nope.yaml
scenes: []
""",
        },
    )
    with pytest.raises(ValueError, match="include not found"):
        read_pack_story_text(pack_path2)
