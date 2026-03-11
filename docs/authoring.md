# Authoring guide (non-programmers)

> **The Night Key book repo note**
>
> This repository is the companion codebase for the book *The Night Key*. It includes the `btg` interactive-fiction engine (MIT) **plus** the anchor story under `stories/the-night-key/`.
>
> Upstream engine: https://github.com/nicholaskarlson/storygame-engine


This guide is for `storygame-engine` (CLI: `btg`).

You can build a complete story game by editing one file: **`scenes.yaml`**.

A story is a set of **scenes**. Each scene has:

- an `id` (unique)
- `text` (what the player reads)
- a list of `choices`

Each choice has:

- `label` (what the player sees)
- `goto` (scene id to transition to)
- optional `delta` (changes to the player state)
- optional flag changes (`sets_flags`, `clears_flags`)

Note: For compatibility, `sets_flags` and `clears_flags` are also accepted as aliases.
- optional `requires_flags` / `forbids_flags` (gates visibility)

## Create a new story

```bash
btg init-story stories/my_story --title "My Story"
btg list-stories
```

Then edit:

- `stories/my_story/scenes.yaml`

Validate:

```bash
btg lint --strict --story my_story
# or:
btg lint --strict --scenes stories/my_story/scenes.yaml
```

Play-test:

```bash
btg play --story my_story
# or:
btg play --scenes stories/my_story/scenes.yaml
```

## Minimal example

```yaml
schema_version: 1
title: "A Tiny Story"
start: intro
flags: [met_neighbor]

scenes:
  - id: intro
    text: |
      You step outside. The air is cold.
    choices:
      - label: Say hello to the neighbor
        goto: neighbor
        sets_flags: [met_neighbor]
        delta: { warmth: +1 }

      - label: Go back inside
        goto: end

  - id: neighbor
    text: |
      They nod. It helps, a little.
    choices:
      - label: Head home
        goto: end

  - id: end
    terminal: true
    text: |
      Day ends.
```

## State model

The engine tracks a small “day 1” state:

- `day`, `energy`, `support`, `guilt`, `warmth` (integers, clamped 0–10)
- `flags` (strings you define in the `flags:` list)

`delta` supports only those numeric keys, with integer adjustments like `+1` or `-2`.

## Design tips

- Keep scene ids short and stable.
- Prefer **many small scenes** over one large “wall of text”.
- Use flags to represent “facts” that matter later.
- Use `btg lint --strict` often.
