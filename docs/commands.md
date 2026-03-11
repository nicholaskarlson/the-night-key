# Command reference

> **The Night Key book repo note**
>
> This repository is the companion codebase for the book *The Night Key*. It includes the `btg` interactive-fiction engine (MIT) **plus** the anchor story under `stories/the-night-key/`.
>
> Upstream engine: https://github.com/nicholaskarlson/storygame-engine
> Quickstart (most readers): `btg play --story the-night-key` and `btg lint --strict --story the-night-key`.


This guide is for `storygame-engine` (CLI: `btg`).

## Story discovery

- `btg list-stories` — list story projects under `stories/`

## Play

- `btg play` — play the default story
- `btg play --story NAME` — play `stories/NAME/scenes.yaml`
- `btg play --scenes PATH` — play a story YAML file
- `btg play --pack PATH` — play a story pack zip
- `btg play --start SCENE_ID` — override start scene
- `btg play --save SAVE.json` — autosave after each choice

## Resume

- `btg resume --save SAVE.json` — resume
- `btg resume --force` — ignore story-hash mismatch (not recommended)

## Lint

- `btg lint --strict --story NAME` — validate `stories/NAME/scenes.yaml`
- `btg lint --strict --scenes PATH` — validate authoring errors
- `btg lint --pack PATH` — validate a pack

## Replay

- `btg replay --script PATH --story NAME`
- `btg replay --script PATH --scenes PATH` — deterministic replay from a script file

## Packing

- `btg pack-story STORY_DIR --out OUT.pack.zip`
- `btg verify-pack OUT.pack.zip`
- `btg ls-pack OUT.pack.zip`
- `btg unpack-story OUT.pack.zip --out DIR`

## Convenience scripts

- Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/play.ps1`
- macOS/Ubuntu: `bash scripts/play.sh`
