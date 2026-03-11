from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .state import GameState


def _format_yaml_error(err: Exception, text: str, source: str | None) -> str:
    """Return a friendlier YAML parse error message.

    Includes source + 1-based line/column (when available) and the offending line.
    """
    src = source or "<yaml>"

    mark = getattr(err, "problem_mark", None)
    if mark is None:
        return f"{src}: YAML parse error: {err}"

    # PyYAML uses 0-based line/column.
    line = int(getattr(mark, "line", 0))
    col = int(getattr(mark, "column", 0))
    line1 = line + 1
    col1 = col + 1

    offending = ""
    try:
        lines = text.splitlines()
        if 0 <= line < len(lines):
            offending_line = lines[line]
            caret = " " * col + "^"
            offending = f"\n\n{offending_line}\n{caret}"
    except Exception:
        pass

    return f"{src}:{line1}:{col1}: YAML parse error: {err}{offending}"


_STATE_FIELDS: set[str] = {"day", "energy", "support", "guilt", "warmth"}

_TEMPLATE_KEYS: set[str] = {"day", "energy", "support", "guilt", "warmth", "flags"}
_TEMPLATE_TOKEN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def render_text(text: str, state: GameState) -> str:
    """Render tiny templates inside scene text.

    Supported placeholders:
      {day} {energy} {support} {guilt} {warmth} {flags}

    Use '{{' and '}}' to escape literal braces.
    """
    if "{" not in text and "}" not in text:
        return text

    # Preserve escaped braces first.
    s = text.replace("{{", "\x00").replace("}}", "\x01")

    def _repl(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in _TEMPLATE_KEYS:
            return m.group(0)  # leave unknown placeholders unchanged
        if key == "flags":
            on = sorted(k for k, v in state.flags.items() if v)
            return ", ".join(on) if on else "(none)"
        val = getattr(state, key, None)
        return str(val) if val is not None else m.group(0)

    s = _TEMPLATE_TOKEN.sub(_repl, s)
    return s.replace("\x00", "{").replace("\x01", "}")


@dataclass(frozen=True)
class StateGate:
    field: str
    op: str
    value: int


@dataclass(frozen=True)
class Choice:
    label: str
    goto: str
    delta: dict[str, int]
    requires_flags: tuple[str, ...] = ()
    forbids_flags: tuple[str, ...] = ()
    sets_flags: tuple[str, ...] = ()
    clears_flags: tuple[str, ...] = ()
    requires_state: tuple[StateGate, ...] = ()
    forbids_state: tuple[StateGate, ...] = ()


@dataclass(frozen=True)
class Scene:
    scene_id: str
    text: str
    choices: tuple[Choice, ...]
    terminal: bool = False


@dataclass(frozen=True)
class Story:
    schema_version: int
    start: str
    title: str | None
    flags: tuple[str, ...]
    scenes: dict[str, Scene]


def _as_str_list(value: Any, *, field: str, ctx: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{ctx}: '{field}' must be a list of strings")
    out: list[str] = []
    for i, v in enumerate(value):
        if not isinstance(v, str):
            raise ValueError(f"{ctx}: '{field}[{i}]' must be a string")
        s = v.strip()
        if not s:
            continue
        out.append(s)
    return out


_GATE_RE = re.compile(r"^\s*(>=|<=|==|!=|>|<)\s*(-?\d+)\s*$")


_OPS: dict[str, Callable[[int, int], bool]] = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def _parse_state_gates(value: Any, *, field: str, ctx: str) -> tuple[StateGate, ...]:
    """Parse mapping of state_field -> comparison string.

    Example:
      requires_state: { energy: ">= 3", guilt: "<= 4" }
    """
    if value is None:
        return ()
    if not isinstance(value, dict):
        raise ValueError(f"{ctx}: '{field}' must be a mapping of state_field -> condition")

    gates: list[StateGate] = []
    for k, raw in value.items():
        if not isinstance(k, str):
            raise ValueError(f"{ctx}: '{field}' keys must be strings (got {type(k).__name__})")
        state_field = k.strip()
        if state_field not in _STATE_FIELDS:
            raise ValueError(f"{ctx}: '{field}' unknown state field '{state_field}'")

        if isinstance(raw, int):
            op = "=="
            num = raw
        elif isinstance(raw, str):
            m = _GATE_RE.match(raw)
            if not m:
                raise ValueError(
                    f"{ctx}: '{field}.{state_field}' must look like '>= 3' (got {raw!r})"
                )
            op = m.group(1)
            num = int(m.group(2))
        else:
            raise ValueError(
                f"{ctx}: '{field}.{state_field}' must be an int or comparison string "
                f"(got {type(raw).__name__})"
            )

        gates.append(StateGate(field=state_field, op=op, value=num))

    # Deterministic ordering independent of YAML map ordering.
    gates.sort(key=lambda g: (g.field, g.op, g.value))
    return tuple(gates)


def _state_gate_true(g: StateGate, state: GameState) -> bool:
    actual = getattr(state, g.field)
    fn = _OPS.get(g.op)
    if fn is None:
        raise ValueError(f"Unknown operator: {g.op}")
    return fn(int(actual), int(g.value))


def _parse_delta(value: Any, *, ctx: str) -> dict[str, int]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{ctx}: 'delta' must be a mapping")
    out: dict[str, int] = {}
    for k, v in value.items():
        if not isinstance(k, str):
            raise ValueError(f"{ctx}: delta keys must be strings")
        key = k.strip()
        if key not in _STATE_FIELDS:
            raise ValueError(f"{ctx}: delta key must be one of {sorted(_STATE_FIELDS)}")
        if not isinstance(v, int):
            raise ValueError(f"{ctx}: delta '{key}' must be an int")
        out[key] = int(v)
    return out


def load_story_text(text: str, source: str | None = None) -> Story:
    """Load a story from YAML text."""
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ValueError(_format_yaml_error(e, text, source)) from e

    schema_version = 0
    title: str | None = None
    start = "day1_arrival"
    flags: tuple[str, ...] = ()
    scenes_raw: Any

    if isinstance(raw, list):
        scenes_raw = raw
    elif isinstance(raw, dict):
        schema_version = int(raw.get("schema_version", 1))
        title_val = raw.get("title", None)
        title = str(title_val).strip() if isinstance(title_val, str) else None
        start_val = raw.get("start", start)
        start = str(start_val).strip() if start_val is not None else start
        flags = tuple(_as_str_list(raw.get("flags", []), field="flags", ctx="root"))
        scenes_raw = raw.get("scenes", None)
    else:
        raise ValueError("root: YAML must be a list of scenes or an object with 'scenes'")

    if not isinstance(scenes_raw, list):
        raise ValueError("root: 'scenes' must be a list")

    scenes: dict[str, Scene] = {}
    for idx, item in enumerate(scenes_raw):
        ctx = f"scene[{idx}]"
        if not isinstance(item, dict):
            raise ValueError(f"{ctx}: scene must be a mapping")

        sid = str(item.get("id", "")).strip()
        scene_text = str(item.get("text", "")).rstrip()
        terminal = bool(item.get("terminal", False))

        if not sid:
            raise ValueError(f"{ctx}: missing 'id'")
        if not scene_text:
            raise ValueError(f"{ctx} ({sid}): missing 'text'")

        choices_val = item.get("choices", []) or []
        if not isinstance(choices_val, list):
            raise ValueError(f"{ctx} ({sid}): 'choices' must be a list")
        if not terminal and len(choices_val) == 0:
            raise ValueError(f"{ctx} ({sid}): non-terminal scenes must have choices")

        choices: list[Choice] = []
        for cidx, c in enumerate(choices_val):
            cctx = f"{ctx} ({sid}) choice[{cidx}]"
            if not isinstance(c, dict):
                raise ValueError(f"{cctx}: choice must be a mapping")

            label = str(c.get("label", "")).strip()
            goto = str(c.get("goto", "")).strip()
            if not label or not goto:
                raise ValueError(f"{cctx}: missing 'label' or 'goto'")

            delta = _parse_delta(c.get("delta", None), ctx=cctx)
            requires_flags = tuple(
                _as_str_list(c.get("requires_flags", []), field="requires_flags", ctx=cctx)
            )
            forbids_flags = tuple(
                _as_str_list(c.get("forbids_flags", []), field="forbids_flags", ctx=cctx)
            )
            requires_state = _parse_state_gates(
                c.get("requires_state", None), field="requires_state", ctx=cctx
            )
            forbids_state = _parse_state_gates(
                c.get("forbids_state", None), field="forbids_state", ctx=cctx
            )
            _raw_sets = c.get("sets_flags", None)
            if _raw_sets is None:
                _raw_sets = c.get("set_flags", [])
            sets_flags = tuple(_as_str_list(_raw_sets, field="sets_flags", ctx=cctx))
            _raw_clears = c.get("clears_flags", None)
            if _raw_clears is None:
                _raw_clears = c.get("clear_flags", [])
            clears_flags = tuple(_as_str_list(_raw_clears, field="clears_flags", ctx=cctx))

            choices.append(
                Choice(
                    label=label,
                    goto=goto,
                    delta=delta,
                    requires_flags=requires_flags,
                    forbids_flags=forbids_flags,
                    sets_flags=sets_flags,
                    clears_flags=clears_flags,
                    requires_state=requires_state,
                    forbids_state=forbids_state,
                )
            )

        if sid in scenes:
            raise ValueError(f"{ctx}: duplicate scene id '{sid}'")
        scenes[sid] = Scene(
            scene_id=sid, text=scene_text, choices=tuple(choices), terminal=terminal
        )

    # validate gotos + start
    for s in scenes.values():
        for ch in s.choices:
            if ch.goto not in scenes:
                raise ValueError(
                    f"scene '{s.scene_id}' choice '{ch.label}' goto missing: {ch.goto}"
                )

    if start not in scenes:
        raise ValueError(f"root: start scene '{start}' not found")

    return Story(
        schema_version=schema_version,
        start=start,
        title=title,
        flags=flags,
        scenes=scenes,
    )


def load_story(path: Path) -> Story:
    """Load a story from a filesystem path."""
    return load_story_text(path.read_text(encoding="utf-8"), source=str(path))


def load_scenes_text(text: str) -> dict[str, Scene]:
    """Backward-compatible: load scenes dict from YAML text."""
    return load_story_text(text).scenes


def load_scenes(path: Path) -> dict[str, Scene]:
    """Backward-compatible: load scenes dict from a filesystem path."""
    return load_story(path).scenes


TranscriptLine = str
ChoiceProvider = Callable[[Scene, GameState], int]


def _apply_delta(state: GameState, delta: dict[str, int]) -> GameState:
    if not delta:
        return state

    data = {
        "day": state.day,
        "energy": state.energy,
        "support": state.support,
        "guilt": state.guilt,
        "warmth": state.warmth,
    }
    for k, dv in delta.items():
        if k not in data:
            raise KeyError(f"Unknown state field in delta: {k}")
        data[k] = data[k] + dv

    # clamp to reasonable bounds
    data["energy"] = max(0, min(10, data["energy"]))
    data["support"] = max(0, min(10, data["support"]))
    data["guilt"] = max(0, min(10, data["guilt"]))
    data["warmth"] = max(0, min(10, data["warmth"]))
    return state.with_updates(**data)


def _choice_available(choice: Choice, state: GameState) -> bool:
    if not state.has_flags(choice.requires_flags):
        return False
    if state.any_flags(choice.forbids_flags):
        return False

    if choice.requires_state:
        if not all(_state_gate_true(g, state) for g in choice.requires_state):
            return False
    if choice.forbids_state:
        if any(_state_gate_true(g, state) for g in choice.forbids_state):
            return False

    return True


def _filter_choices(scene: Scene, state: GameState) -> tuple[Choice, ...]:
    return tuple(ch for ch in scene.choices if _choice_available(ch, state))


def available_choices(scene: Scene, state: GameState) -> tuple[Choice, ...]:
    """Public helper: choices available given the current flags/state."""
    return _filter_choices(scene, state)


def apply_choice(
    scenes: dict[str, Scene],
    cur: str,
    state: GameState,
    choice_index: int,
) -> tuple[str, GameState, list[str]]:
    """Apply one choice and return (next_scene_id, new_state, transcript_lines).

    `choice_index` is relative to the *available* (filtered) choices for this scene,
    matching what the player sees and what replay scripts encode.
    """
    scene = scenes[cur]
    transcript: list[str] = [f"[{scene.scene_id}]"]
    transcript.extend(render_text(scene.text, state).splitlines())

    if scene.terminal:
        transcript.append("[end]")
        return cur, state, transcript

    available = _filter_choices(scene, state)
    if len(available) == 0:
        raise RuntimeError(f"No available choices for scene '{scene.scene_id}'")

    if not (0 <= choice_index < len(available)):
        raise ValueError(f"Choice index out of range: {choice_index}")

    ch = available[choice_index]
    transcript.append(f"> {ch.label}")

    st = _apply_delta(state, ch.delta)
    st = st.with_flags(set_flags=ch.sets_flags, clear_flags=ch.clears_flags)
    return ch.goto, st, transcript


def run(
    scenes: dict[str, Scene],
    start: str,
    state: GameState | None,
    choose: ChoiceProvider,
    max_steps: int = 200,
) -> tuple[GameState, list[TranscriptLine]]:
    st: GameState
    if state is None:
        st = GameState()
    else:
        st = state
    cur = start
    transcript: list[TranscriptLine] = []

    for _ in range(max_steps):
        scene = scenes[cur]
        transcript.append(f"[{scene.scene_id}]")
        transcript.extend(render_text(scene.text, st).splitlines())

        if scene.terminal:
            transcript.append("[end]")
            return st, transcript

        available = _filter_choices(scene, st)
        if len(available) == 0:
            raise RuntimeError(f"No available choices for scene '{scene.scene_id}'")

        play_scene = Scene(
            scene_id=scene.scene_id,
            text=render_text(scene.text, st),
            choices=available,
            terminal=False,
        )

        idx = choose(play_scene, st)
        if not (0 <= idx < len(play_scene.choices)):
            raise ValueError(f"Choice index out of range: {idx}")

        ch = play_scene.choices[idx]
        transcript.append(f"> {ch.label}")

        st = _apply_delta(st, ch.delta)
        st = st.with_flags(set_flags=ch.sets_flags, clear_flags=ch.clears_flags)
        cur = ch.goto

    raise RuntimeError("Exceeded max_steps; possible loop")


def scripted_choice_provider(script: Sequence[int]) -> ChoiceProvider:
    it = iter(script)

    def _choose(scene: Scene, state: GameState) -> int:
        _ = scene
        _ = state
        try:
            return int(next(it))
        except StopIteration as e:
            raise RuntimeError("Script ended before game ended") from e

    return _choose


def transcript_sha256(lines: Sequence[str]) -> str:
    h = hashlib.sha256()
    for line in lines:
        h.update(line.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()
