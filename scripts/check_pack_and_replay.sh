#!/usr/bin/env bash
set -euo pipefail

# Proof-first demo: build -> verify -> replay -> sha check
#
# Usage:
#   bash scripts/check_pack_and_replay.sh
#
# Outputs:
#   dist/the-night-key.pack.zip
#   dist/night_key_seed.transcript.txt

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e ".[dev]"

mkdir -p dist

PACK="dist/the-night-key.pack.zip"
OUT="dist/night_key_seed.transcript.txt"
EXPECT="expected_transcripts/night_key_seed.txt"
EXPECT_SHA="1496afa73c2fb7bb2bd56c7af82f2daf7ceded0be55053ac1bef956b63e79691"

btg pack-story stories/the-night-key --out "$PACK"
btg verify-pack "$PACK"

btg replay --script "replays/night_key_seed.script" --pack "$PACK" --out "$OUT" --expect-sha "$EXPECT_SHA"

# Optional: verify the on-disk transcript matches our pinned expected transcript.
# (The sha check above is the real proof gate.)
if command -v diff >/dev/null 2>&1; then
  diff -u "$EXPECT" "$OUT" >/dev/null
fi

echo "✅ OK: pack verified + replay sha matched"
