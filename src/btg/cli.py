from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .engine import (
    Scene,
    Story,
    apply_choice,
    available_choices,
    load_story,
    load_story_text,
    render_text,
    run,
)
from .init_story import init_story
from .lint import has_errors, lint_story
from .pack import (
    PackResult,
    VerifyResult,
    build_pack,
    pack_summary,
    read_pack_manifest,
    read_pack_story_text,
    unpack_pack,
    verify_pack,
)
from .replay import (
    load_story_text_default,
    parse_script_file,
    replay_from_text,
    story_sha256_from_text,
    transcript_sha256,
)
from .savegame import SaveGame, verify_story_hash
from .savegame import read as read_save
from .savegame import write as write_save
from .state import GameState


def _prompt_choice(console: Console, n: int) -> int:
    while True:
        raw = console.input(f"[bold]Choose[/bold] (1..{n}): ").strip()
        if raw.isdigit():
            v = int(raw)
            if 1 <= v <= n:
                return v - 1
        console.print("[red]Invalid choice.[/red]")


def _print_state(console: Console, st: GameState, title: str) -> None:
    flags_on = sorted([k for k, v in st.flags.items() if v])
    flags_str = ", ".join(flags_on) if flags_on else "(none)"
    console.print()
    console.print(
        Panel.fit(
            f"Day={st.day}  Energy={st.energy}  Support={st.support}  "
            f"Guilt={st.guilt}  Warmth={st.warmth}\n"
            f"Flags: {flags_str}",
            title=title,
        )
    )


def _load_story_from_source(scenes_path: str, pack_path: str, story_name: str) -> tuple[str, Story]:
    sources = [("scenes", scenes_path), ("pack", pack_path), ("story", story_name)]
    chosen = [k for k, v in sources if v]
    if len(chosen) > 1:
        raise ValueError("Choose only one: --scenes, --pack, or --story")

    if scenes_path:
        p = Path(scenes_path)
        text = p.read_text(encoding="utf-8")
        return text, load_story(p)

    if pack_path:
        text = read_pack_story_text(Path(pack_path))
        return text, load_story_text(text, source=f"pack:{pack_path}")

    if story_name:
        p = Path("stories") / story_name / "scenes.yaml"
        if not p.exists():
            raise FileNotFoundError(f"Story not found: {p}")
        text = p.read_text(encoding="utf-8")
        return text, load_story(p)

    text = load_story_text_default()
    return text, load_story_text(text, source="game_content/scenes.yaml")


def _slug_from_pack_path(pack_path: Path) -> str:
    name = pack_path.name
    if name.endswith(".pack.zip"):
        return name[: -len(".pack.zip")]
    return pack_path.stem


def _reconstruct_prefix(
    scenes: dict[str, Scene],
    start: str,
    script: list[int],
) -> tuple[str, GameState, list[str]]:
    cur = start
    st = GameState()
    transcript_lines: list[str] = []
    for idx in script:
        nxt, st, step_lines = apply_choice(scenes, cur, st, idx)
        transcript_lines.extend(step_lines)
        cur = nxt
        if scenes[cur].terminal:
            continue
    return cur, st, transcript_lines


