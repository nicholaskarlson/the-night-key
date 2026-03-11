from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from .engine import Choice, Story
from .state import GameState

Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class Issue:
    severity: Severity
    code: str
    message: str


_TEMPLATE_ALLOWED: set[str] = {"day", "energy", "support", "guilt", "warmth", "flags"}
_TEMPLATE_TOKEN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _choice_visible(choice: Choice, state: GameState) -> bool:
    if not state.has_flags(choice.requires_flags):
        return False
    if state.any_flags(choice.forbids_flags):
        return False
    return True


def lint_story(story: Story) -> list[Issue]:
    issues: list[Issue] = []

    declared = set(story.flags)

    used: set[str] = set()
    used_ctx: dict[str, set[str]] = {}

    for sid, scene in story.scenes.items():
        for ch in scene.choices:
            for f in (*ch.requires_flags, *ch.forbids_flags, *ch.sets_flags, *ch.clears_flags):
                if not f:
                    continue
                used.add(f)
                used_ctx.setdefault(f, set()).add(sid)

    # Flags declaration guidance
    if declared:
        unknown = sorted(used - declared)
        if unknown:
            for f in unknown:
                scenes = ", ".join(sorted(used_ctx.get(f, set())))
                issues.append(
                    Issue(
                        severity="error",
                        code="FLAG_UNDECLARED",
                        message=(
                            f"Flag '{f}' is used but not declared in root.flags "
                            f"(seen in scenes: {scenes})."
                        ),
                    )
                )

        unused = sorted(declared - used)
        for f in unused:
            issues.append(
                Issue(
                    severity="warning",
                    code="FLAG_UNUSED",
                    message=f"Flag '{f}' is declared in root.flags but never used.",
                )
            )
    else:
        if used:
            suggestions = ", ".join(sorted(used))
            issues.append(
                Issue(
                    severity="warning",
                    code="FLAGS_MISSING",
                    message=f"root.flags is missing; consider declaring: {suggestions}",
                )
            )

    # Terminal scenes shouldn't have choices (warn only)
    for scene in story.scenes.values():
        if scene.terminal and len(scene.choices) > 0:
            issues.append(
                Issue(
                    severity="warning",
                    code="TERMINAL_HAS_CHOICES",
                    message=f"Scene '{scene.scene_id}' is terminal but has choices.",
                )
            )

    # Start scene must be playable with empty flags
    empty = GameState()
    start_scene = story.scenes[story.start]
    if not start_scene.terminal:
        visible = [ch for ch in start_scene.choices if _choice_visible(ch, empty)]
        if len(visible) == 0:
            issues.append(
                Issue(
                    severity="error",
                    code="START_STUCK",
                    message=(
                        f"Start scene '{story.start}' has no available choices with empty flags."
                    ),
                )
            )

    # Reachability ignoring conditions (useful for authors)
    reachable: set[str] = set()
    stack = [story.start]
    while stack:
        cur = stack.pop()
        if cur in reachable:
            continue
        reachable.add(cur)
        scene = story.scenes[cur]
        for ch in scene.choices:
            if ch.goto not in reachable:
                stack.append(ch.goto)

    for sid in sorted(set(story.scenes.keys()) - reachable):
        issues.append(
            Issue(
                severity="warning",
                code="SCENE_UNREACHABLE",
                message=(
                    f"Scene '{sid}' is unreachable from start '{story.start}' "
                    "(ignoring conditions)."
                ),
            )
        )

    # At least one terminal reachable ignoring conditions (warn)
    if not any(story.scenes[sid].terminal for sid in reachable):
        issues.append(
            Issue(
                severity="warning",
                code="NO_TERMINAL_REACHABLE",
                message="No terminal scenes reachable from start (ignoring conditions).",
            )
        )

    # Tiny text templating checks (book-friendly guardrails)
    for sid, scene in story.scenes.items():
        raw = scene.text

        # Ignore escaped braces.
        s = raw.replace("{{", "").replace("}}", "")

        names = _TEMPLATE_TOKEN.findall(s)
        unknown = sorted({n for n in names if n not in _TEMPLATE_ALLOWED})
        for n in unknown:
            issues.append(
                Issue(
                    severity="warning",
                    code="TEMPLATE_UNKNOWN",
                    message=(
                        f"Scene '{sid}' uses unknown template '{{{n}}}' in text. "
                        "Allowed: {day},{energy},{support},{guilt},{warmth},{flags}. "
                        "Use '{{' and '}}' for literal braces."
                    ),
                )
            )

        # Remove all valid-looking placeholders; if braces remain, it's malformed.
        s2 = _TEMPLATE_TOKEN.sub("", s)
        if "{" in s2 or "}" in s2:
            issues.append(
                Issue(
                    severity="error",
                    code="TEMPLATE_MALFORMED",
                    message=(
                        f"Scene '{sid}' has malformed template braces in text. "
                        "Use '{{' and '}}' for literal braces."
                    ),
                )
            )

    return issues


def has_errors(issues: list[Issue]) -> bool:
    return any(i.severity == "error" for i in issues)
