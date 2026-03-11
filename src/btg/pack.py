from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import yaml

from .engine import Story, load_story

PACK_SCHEMA_VERSION = 1
ZIP_FIXED_DATETIME = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class PackResult:
    pack_path: Path
    files_written: int
    manifest: dict[str, Any]


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    errors: list[str]
    manifest: dict[str, Any] | None


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _stable_json(obj: dict[str, Any]) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _iter_story_files(story_dir: Path) -> list[Path]:
    exclude_names = {".DS_Store", "Thumbs.db"}
    files: list[Path] = []
    for p in story_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.name in exclude_names:
            continue
        if ".venv" in p.parts or ".git" in p.parts or "__pycache__" in p.parts:
            continue
        files.append(p)
    files.sort(key=lambda x: x.relative_to(story_dir).as_posix())
    return files


def _zip_write_bytes(z: ZipFile, arcname: str, data: bytes) -> None:
    zi = ZipInfo(filename=arcname, date_time=ZIP_FIXED_DATETIME)
    zi.compress_type = ZIP_DEFLATED
    zi.external_attr = (0o644 & 0xFFFF) << 16
    z.writestr(zi, data)


def _zip_write_file(z: ZipFile, arcname: str, path: Path) -> None:
    _zip_write_bytes(z, arcname, path.read_bytes())


def _story_metadata(story: Story) -> dict[str, Any]:
    scenes_count = len(story.scenes)
    choices_count = sum(len(s.choices) for s in story.scenes.values())
    return {
        "schema_version": PACK_SCHEMA_VERSION,
        "title": story.title,
        "start": story.start,
        "flags": list(story.flags),
        "scenes_count": scenes_count,
        "choices_count": choices_count,
    }


def build_pack(story_dir: Path, out_path: Path, *, force: bool = False) -> PackResult:
    story_dir = story_dir.expanduser().resolve()
    out_path = out_path.expanduser().resolve()

    scenes_path = story_dir / "scenes.yaml"
    if not scenes_path.exists():
        raise ValueError(f"Missing required file: {scenes_path}")

    if out_path.exists() and not force:
        raise ValueError(f"Refusing to overwrite existing file: {out_path}")

    story = load_story(scenes_path)
    files = _iter_story_files(story_dir)

    payload: list[dict[str, Any]] = []
    payload_hashes: dict[str, str] = {}
    for f in files:
        rel = f.relative_to(story_dir).as_posix()
        sha = _sha256_file(f)
        payload_hashes[rel] = sha
        payload.append({"path": rel, "sha256": sha, "bytes": f.stat().st_size})

    manifest: dict[str, Any] = {**_story_metadata(story), "root": story_dir.name, "files": payload}

    manifest_bytes = _stable_json(manifest)
    manifest_sha = _sha256_bytes(manifest_bytes)

    sha_lines: list[str] = [f"{manifest_sha}  pack_manifest.json"]
    for rel in sorted(payload_hashes.keys()):
        sha_lines.append(f"{payload_hashes[rel]}  {rel}")
    sha_bytes = ("\n".join(sha_lines) + "\n").encode("utf-8")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out_path, "w") as z:
        _zip_write_bytes(z, "pack_manifest.json", manifest_bytes)
        _zip_write_bytes(z, "manifest.sha256", sha_bytes)
        for f in files:
            rel = f.relative_to(story_dir).as_posix()
            _zip_write_file(z, rel, f)

    return PackResult(pack_path=out_path, files_written=len(files) + 2, manifest=manifest)


def _pack_includes_missing(listed: set[str], scenes_text: str) -> list[str]:
    """Return include entries from scenes.yaml that are not satisfied by the pack manifest.

    We treat the manifest's `files[].path` list as the authoritative payload.
    Glob patterns are matched against those paths deterministically.
    """
    try:
        raw = yaml.safe_load(scenes_text)
    except Exception:
        return []

    if not isinstance(raw, dict):
        return []

    includes = raw.get("includes", [])
    if includes is None:
        includes = []
    if not isinstance(includes, list):
        return []

    def _has_glob(s: str) -> bool:
        return any(ch in s for ch in ["*", "?", "["])

    missing: list[str] = []
    for inc in includes:
        if not isinstance(inc, str):
            continue
        pat = inc.strip()
        if not pat:
            continue

        if _has_glob(pat):
            matches = sorted([p for p in listed if fnmatch.fnmatch(p, pat)])
            if not matches:
                missing.append(pat)
        else:
            if pat not in listed:
                missing.append(pat)

    # de-dup preserve order
    seen: set[str] = set()
    out: list[str] = []
    for m in missing:
        if m in seen:
            continue
        seen.add(m)
        out.append(m)
    return out


