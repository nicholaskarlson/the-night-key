from __future__ import annotations

from importlib import resources
from pathlib import Path

from btg.engine import load_scenes_text


def test_packaged_scenes_parse() -> None:
    text = resources.files("btg").joinpath("data/scenes.yaml").read_text(encoding="utf-8")
    scenes = load_scenes_text(text)
    assert "day1_arrival" in scenes


def test_packaged_scenes_matches_repo() -> None:
    repo_text = Path("game_content/scenes.yaml").read_text(encoding="utf-8")
    pkg_text = resources.files("btg").joinpath("data/scenes.yaml").read_text(encoding="utf-8")
    assert repo_text.replace("\r\n", "\n") == pkg_text.replace("\r\n", "\n")
