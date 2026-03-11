from __future__ import annotations

from pathlib import Path

from btg.cli import main


def test_list_stories(tmp_path: Path, capsys) -> None:
    stories = tmp_path / "stories"
    (stories / "a").mkdir(parents=True)
    (stories / "b").mkdir(parents=True)

    (stories / "a" / "scenes.yaml").write_text(
        "schema_version: 1\ntitle: A\nstart: intro\nscenes: []\n", encoding="utf-8"
    )
    (stories / "b" / "scenes.yaml").write_text(
        "schema_version: 1\ntitle: B\nstart: s\nscenes: []\n", encoding="utf-8"
    )

    rc = main(["list-stories", "--stories", str(stories)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Stories" in out
    assert "a" in out
    assert "b" in out
