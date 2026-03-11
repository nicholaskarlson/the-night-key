from __future__ import annotations

from pathlib import Path

from btg.engine import load_scenes, run, scripted_choice_provider, transcript_sha256
from btg.state import GameState


def test_deterministic_transcript_hash() -> None:
    scenes = load_scenes(Path("game_content/scenes.yaml"))

    # Scripted path (indices are relative to *available* choices per scene):
    # day1_arrival -> call mom
    # day1_call_mom -> tell truth
    # day1_foyer -> kitchen
    # day1_kitchen -> voicemail
    # day1_voicemail -> text cousin
    # day1_cousin_text -> ask them to come
    # day1_foyer -> kitchen
    # day1_kitchen -> kettle
    # day1_kettle -> call mom (requires called_mom)
    script = [1, 1, 0, 1, 1, 0, 0, 4, 0]

    st1, t1 = run(scenes, "day1_arrival", GameState(), scripted_choice_provider(script))
    st2, t2 = run(scenes, "day1_arrival", GameState(), scripted_choice_provider(script))

    assert st1 == st2
    assert transcript_sha256(t1) == transcript_sha256(t2)
