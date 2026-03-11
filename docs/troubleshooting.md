# Troubleshooting

This guide is for `storygame-engine` (CLI: `btg`).
Website: storygame.ca

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
