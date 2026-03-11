from __future__ import annotations

from pathlib import Path

import pytest

from btg.engine import load_story


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_includes_merges_scenes_and_validates(tmp_path: Path) -> None:
    story_dir = tmp_path / "s"
    scenes_yaml = story_dir / "scenes.yaml"
    inc1 = story_dir / "scenes" / "act1.yaml"
    inc2 = story_dir / "scenes" / "act2.yaml"

    _write(
        scenes_yaml,
        """
schema_version: 1
title: "Inc Test"
start: a1
includes:
  - scenes/act1.yaml
  - scenes/act2.yaml
scenes:
  - id: root_scene
    text: "root"
    terminal: true
""".lstrip(),
    )
    _write(
        inc1,
        """
scenes:
  - id: a1
    text: "act1"
    choices:
      - label: "to a2"
        goto: a2
""".lstrip(),
    )
    _write(
        inc2,
        """
- id: a2
  text: "act2"
  terminal: true
""".lstrip(),
    )

    story = load_story(scenes_yaml)
    assert story.start == "a1"
    assert set(story.scenes.keys()) == {"root_scene", "a1", "a2"}


def test_includes_glob_is_deterministic(tmp_path: Path) -> None:
    story_dir = tmp_path / "s"
    scenes_yaml = story_dir / "scenes.yaml"
    _write(
        scenes_yaml,
        """
schema_version: 1
title: "Glob"
start: a
includes:
  - parts/*.yaml
""".lstrip(),
    )
    # write in reverse order, glob expansion sorts by path
    _write(story_dir / "parts" / "b.yaml", 'scenes: [{id: b, text: "b", terminal: true}]\n')
    _write(story_dir / "parts" / "a.yaml", 'scenes: [{id: a, text: "a", terminal: true}]\n')

    story = load_story(scenes_yaml)
    assert "a" in story.scenes
    assert "b" in story.scenes


def test_duplicate_scene_id_hard_fails(tmp_path: Path) -> None:
    story_dir = tmp_path / "s"
    scenes_yaml = story_dir / "scenes.yaml"
    _write(
        scenes_yaml,
        """
schema_version: 1
title: "Dup"
start: x
includes:
  - one.yaml
  - two.yaml
""".lstrip(),
    )
    _write(story_dir / "one.yaml", 'scenes: [{id: x, text: "one", terminal: true}]\n')
    _write(story_dir / "two.yaml", 'scenes: [{id: x, text: "two", terminal: true}]\n')

    with pytest.raises(ValueError, match="duplicate scene id"):
        load_story(scenes_yaml)
