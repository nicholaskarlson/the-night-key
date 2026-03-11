from __future__ import annotations

from pathlib import Path

from btg.cli import main as btg_main
from btg.replay import parse_script_file, replay_from_text


def test_replay_day1_humor_sha_stable() -> None:
    story_text = Path("game_content/scenes.yaml").read_text(encoding="utf-8")
    script = parse_script_file(Path("replays/day1_humor.script"))
    _, _, sha, _ = replay_from_text(story_text, script=script)
    assert sha == "cd13654fbaa4da31105a2d2ad0ee87c6db5fccefd658c259522c3a51062b6307"


def test_replay_day1_connected_sha_stable() -> None:
    story_text = Path("game_content/scenes.yaml").read_text(encoding="utf-8")
    script = parse_script_file(Path("replays/day1_connected.script"))
    _, _, sha, _ = replay_from_text(story_text, script=script)
    assert sha == "6c368a63c2a15d9e1dc7ff4826996ae87486d45cf591f655916f3de142bf41d9"


def test_replay_out_uses_lf_newlines(tmp_path: Path) -> None:
    out = tmp_path / "replay_transcript.txt"
    rc = btg_main(
        [
            "replay",
            "--script",
            "replays/day1_connected.script",
            "--scenes",
            "game_content/scenes.yaml",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    data = out.read_bytes()
    assert data.endswith(b"\n")
    assert b"\r\n" not in data
