from __future__ import annotations

import pytest

from btg.engine import load_story_text


def test_yaml_parse_error_includes_line_col_and_snippet() -> None:
    bad = "title: Test\nscenes:\n  - id: a\n    text: hi\n    choices: [\n"
    with pytest.raises(ValueError) as ei:
        load_story_text(bad, source="stories/bad/scenes.yaml")

    msg = str(ei.value)
    assert "stories/bad/scenes.yaml:" in msg
    assert "YAML parse error" in msg
    # Should include a caret line if mark is present.
    assert "^" in msg
