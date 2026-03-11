from __future__ import annotations

from pathlib import Path

from btg.cli import main


def test_cli_lint_accepts_positional_scenes(tmp_path: Path) -> None:
    scenes = tmp_path / "scenes.yaml"
    scenes.write_text(
        """
schema_version: 1
title: "Positional"
start: s1
scenes:
  - id: s1
    terminal: true
    text: "done"
""".lstrip(),
        encoding="utf-8",
    )

    rc = main(["lint", "--strict", str(scenes)])
    assert rc == 0


def test_cli_replay_accepts_positional_scenes(tmp_path: Path) -> None:
    scenes = tmp_path / "scenes.yaml"
    scenes.write_text(
        """
schema_version: 1
title: "Replay Positional"
start: s1
scenes:
  - id: s1
    text: "start"
    choices:
      - label: "to end"
        goto: s2
  - id: s2
    terminal: true
    text: "end"
""".lstrip(),
        encoding="utf-8",
    )

    script = tmp_path / "script.txt"
    script.write_text("0\n", encoding="utf-8")

    rc = main(["replay", "--script", str(script), str(scenes)])
    assert rc == 0
