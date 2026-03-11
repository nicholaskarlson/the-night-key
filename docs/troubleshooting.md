# Troubleshooting

> **The Night Key book repo note**
>
> This repository is the companion codebase for the book *The Night Key*. It includes the `btg` interactive-fiction engine (MIT) **plus** the anchor story under `stories/the-night-key/`.
>
> Upstream engine: https://github.com/nicholaskarlson/storygame-engine
> If you see flags not being applied, check that your choices use `sets_flags` / `clears_flags` (or the accepted aliases `set_flags` / `clear_flags`).


This guide is for `storygame-engine` (CLI: `btg`).

## YAML won’t parse

If you see an error that mentions YAML:

- check indentation (2 spaces is safest)
- ensure lists use `-` and align under the key
- confirm strings with `:` are quoted

Use `btg lint --strict` to get story-specific validation after YAML parses.

## Lint errors

Common authoring mistakes:

- `goto` references a scene id that doesn't exist
- duplicate scene ids
- flags used in `requires_flags` / `sets_flags` not declared in the top-level `flags:` list
- terminal scenes that still have choices

## Windows notes

Use PowerShell:

```powershell
.\scripts\verify.ps1
```

If `btg` isn’t found, run it through the venv:

```powershell
.\.venv\Scripts\btg play
```

## Text templating

Scene text supports placeholders like `{energy}` and `{flags}`.

- If you see a `TEMPLATE_UNKNOWN` warning, you used a placeholder name the engine doesn’t recognize.
- If you see a `TEMPLATE_MALFORMED` error, you likely have an unmatched `{` or `}`.
  Use `{{` and `}}` to include literal braces.
