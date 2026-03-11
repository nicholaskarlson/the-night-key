# The Night Key (story)

This folder contains the build-along story used in the book project.

## Quick play (from repo root)

- Play:
  - `btg play --story the-night-key`
- Lint:
  - `btg lint --strict --story the-night-key`

## What this story demonstrates

This story intentionally uses new engine features so readers see them “in the wild”:

- **Multi-file stories via `includes:`**
  - `stories/the-night-key/scenes.yaml` includes `scenes/act*.yaml` (deterministic glob order).
- **Numeric gating**
  - Choices gated by `requires_state` / `forbids_state` (e.g., energy/warmth thresholds).
- **Tiny templating**
  - Scene text can render `{energy}`, `{warmth}`, `{day}`, `{flags}` for subtle narrative feedback.

## Structure

- `scenes.yaml` — metadata + `includes:`
- `scenes/act1.yaml` — lobby/hallway setup (seed)
- `scenes/act2.yaml` — first deeper turn (gating + templating + a real ending)
