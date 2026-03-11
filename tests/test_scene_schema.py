from __future__ import annotations

from pathlib import Path

from btg.engine import load_scenes, load_story


def test_story_loads_and_gotos_valid() -> None:
    story = load_story(Path("game_content/scenes.yaml"))
    scenes = story.scenes

    assert story.start in scenes
    assert "day1_arrival" in scenes
    assert "day1_end_connected" in scenes
    assert "day1_end_solitary" in scenes
    assert "day1_end_humor" in scenes

    # Backward-compatible loader still works
    scenes2 = load_scenes(Path("game_content/scenes.yaml"))
    assert scenes2.keys() == scenes.keys()
