from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .replay import story_sha256_from_text
from .state import GameState

SAVE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class SaveGame:
    schema_version: int
    story_sha256: str
    scene_id: str
    state: GameState
    script: list[int]
    transcript_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "story_sha256": self.story_sha256,
            "scene_id": self.scene_id,
            "state": {
                "day": self.state.day,
                "energy": self.state.energy,
                "support": self.state.support,
                "guilt": self.state.guilt,
                "warmth": self.state.warmth,
                "flags": dict(self.state.flags),
            },
            "script": list(self.script),
            "transcript_sha256": self.transcript_sha256,
        }


def dumps(save: SaveGame) -> str:
    # Stable JSON for proof-first diffs.
    return json.dumps(save.to_dict(), indent=2, sort_keys=True) + "\n"


def write(path: Path, save: SaveGame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(save), encoding="utf-8")


def _get_obj(o: object) -> dict[str, Any]:
    if not isinstance(o, dict):
        raise ValueError("save: expected a JSON object")
    return o


def _get_str(d: dict[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v:
        raise ValueError(f"save: missing {key}")
    return v


def _get_int(d: dict[str, Any], key: str) -> int:
    v = d.get(key)
    if not isinstance(v, int):
        raise ValueError(f"save: {key} must be int")
    return v


def loads(text: str) -> SaveGame:
    obj = _get_obj(json.loads(text))

    schema_version = obj.get("schema_version")
    if schema_version != SAVE_SCHEMA_VERSION:
        raise ValueError("save: unsupported schema_version")

    story_sha = _get_str(obj, "story_sha256")
    scene_id = _get_str(obj, "scene_id")

    state_obj_any = obj.get("state")
    state_obj = _get_obj(state_obj_any)

    flags_any = state_obj.get("flags", {})
    if not isinstance(flags_any, dict):
        raise ValueError("save: state.flags must be an object")

    flags: dict[str, bool] = {}
    for k, v in flags_any.items():
        if not isinstance(k, str):
            raise ValueError("save: state.flags keys must be strings")
        if not isinstance(v, bool):
            raise ValueError(f"save: state.flags[{k}] must be bool")
        flags[k] = v

    state = GameState(
        day=_get_int(state_obj, "day"),
        energy=_get_int(state_obj, "energy"),
        support=_get_int(state_obj, "support"),
        guilt=_get_int(state_obj, "guilt"),
        warmth=_get_int(state_obj, "warmth"),
        flags=flags,
    )

    script_any = obj.get("script", [])
    if not isinstance(script_any, list):
        raise ValueError("save: script must be a list")

    script: list[int] = []
    for i, v in enumerate(script_any):
        if not isinstance(v, int):
            raise ValueError(f"save: script[{i}] must be int")
        script.append(v)

    transcript_sha = _get_str(obj, "transcript_sha256")

    return SaveGame(
        schema_version=SAVE_SCHEMA_VERSION,
        story_sha256=story_sha,
        scene_id=scene_id,
        state=state,
        script=script,
        transcript_sha256=transcript_sha,
    )


def read(path: Path) -> SaveGame:
    return loads(path.read_text(encoding="utf-8"))


def verify_story_hash(save: SaveGame, story_text: str, *, force: bool = False) -> None:
    cur = story_sha256_from_text(story_text)
    if cur != save.story_sha256 and not force:
        raise ValueError(
            "save: story_sha256 mismatch. The story differs from the one used to create "
            "this save. Use --force to continue anyway."
        )
