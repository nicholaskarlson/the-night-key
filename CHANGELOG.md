# Changelog

## Unreleased

- Engine: numeric choice gating via `requires_state` / `forbids_state` for the five state fields.
- Engine: deterministic scene-text templating (`{day}`, `{energy}`, `{support}`, `{guilt}`, `{warmth}`, `{flags}`) with lint guardrails.
- Engine: multi-file stories via `includes:` (with deterministic glob expansion).
- Engine: pack-aware `includes:` so `--pack` workflows match on-disk behavior.
- Docs: clarified this repo as the book companion (engine + anchor story).

## 0.1.0

- Initial public release of the `btg` engine plus *The Night Key* seed story and book scaffolding.
