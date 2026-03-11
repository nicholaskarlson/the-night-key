from __future__ import annotations

import hashlib
from pathlib import Path

from .engine import (
    Story,
    load_story_text,
    run,
    scripted_choice_provider,
    transcript_sha256,
)
from .state import GameState


def parse_script_text(text: str) -> list[int]:
    """Parse a replay script: one integer choice index per line.

    - Blank lines are ignored.
    - Lines starting with # are comments.
    """
    out: list[int] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            out.append(int(line))
        except ValueError as e:  # noqa: BLE001
            raise ValueError(f"script:{lineno}: expected an integer, got {line!r}") from e
    return out


def parse_script_file(path: Path) -> list[int]:
    return parse_script_text(path.read_text(encoding="utf-8"))


def story_sha256_from_text(story_text: str) -> str:
    """A stable hash of the story YAML text (LF-normalized)."""
    norm = story_text.replace("\r\n", "\n").replace("\r", "\n")
    h = hashlib.sha256()
    h.update(norm.encode("utf-8"))
    h.update(b"\n")
    return h.hexdigest()


def replay_from_text(
    story_text: str,
    *,
    start_override: str | None = None,
    script: list[int],
    max_steps: int = 400,
) -> tuple[GameState, list[str], str, str]:
    """Replay a story from YAML text.

    Returns: (final_state, transcript_lines, transcript_sha256, story_sha256)
    """
    story: Story = load_story_text(story_text)
    start = start_override.strip() if start_override else story.start

    st, transcript = run(
        story.scenes,
        start,
        GameState(),
        scripted_choice_provider(script),
        max_steps=max_steps,
    )
    return st, transcript, transcript_sha256(transcript), story_sha256_from_text(story_text)


def replay_from_file(
    story_path: Path,
    *,
    start_override: str | None = None,
    script: list[int],
    max_steps: int = 400,
) -> tuple[GameState, list[str], str, str]:
    story_text = story_path.read_text(encoding="utf-8")
    return replay_from_text(
        story_text,
        start_override=start_override,
        script=script,
        max_steps=max_steps,
    )


def load_story_text_default() -> str:
    """Load the default story text (repo-local if present, else packaged)."""
    repo_path = Path("game_content/scenes.yaml")
    if repo_path.exists():
        return repo_path.read_text(encoding="utf-8")

    # packaged
    from importlib import resources  # local import for perf/clarity

    return resources.files("btg").joinpath("data/scenes.yaml").read_text(encoding="utf-8")
