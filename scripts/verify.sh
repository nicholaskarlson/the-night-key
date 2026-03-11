#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"

ruff format --check .
ruff check .
mypy src/btg
btg lint --strict
pytest -q
python scripts/build_packs.py

echo "OK: verify"