def _interactive_play(
    console: Console,
    scenes: dict[str, Scene],
    *,
    start: str,
    story_text: str,
    save_path: Path | None,
    initial_scene: str | None = None,
    initial_state: GameState | None = None,
    initial_script: list[int] | None = None,
    initial_transcript: list[str] | None = None,
) -> int:
    cur = initial_scene or start
    st = initial_state or GameState()
    script: list[int] = list(initial_script or [])
    transcript_lines: list[str] = list(initial_transcript or [])
    story_sha = story_sha256_from_text(story_text)

    while True:
        scene = scenes[cur]
        console.print()
        console.print(Panel.fit(render_text(scene.text, st), title=scene.scene_id))

        if scene.terminal:
            transcript_lines.append(f"[{scene.scene_id}]")
            transcript_lines.extend(render_text(scene.text, st).splitlines())
            transcript_lines.append("[end]")
            break

        avail = available_choices(scene, st)
        if not avail:
            console.print("[red]ERROR[/red] No available choices from this scene.")
            return 2

        for i, ch in enumerate(avail, start=1):
            console.print(f"  {i}. {ch.label}")

        idx = _prompt_choice(console, len(avail))
        script.append(idx)

        nxt, st, step_lines = apply_choice(scenes, cur, st, idx)
        transcript_lines.extend(step_lines)
        cur = nxt

        if save_path is not None:
            save = SaveGame(
                schema_version=1,
                story_sha256=story_sha,
                scene_id=cur,
                state=st,
                script=script,
                transcript_sha256=transcript_sha256(transcript_lines),
            )
            write_save(save_path, save)

    _print_state(console, st, "Final State")

    if save_path is not None:
        save = SaveGame(
            schema_version=1,
            story_sha256=story_sha,
            scene_id=cur,
            state=st,
            script=script,
            transcript_sha256=transcript_sha256(transcript_lines),
        )
        write_save(save_path, save)

    return 0


