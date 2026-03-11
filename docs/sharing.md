# Sharing stories (packs + gallery)

> **The Night Key book repo note**
>
> This repository is the companion codebase for the book *The Night Key*. It includes the `btg` interactive-fiction engine (MIT) **plus** the anchor story under `stories/the-night-key/`.
>
> Upstream engine: https://github.com/nicholaskarlson/storygame-engine
> Recommended for this repo: pack and verify the anchor story before sharing: `btg pack-story stories/the-night-key --out dist/the-night-key.pack.zip` then `btg verify-pack dist/the-night-key.pack.zip`.


This guide is for `storygame-engine` (CLI: `btg`).

A **story pack** is a deterministic zip file that contains:

- `scenes.yaml` (your story)
- optional extra files inside your story folder (README, assets)

Each pack also contains a deterministic manifest and checksum list so others can verify integrity.

## Build a single pack

```bash
btg pack-story stories/my_story --out dist/packs/my_story.pack.zip
```

Verify a pack:

```bash
btg verify-pack dist/packs/my_story.pack.zip
```

## Build the gallery index

Build packs for everything in `stories/` and write:

- `dist/packs/index.json`

```bash
python scripts/build_packs.py
```

This is designed for “proof-first” sharing: deterministic outputs and stable hashing.
