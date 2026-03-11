from __future__ import annotations

from pathlib import Path

from btg.replay import replay_from_text
from btg.savegame import SaveGame, loads, write


def test_savegame_roundtrip(tmp_path: Path) -> None:
    story_text = Path("game_content/scenes.yaml").read_text(encoding="utf-8")
    st, _transcript, tr_sha, story_sha = replay_from_text(story_text, script=[0, 0, 0, 0, 0])

    save = SaveGame(
        schema_version=1,
        story_sha256=story_sha,
        scene_id="day1_end_humor",
        state=st,
        script=[0, 0, 0, 0, 0],
        transcript_sha256=tr_sha,
    )

    p = tmp_path / "save.json"
    write(p, save)

    loaded = loads(p.read_text(encoding="utf-8"))
    assert loaded.story_sha256 == story_sha
    assert loaded.scene_id == "day1_end_humor"
    assert loaded.script == [0, 0, 0, 0, 0]
    assert loaded.transcript_sha256 == tr_sha
    assert loaded.state == st
