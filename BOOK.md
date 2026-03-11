# The Night Key — Book Project

This repository supports a book that teaches interactive fiction by building one complete story, **The Night Key**, step by step using the `btg` CLI.

The book is written for:
- non-programmers
- beginner writers interested in interactive fiction
- technically curious readers who want a rigorous but friendly workflow

## What you will build

By the end, a reader will be able to:
- design a branching story with flags and consequences
- author scenes in plain YAML
- playtest early and often (`btg play`)
- lint strictly (`btg lint --strict`)
- create deterministic replays (`btg replay`)
- package and verify a deterministic story pack (`btg pack-story`, `btg verify-pack`)
- share the project in a GitHub-friendly way

## Project structure (book-facing)

- `stories/the-night-key/` — the anchor story built through the book
- `replays/` — replay scripts used in the book (added as the story grows)
- `manuscript/` — manuscript files (optional; add when ready)

## Proof-first checkpoints

A repeating checkpoint used throughout the book:

1. `btg play --story the-night-key`
2. `btg lint --strict --story the-night-key`
3. `btg replay --script replays/<path>.yaml --story the-night-key` (when replays exist)
4. `btg pack-story stories/the-night-key --out dist/packs/the-night-key.pack.zip`
5. `btg verify-pack dist/packs/the-night-key.pack.zip`

## Status

This repo is intentionally iterative. The story and book assets will evolve in visible, reviewable steps.
