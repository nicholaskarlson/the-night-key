from __future__ import annotations

import hashlib
from pathlib import Path

from btg.gallery import build_gallery
from btg.init_story import init_story


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_gallery_deterministic(tmp_path: Path) -> None:
    stories = tmp_path / "stories"
    init_story(stories / "a", title="A Story")
    init_story(stories / "b", title="B Story")

    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"

    idx1 = build_gallery(stories, out1)
    idx2 = build_gallery(stories, out2)

    assert _sha256_file(idx1) == _sha256_file(idx2)
    assert _sha256_file(out1 / "a.pack.zip") == _sha256_file(out2 / "a.pack.zip")
    assert _sha256_file(out1 / "b.pack.zip") == _sha256_file(out2 / "b.pack.zip")
