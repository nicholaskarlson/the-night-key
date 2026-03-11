from __future__ import annotations

from btg.engine import load_story_text, run, scripted_choice_provider
from btg.lint import lint_story
from btg.state import GameState


def test_text_templating_renders_state_and_flags() -> None:
    yml = """
schema_version: 1
title: "Template Test"
start: s1
flags: [a]
scenes:
  - id: s1
    text: "E={energy} Day={day} Flags={flags} Literal={{brace}} Unknown={unknown}"
    choices:
      - label: "Go"
        goto: s2
        sets_flags: [a]
  - id: s2
    terminal: true
    text: "After Flags={flags}"
"""
    story = load_story_text(yml, source="<mem>")
    st, transcript = run(
        story.scenes, story.start, GameState(), scripted_choice_provider([0]), max_steps=20
    )

    joined = "\n".join(transcript)
    assert "E=5" in joined
    assert "Day=1" in joined
    assert "Flags=(none)" in joined
    assert "Literal={brace}" in joined
    assert "Unknown={unknown}" in joined
    assert "After Flags=a" in joined
    assert st.has_flag("a")


def test_templating_lint_warns_on_unknown_placeholders() -> None:
    yml = """
schema_version: 1
title: "Template Lint"
start: s1
scenes:
  - id: s1
    text: "Hello {mystery}."
    terminal: true
"""
    story = load_story_text(yml, source="<mem>")
    issues = lint_story(story)
    assert any(i.code == "TEMPLATE_UNKNOWN" for i in issues)
