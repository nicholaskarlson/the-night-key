from __future__ import annotations

import pytest

from btg.engine import available_choices, load_story_text
from btg.state import GameState


def test_requires_state_hides_choice_until_satisfied() -> None:
    yml = """schema_version: 1
title: "State gating test"
start: s1
flags: []
scenes:
  - id: s1
    text: "start"
    choices:
      - label: "Always"
        goto: end
      - label: "Needs energy"
        goto: end
        requires_state:
          energy: ">= 6"
  - id: end
    terminal: true
    text: "end"
"""
    story = load_story_text(yml, source="requires_state_test")
    scene = story.scenes["s1"]

    labels = [c.label for c in available_choices(scene, GameState())]
    assert "Always" in labels
    assert "Needs energy" not in labels

    st_ok = GameState().with_updates(energy=6)
    labels_ok = [c.label for c in available_choices(scene, st_ok)]
    assert "Needs energy" in labels_ok


def test_forbids_state_hides_choice_when_condition_true() -> None:
    yml = """schema_version: 1
title: "State gating test"
start: s1
flags: []
scenes:
  - id: s1
    text: "start"
    choices:
      - label: "Calm down"
        goto: end
        forbids_state:
          guilt: ">= 2"
  - id: end
    terminal: true
    text: "end"
"""
    story = load_story_text(yml, source="forbids_state_test")
    scene = story.scenes["s1"]

    # Default guilt is 2, so the choice is forbidden.
    labels = [c.label for c in available_choices(scene, GameState())]
    assert "Calm down" not in labels

    st_ok = GameState().with_updates(guilt=1)
    labels_ok = [c.label for c in available_choices(scene, st_ok)]
    assert "Calm down" in labels_ok


def test_invalid_state_gate_field_raises() -> None:
    yml = """schema_version: 1
title: "Bad field"
start: s1
flags: []
scenes:
  - id: s1
    text: "start"
    choices:
      - label: "Bad"
        goto: s1
        requires_state:
          coins: ">= 1"
"""
    with pytest.raises(ValueError):
        load_story_text(yml, source="bad_field")


def test_invalid_state_gate_syntax_raises() -> None:
    yml = """schema_version: 1
title: "Bad syntax"
start: s1
flags: []
scenes:
  - id: s1
    text: "start"
    choices:
      - label: "Bad"
        goto: s1
        requires_state:
          energy: ">> 3"
"""
    with pytest.raises(ValueError):
        load_story_text(yml, source="bad_syntax")
