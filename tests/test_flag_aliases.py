from __future__ import annotations

from pathlib import Path

from btg.engine import load_story


def test_choice_flag_aliases_set_flags_clear_flags(tmp_path: Path) -> None:
    # Author-facing aliases should be accepted for non-programmer friendliness.
    yml = '''
schema_version: 1
title: "Alias Test"
start: s1
flags: [a, b]
scenes:
  - id: s1
    text: "start"
    choices:
      - label: "go"
        goto: s2
        set_flags: [a]
        clear_flags: [b]
  - id: s2
    terminal: true
    text: "end"
'''
    p = tmp_path / "scenes.yaml"
    p.write_text(yml, encoding="utf-8")

    story = load_story(p)
    ch = story.scenes["s1"].choices[0]
    assert ch.sets_flags == ("a",)
    assert ch.clears_flags == ("b",)
