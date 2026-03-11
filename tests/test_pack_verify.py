from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest

from btg.init_story import init_story
from btg.pack import build_pack, unpack_pack, verify_pack


def test_verify_pack_ok(tmp_path: Path) -> None:
    story_dir = tmp_path / "story"
    init_story(story_dir, title="Verify Test")
    pack_path = tmp_path / "story.pack.zip"
    build_pack(story_dir, pack_path, force=True)

    res = verify_pack(pack_path)
    assert res.ok
    assert res.errors == []


def test_verify_pack_detects_tamper(tmp_path: Path) -> None:
    story_dir = tmp_path / "story"
    init_story(story_dir, title="Verify Test")
    pack_path = tmp_path / "story.pack.zip"
    build_pack(story_dir, pack_path, force=True)

    tampered = tmp_path / "tampered.pack.zip"
    with ZipFile(pack_path, "r") as zin, ZipFile(tampered, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "scenes.yaml":
                data = data + b"\n# tampered\n"
            zi = ZipInfo(info.filename, date_time=(1980, 1, 1, 0, 0, 0))
            zi.compress_type = ZIP_DEFLATED
            zi.external_attr = info.external_attr
            zout.writestr(zi, data)

    res = verify_pack(tampered)
    assert not res.ok
    assert any("sha mismatch: scenes.yaml" in e for e in res.errors)


def test_unpack_rejects_zip_slip(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pack.zip"
    with ZipFile(bad, "w") as z:
        zi = ZipInfo("../evil.txt", date_time=(1980, 1, 1, 0, 0, 0))
        zi.compress_type = ZIP_DEFLATED
        zi.external_attr = (0o644 & 0xFFFF) << 16
        z.writestr(zi, b"nope\n")

        zi2 = ZipInfo("pack_manifest.json", date_time=(1980, 1, 1, 0, 0, 0))
        zi2.compress_type = ZIP_DEFLATED
        zi2.external_attr = (0o644 & 0xFFFF) << 16
        z.writestr(zi2, b"{}\n")

        zi3 = ZipInfo("manifest.sha256", date_time=(1980, 1, 1, 0, 0, 0))
        zi3.compress_type = ZIP_DEFLATED
        zi3.external_attr = (0o644 & 0xFFFF) << 16
        z.writestr(zi3, b"")

    out_dir = tmp_path / "out"
    with pytest.raises(ValueError):
        unpack_pack(bad, out_dir, force=True)


def test_unpack_rejects_backslash_traversal(tmp_path: Path) -> None:
    bad = tmp_path / "bad_backslash.pack.zip"
    with ZipFile(bad, "w") as z:
        zi = ZipInfo("..\\evil.txt", date_time=(1980, 1, 1, 0, 0, 0))
        zi.compress_type = ZIP_DEFLATED
        zi.external_attr = (0o644 & 0xFFFF) << 16
        z.writestr(zi, b"nope\n")

        zi2 = ZipInfo("pack_manifest.json", date_time=(1980, 1, 1, 0, 0, 0))
        zi2.compress_type = ZIP_DEFLATED
        zi2.external_attr = (0o644 & 0xFFFF) << 16
        z.writestr(zi2, b"{}\n")

        zi3 = ZipInfo("manifest.sha256", date_time=(1980, 1, 1, 0, 0, 0))
        zi3.compress_type = ZIP_DEFLATED
        zi3.external_attr = (0o644 & 0xFFFF) << 16
        z.writestr(zi3, b"")

    out_dir = tmp_path / "out"
    with pytest.raises(ValueError):
        unpack_pack(bad, out_dir, force=True)
