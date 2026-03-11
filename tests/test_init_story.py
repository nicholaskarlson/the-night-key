from __future__ import annotations

from pathlib import Path

import pytest

from btg.engine import load_story
from btg.init_story import init_story
from btg.lint import lint_story


def test_init_story_creates_files(tmp_path: Path) -> None:
    d = tmp_path / "my_story"
    res = init_story(d, title="Test Story")
    assert res.scenes_path.exists()
    assert res.readme_path.exists()

    story = load_story(res.scenes_path)
    issues = lint_story(story)
    assert issues == []


def test_init_story_refuses_overwrite_without_force(tmp_path: Path) -> None:
    d = tmp_path / "my_story"
    init_story(d, title="A")
    with pytest.raises(ValueError):
        init_story(d, title="B", force=False)

    init_story(d, title="B", force=True)
