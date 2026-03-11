# The Night Key (anchor story)

This folder contains the anchor interactive-fiction story for the book *The Night Key*.

## Quick play

From the repo root:

```bash
btg play --story the-night-key
```

## File layout (multi-file)

This story uses **multi-file scenes** via `includes:`:

- `scenes.yaml` — entrypoint (metadata + flags + start + includes list)
- `scenes/act1.yaml` — the current scene content (Act 1 seed)

Splitting scenes keeps the project approachable as it grows. The engine merges included files deterministically.
