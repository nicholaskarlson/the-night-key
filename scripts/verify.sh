#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"

ruff format --check .
ruff check .
mypy src/btg

# Book repo default: verify The Night Key stays valid.
btg lint --strict --story the-night-key
# Keep starter as a reference story (optional, but helpful).
btg lint --strict --story starter

pytest -q
python scripts/build_packs.py

echo "OK: verify"
