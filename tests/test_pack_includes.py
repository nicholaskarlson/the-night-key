from __future__ import annotations

from btg.pack import _pack_includes_missing


def test_pack_includes_missing_basic_and_glob() -> None:
    listed = {"scenes.yaml", "scenes/act1.yaml", "scenes/act2.yaml", "README.md"}
    scenes_text = """
schema_version: 1
title: "Pack"
start: a
includes:
  - scenes/act1.yaml
  - scenes/*.extras.yaml
  - scenes/missing.yaml
scenes: []
"""
    missing = _pack_includes_missing(listed, scenes_text)
    assert "scenes/missing.yaml" in missing
    # glob should report pattern if nothing matches among listed
    assert "scenes/*.extras.yaml" in missing