def read_pack_scenes_text(pack_path: Path) -> str:
    pack_path = pack_path.expanduser().resolve()
    with ZipFile(pack_path, "r") as z:
        try:
            b = z.read("scenes.yaml")
        except KeyError as e:
            raise ValueError("pack: missing scenes.yaml") from e
    return b.decode("utf-8")


def _is_hex_sha256(s: str) -> bool:
    if len(s) != 64:
        return False
    try:
        int(s, 16)
    except ValueError:
        return False
    return True


def _schema_error(errors: list[str], msg: str) -> None:
    errors.append("schema: " + msg)


def _validate_pack_manifest(obj: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(obj, dict):
        _schema_error(errors, "pack_manifest.json must be a JSON object")
        return None, errors

    def req_str(k: str) -> None:
        v = obj.get(k)
        if not isinstance(v, str) or not v:
            _schema_error(errors, f"missing or invalid '{k}'")

    def req_int(k: str) -> None:
        v = obj.get(k)
        if not isinstance(v, int) or v < 0:
            _schema_error(errors, f"missing or invalid '{k}' (int >= 0)")

    if obj.get("schema_version") != PACK_SCHEMA_VERSION:
        _schema_error(errors, "unsupported schema_version")

    req_str("title")
    req_str("start")
    req_str("root")
    req_int("scenes_count")
    req_int("choices_count")

    flags = obj.get("flags")
    if not isinstance(flags, list) or any(not isinstance(x, str) or not x for x in flags):
        _schema_error(errors, "flags must be a list of non-empty strings")

    files = obj.get("files")
    if not isinstance(files, list):
        _schema_error(errors, "files must be a list")
        files = []

    seen_paths: set[str] = set()
    for i, item in enumerate(files):
        if not isinstance(item, dict):
            _schema_error(errors, f"files[{i}] must be an object")
            continue
        p = item.get("path")
        sha = item.get("sha256")
        b = item.get("bytes")

        if not isinstance(p, str) or not p:
            _schema_error(errors, f"files[{i}].path must be a non-empty string")
            continue
        pp = PurePosixPath(p)
        if pp.is_absolute() or ".." in pp.parts or "\\" in p or p.startswith("\\") or ":" in p:
            _schema_error(errors, f"files[{i}].path is unsafe: {p!r}")
        if p in seen_paths:
            _schema_error(errors, f"duplicate path in files: {p!r}")
        seen_paths.add(p)

        if not isinstance(sha, str) or not _is_hex_sha256(sha):
            _schema_error(errors, f"files[{i}].sha256 must be 64 hex chars")
        if not isinstance(b, int) or b < 0:
            _schema_error(errors, f"files[{i}].bytes must be int >= 0")

    # manifest is dict[str, Any] at runtime
    return obj, errors


def _parse_manifest_sha256(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    mapping: dict[str, str] = {}
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            errors.append(f"manifest.sha256:{lineno}: invalid line")
            continue
        sha = parts[0].strip()
        path = parts[-1].strip()
        if not _is_hex_sha256(sha):
            errors.append(f"manifest.sha256:{lineno}: invalid sha256")
            continue
        mapping[path] = sha
    return mapping, errors


def verify_pack(pack_path: Path) -> VerifyResult:
    pack_path = pack_path.expanduser().resolve()
    errors: list[str] = []
    manifest: dict[str, Any] | None = None

    try:
        with ZipFile(pack_path, "r") as z:
            names = set(z.namelist())
            if "pack_manifest.json" not in names:
                errors.append("pack: missing pack_manifest.json")
                return VerifyResult(ok=False, errors=errors, manifest=None)
            if "manifest.sha256" not in names:
                errors.append("pack: missing manifest.sha256")
                return VerifyResult(ok=False, errors=errors, manifest=None)

            manifest_obj = json.loads(z.read("pack_manifest.json").decode("utf-8"))
            manifest, schema_errors = _validate_pack_manifest(manifest_obj)
            errors.extend(schema_errors)

            sha_text = z.read("manifest.sha256").decode("utf-8")
            sha_map, sha_errors = _parse_manifest_sha256(sha_text)
            errors.extend(sha_errors)

            pm_sha_expected = sha_map.get("pack_manifest.json")
            pm_sha_actual = _sha256_bytes(z.read("pack_manifest.json"))
            if pm_sha_expected is None:
                errors.append("manifest.sha256: missing entry for pack_manifest.json")
            elif pm_sha_expected != pm_sha_actual:
                errors.append("manifest.sha256: pack_manifest.json sha mismatch")

            if manifest is not None:
                listed: list[str] = []
                for f in manifest.get("files", []):
                    if isinstance(f, dict) and isinstance(f.get("path"), str):
                        listed.append(f["path"])

                for rel in listed:
                    if rel not in names:
                        errors.append(f"pack: missing file in zip: {rel}")
                        continue
                    expected = sha_map.get(rel)
                    actual = _sha256_bytes(z.read(rel))
                    if expected is None:
                        errors.append(f"manifest.sha256: missing entry for {rel}")
                    elif expected != actual:
                        errors.append(f"sha mismatch: {rel}")

                # Multi-file story support: ensure `includes:` entries are
                # satisfied by the pack payload.
                if "scenes.yaml" in names:
                    try:
                        scenes_text = z.read("scenes.yaml").decode("utf-8")
                        missing = _pack_includes_missing(set(listed), scenes_text)
                        for miss in missing:
                            errors.append(f"pack: includes missing from payload: {miss}")
                    except Exception:
                        pass

                allowed = set(listed) | {"pack_manifest.json", "manifest.sha256"}
                extras = sorted(n for n in names if n not in allowed and not n.endswith("/"))
                if extras:
                    errors.append("pack: unexpected files present: " + ", ".join(extras))

    except Exception as e:  # noqa: BLE001
        errors.append(f"pack: {e}")
        return VerifyResult(ok=False, errors=errors, manifest=None)

    return VerifyResult(ok=(len(errors) == 0), errors=errors, manifest=manifest)


def read_pack_manifest(pack_path: Path) -> dict[str, Any]:
    pack_path = pack_path.expanduser().resolve()
    with ZipFile(pack_path, "r") as z:
        obj = json.loads(z.read("pack_manifest.json").decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("pack_manifest.json must be a JSON object")
    return obj


def pack_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": manifest.get("schema_version"),
        "title": manifest.get("title"),
        "start": manifest.get("start"),
        "scenes_count": manifest.get("scenes_count"),
        "choices_count": manifest.get("choices_count"),
        "flags": manifest.get("flags"),
        "root": manifest.get("root"),
    }


def _is_symlink(zip_info: ZipInfo) -> bool:
    mode = (zip_info.external_attr >> 16) & 0xFFFF
    return (mode & 0o170000) == 0o120000


def _safe_member_path(out_dir: Path, name: str) -> Path:
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or "\\" in name or name.startswith("\\") or ":" in name:
        raise ValueError(f"pack: unsafe path in zip: {name!r}")

    target = (out_dir / Path(*p.parts)).resolve()
    out_root = out_dir.resolve()
    try:
        target.relative_to(out_root)
    except ValueError as e:
        raise ValueError(f"pack: unsafe path in zip: {name!r}") from e
    return target


def unpack_pack(pack_path: Path, out_dir: Path, *, force: bool = False) -> Path:
    pack_path = pack_path.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()

    if out_dir.exists() and any(out_dir.iterdir()) and not force:
        raise ValueError(f"Refusing to overwrite non-empty directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(pack_path, "r") as z:
        for info in z.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            if _is_symlink(info):
                raise ValueError(f"pack: refusing to extract symlink: {name!r}")
            target = _safe_member_path(out_dir, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(name))

    return out_dir
