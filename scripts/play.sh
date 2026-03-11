#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/play.sh
#   bash scripts/play.sh -- --story starter
# Any args after -- are forwarded to: btg play <args>

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e ".[dev]"

if [ "${1:-}" = "--" ]; then
  shift
fi

if [ "$#" -eq 0 ]; then
  btg play --story starter
else
  btg play "$@"
fi