def _print_pack_summary(console: Console, manifest: dict[str, Any]) -> None:
    s = pack_summary(manifest)
    flags_list: list[str] = []
    flags_any = s.get("flags")
    if isinstance(flags_any, list):
        flags_list = [x for x in flags_any if isinstance(x, str)]
    console.print(f"title: {s.get('title')}")
    console.print(f"start: {s.get('start')}")
    console.print(f"scenes: {s.get('scenes_count')}")
    console.print(f"choices: {s.get('choices_count')}")
    console.print(f"flags: {', '.join(flags_list)}")
    console.print(f"root: {s.get('root')}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="btg", description="Story game engine (proof-first).")
    sub = p.add_subparsers(dest="cmd", required=True)

    play = sub.add_parser("play", help="Play the game.")
    play.add_argument("--scenes", default="", help="Path to scenes.yaml.")
    play.add_argument("--pack", default="", help="Path to a story pack zip.")
    play.add_argument("--story", default="", help="Story name under stories/ (e.g., starter).")
    play.add_argument("--start", default="", help="Start scene id override.")
    play.add_argument("--save", default="", help="Optional autosave JSON path.")

    resume = sub.add_parser("resume", help="Resume from a savegame JSON.")
    resume.add_argument("--save", required=True, help="Path to a savegame JSON.")
    resume.add_argument("--scenes", default="", help="Optional story YAML path override.")
    resume.add_argument("--pack", default="", help="Optional story pack zip override.")
    resume.add_argument("--story", default="", help="Story name under stories/ (e.g., starter).")
    resume.add_argument("--force", action="store_true", help="Ignore story hash / prefix mismatch.")

    lint = sub.add_parser("lint", help="Validate a story file for authoring errors.")
    lint.add_argument("--scenes", default="", help="Path to scenes.yaml.")
    lint.add_argument("--pack", default="", help="Path to a story pack zip.")
    lint.add_argument("--story", default="", help="Story name under stories/ (e.g., starter).")
    lint.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors (non-zero exit)."
    )

    replay = sub.add_parser("replay", help="Run a deterministic replay from a script file.")
    replay.add_argument(
        "--script", required=True, help="Path to a replay script (one integer per line)."
    )
    replay.add_argument("--scenes", default="", help="Path to scenes.yaml.")
    replay.add_argument("--pack", default="", help="Path to a story pack zip.")
    replay.add_argument("--story", default="", help="Story name under stories/ (e.g., starter).")
    replay.add_argument("--start", default="", help="Start scene id override (optional).")
    replay.add_argument("--out", default="", help="Optional path to write transcript.")
    replay.add_argument(
        "--expect-sha", default="", help="Exit non-zero unless transcript sha matches."
    )

    initp = sub.add_parser("init-story", help="Create a starter story folder.")
    initp.add_argument("path", help="Directory to create (or reuse).")
    initp.add_argument("--title", default="My Story", help="Title to write into scenes.yaml.")
    initp.add_argument("--force", action="store_true", help="Overwrite existing files.")

    lspj = sub.add_parser("list-stories", help="List story projects under stories/.")
    lspj.add_argument(
        "--stories",
        default="stories",
        help="Stories source folder (default: stories/).",
    )

    packp = sub.add_parser("pack-story", help="Build a deterministic story pack zip from a folder.")
    packp.add_argument(
        "story_dir", help="Story folder containing scenes.yaml (and optional README/assets)."
    )
    packp.add_argument("--out", required=True, help="Output zip path.")
    packp.add_argument("--force", action="store_true", help="Overwrite existing output zip.")

    unpackp = sub.add_parser("unpack-story", help="Unpack a story pack zip into a folder.")
    unpackp.add_argument("pack", help="Path to story pack zip.")
    unpackp.add_argument("--out", required=True, help="Output directory.")
    unpackp.add_argument("--force", action="store_true", help="Allow non-empty output directory.")

    verifyp = sub.add_parser(
        "verify-pack", help="Verify a story pack zip (schema + sha256 manifest)."
    )
    verifyp.add_argument("pack", help="Path to story pack zip.")

    lsp = sub.add_parser("ls-pack", help="Print a short summary of a story pack zip.")
    lsp.add_argument("pack", help="Path to story pack zip.")

    args = p.parse_args(argv)
    console = Console()

    if args.cmd == "list-stories":
        stories_root = Path(str(args.stories))
        if not stories_root.exists():
            console.print(f"[red]ERROR[/red] Stories folder not found: {stories_root}")
            return 2

        items: list[tuple[str, str, str]] = []
        for d in sorted([p for p in stories_root.iterdir() if p.is_dir()], key=lambda p: p.name):
            scenes = d / "scenes.yaml"
            if not scenes.exists():
                continue
            try:
                story_obj = load_story(scenes)
                title = story_obj.title or ""
                start = story_obj.start or ""
            except Exception:
                title = ""
                start = ""
            items.append((d.name, title, start))

        if not items:
            console.print("No stories found.")
            return 0

        t = Table(title="Stories")
        t.add_column("name", style="bold")
        t.add_column("title")
        t.add_column("start")
        for name, title, start in items:
            t.add_row(name, title, start)
        console.print(t)
        return 0

    if args.cmd == "init-story":
        try:
            out_dir = Path(args.path)
            result = init_story(out_dir, title=str(args.title), force=bool(args.force))
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]ERROR[/red] {e}")
            return 2
        console.print(f"[green]OK[/green] Wrote story template to: {result.directory}")
        # If the story lives under stories/<name>, suggest the --story shorthand.
        try:
            rel = result.scenes_path.relative_to(Path("stories"))
            story_name = rel.parts[0] if rel.parts else ""
        except Exception:
            story_name = ""
        if story_name:
            console.print(f"Next: btg play --story {story_name}")
            console.print(f"Then: btg lint --strict --story {story_name}")
        else:
            console.print(f"Next: btg play --scenes {result.scenes_path}")
            return 0

    if args.cmd == "pack-story":
        try:
            pres: PackResult = build_pack(
                Path(args.story_dir), Path(args.out), force=bool(args.force)
            )
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]ERROR[/red] {e}")
            return 2
        console.print(f"[green]OK[/green] Wrote pack: {pres.pack_path}")
        console.print(f"Files: {pres.files_written}")
        console.print("Next: btg play --pack " + str(pres.pack_path))
        return 0

    if args.cmd == "unpack-story":
        try:
            out_dir = unpack_pack(Path(args.pack), Path(args.out), force=bool(args.force))
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]ERROR[/red] {e}")
            return 2
        console.print(f"[green]OK[/green] Unpacked to: {out_dir}")
        console.print(f"Next: btg play --scenes {out_dir / 'scenes.yaml'}")
        return 0

    if args.cmd == "ls-pack":
        try:
            manifest = read_pack_manifest(Path(args.pack))
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]ERROR[/red] {e}")
            return 2
        _print_pack_summary(console, manifest)
        return 0

    if args.cmd == "verify-pack":
        vres: VerifyResult = verify_pack(Path(args.pack))
        if vres.ok and vres.manifest is not None:
            console.print("[green]OK[/green] Pack verified.")
            _print_pack_summary(console, vres.manifest)
            return 0
        console.print("[red]ERROR[/red] Pack verification failed.")
        for err in vres.errors:
            console.print(f"- {err}")
        return 1

    if args.cmd == "play":
        try:
            story_text, story = _load_story_from_source(args.scenes, args.pack, args.story)
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]ERROR[/red] {e}")
            return 2

        start = args.start.strip() or story.start
        save_path = Path(args.save) if args.save.strip() else None

        if save_path is None:

            def choose(scene: Scene, state: GameState) -> int:
                console.print()
                console.print(Panel.fit(render_text(scene.text, state), title=scene.scene_id))
                avail = available_choices(scene, state)
                for i, ch in enumerate(avail, start=1):
                    console.print(f"  {i}. {ch.label}")
                return _prompt_choice(console, len(avail))

            st1, _ = run(story.scenes, start, GameState(), choose, max_steps=400)
            _print_state(console, st1, "Final State")
            return 0

        return _interactive_play(
            console, story.scenes, start=start, story_text=story_text, save_path=save_path
        )

    if args.cmd == "resume":
        save_path = Path(args.save)
        save = read_save(save_path)

        try:
            story_text, story = _load_story_from_source(args.scenes, args.pack, args.story)
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]ERROR[/red] {e}")
            return 2

        verify_story_hash(save, story_text, force=bool(args.force))

        cur, st, transcript_lines = _reconstruct_prefix(story.scenes, story.start, save.script)

        if not bool(args.force):
            ok_scene = cur == save.scene_id
            ok_state = st == save.state
            ok_transcript = transcript_sha256(transcript_lines) == save.transcript_sha256
            if not (ok_scene and ok_state and ok_transcript):
                console.print(
                    "[red]ERROR[/red] Save file does not match reconstructed prefix. "
                    "Use --force to continue."
                )
                return 2

        return _interactive_play(
            console,
            story.scenes,
            start=story.start,
            story_text=story_text,
            save_path=save_path,
            initial_scene=save.scene_id,
            initial_state=save.state,
            initial_script=save.script,
            initial_transcript=transcript_lines,
        )

    if args.cmd == "lint":
        try:
            _story_text, story = _load_story_from_source(args.scenes, args.pack, args.story)
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]ERROR[/red] {e}")
            return 2

        issues = lint_story(story)
        if not issues:
            console.print("[green]OK[/green] Story lint passed.")
            return 0

        order = {"error": 0, "warning": 1}
        issues = sorted(issues, key=lambda i: (order[i.severity], i.code, i.message))

        for i in issues:
            tag = "ERROR" if i.severity == "error" else "WARN"
            color = "red" if i.severity == "error" else "yellow"
            console.print(f"[{color}]{tag}[/{color}] {i.code}: {i.message}")

        if has_errors(issues) or bool(args.strict):
            return 1
        return 0

    if args.cmd == "replay":
        script = parse_script_file(Path(args.script))

        try:
            story_text, _story = _load_story_from_source(args.scenes, args.pack, args.story)
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]ERROR[/red] {e}")
            return 2

        start_override = args.start.strip() or None

        try:
            st, transcript, tr_sha, story_sha = replay_from_text(
                story_text, start_override=start_override, script=script
            )
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]ERROR[/red] {e}")
            return 2

        if args.out:
            Path(args.out).write_bytes(("\n".join(transcript) + "\n").encode("utf-8"))

        console.print(f"Transcript sha256: {tr_sha}")
        console.print(f"Story sha256:      {story_sha}")
        _print_state(console, st, "Final State")

        if args.expect_sha and args.expect_sha.strip() != tr_sha:
            console.print(
                f"[red]ERROR[/red] expected sha256 {args.expect_sha.strip()}, got {tr_sha}"
            )
            return 1

        return 0

    return 2
