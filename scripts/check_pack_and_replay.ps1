$ErrorActionPreference = "Stop"

function Invoke-Step([string]$cmd) {
  Write-Host $cmd
  Invoke-Expression $cmd
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# Proof-first demo: build -> verify -> replay -> sha check
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_pack_and_replay.ps1

python -m venv .venv
Invoke-Step ".\.venv\Scripts\python -m pip install -U pip"
Invoke-Step ".\.venv\Scripts\python -m pip install -e '.[dev]'"

if (!(Test-Path -Path "dist")) {
  New-Item -ItemType Directory -Path "dist" | Out-Null
}

$Pack = "dist/the-night-key.pack.zip"
$Out = "dist/night_key_seed.transcript.txt"
$Expect = "expected_transcripts/night_key_seed.txt"
$ExpectSha = "1496afa73c2fb7bb2bd56c7af82f2daf7ceded0be55053ac1bef956b63e79691"

Invoke-Step ".\.venv\Scripts\btg pack-story stories/the-night-key --out $Pack"
Invoke-Step ".\.venv\Scripts\btg verify-pack $Pack"
Invoke-Step ".\.venv\Scripts\btg replay --script replays/night_key_seed.script --pack $Pack --out $Out --expect-sha $ExpectSha"

# Optional: compare transcript files
$a = Get-Content -Raw $Expect
$b = Get-Content -Raw $Out
if ($a -ne $b) {
  Write-Host "ERROR transcript file does not match expected_transcripts/night_key_seed.txt"
  exit 1
}

Write-Host "✅ OK: pack verified + replay sha matched"
