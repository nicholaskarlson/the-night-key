# The Night Key (Anchor Story)

This folder contains the anchor interactive-fiction story used throughout the book *The Night Key*.

- Story file: `scenes.yaml`
- Play it: `btg play --story the-night-key`
- Lint it (proof-first): `btg lint --strict --story the-night-key`

## What this story is (and isn’t)

This is not a demo snippet. It’s a growing, book-length example that will expand chapter by chapter:
- more scenes
- more flags and conditional choices
- multiple endings
- replay scripts and deterministic transcripts
- deterministic story packs for sharing

## Quick commands

```bash
# from repo root
btg play --story the-night-key
btg lint --strict --story the-night-key

# optional: use the helper scripts
./scripts/check_night_key.sh
# or on Windows:
# powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_night_key.ps1
```

## Proof-first checkpoint

Before you share changes:
1) `btg lint --strict --story the-night-key`
2) `pytest -q`
3) Commit with a clear message describing the narrative/structural change.
