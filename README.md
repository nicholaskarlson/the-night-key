# The Night Key

**A build-along interactive fiction book + a complete example story, built on `storygame-engine` (CLI: `btg`).**  
License: **MIT** (see `LICENSE`).

This repo is the working home for the book project **The Night Key** and its anchor interactive-fiction story. The book teaches non-programmers to write interactive fiction **by building one real story step by step**—from a tiny playable seed to a verified, shareable, deterministic story pack.

## What you can do here

- **Play** the story: `btg play --story the-night-key`
- **Lint** it strictly (catch authoring mistakes early): `btg lint --strict --story the-night-key`
- **Replay** deterministically from a script: `btg replay --script PATH --story the-night-key`
- **Pack** and **verify** a deterministic artifact: `btg pack-story ...` and `btg verify-pack ...`

No GUI. No Python coding required for authors. Stories are plain YAML.

## Repo layout

- `stories/the-night-key/scenes.yaml` — the anchor story (source of truth for the narrative)
- `docs/authoring.md` — how to author stories in YAML (non-programmer friendly)
- `docs/commands.md` — CLI command reference
- `docs/sharing.md` — deterministic packs and GitHub-friendly sharing
- `src/btg/cli.py` — CLI implementation (authoritative behavior)
- `tests/` — test-backed behavior (source of truth when docs disagree)

## Quickstart (macOS / Ubuntu)

```bash
git clone https://github.com/nicholaskarlson/the-night-key
cd the-night-key

python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"

# Validate and play the anchor story
btg lint --strict --story the-night-key
btg play --story the-night-key
```

## Quickstart (Windows PowerShell)

```powershell
git clone https://github.com/nicholaskarlson/the-night-key
cd the-night-key

python -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install -e '.[dev]'

.\.venv\Scripts\btg lint --strict --story the-night-key
.\.venv\Scripts\btg play --story the-night-key
```

## The proof-first workflow (recommended loop)

This is the “teach by doing” rhythm the book uses:

1) **Play early**
```bash
btg play --story the-night-key
```

2) **Lint strictly**
```bash
btg lint --strict --story the-night-key
```

3) **Replay deterministically** (once you have a replay script)
```bash
btg replay --script replays/night-key_path_a.yaml --story the-night-key
```

4) **Pack and verify** (for sharing)
```bash
mkdir -p dist/packs
btg pack-story stories/the-night-key --out dist/packs/the-night-key.pack.zip
btg verify-pack dist/packs/the-night-key.pack.zip
```

5) **Unpack to inspect** (optional)
```bash
mkdir -p /tmp/night_key_unpack
btg unpack-story dist/packs/the-night-key.pack.zip --out /tmp/night_key_unpack
```

## Writing your own story (using this repo as a template)

You can create a new story project beside The Night Key:

```bash
btg init-story stories/my_story --title "My Story"
btg lint --strict --story my_story
btg play --story my_story
```

Stories live at:

- `stories/<name>/scenes.yaml`

## If you want the authoritative rules (no guessing)

Start here:

- `docs/authoring.md` (YAML schema, scenes, choices, flags, deltas)
- `docs/commands.md` (exact `btg` CLI syntax)
- `docs/sharing.md` (packs, verification, gallery/index)

When docs and behavior disagree, **trust the implementation and tests**.

## License

MIT — see `LICENSE`.
