from __future__ import annotations

from btg.engine import load_story_text
from btg.lint import has_errors, lint_story


def test_lint_unknown_flag_is_error() -> None:
    text = """schema_version: 1
start: s
flags: [a]
scenes:
  - id: s
    text: "hi"
    choices:
      - label: "go"
        goto: end
        sets_flags: [b]
  - id: end
    text: "bye"
    terminal: true
"""
    story = load_story_text(text)
    issues = lint_story(story)
    assert has_errors(issues)
    assert any(i.code == "FLAG_UNDECLARED" for i in issues)


def test_lint_missing_flags_list_warns() -> None:
    text = """schema_version: 1
start: s
scenes:
  - id: s
    text: "hi"
    choices:
      - label: "go"
        goto: end
        sets_flags: [x]
  - id: end
    text: "bye"
    terminal: true
"""
    story = load_story_text(text)
    issues = lint_story(story)
    assert any(i.code == "FLAGS_MISSING" for i in issues)
