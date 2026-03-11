$ErrorActionPreference = "Stop"

# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/play.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/play.ps1 -- --story starter
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/play.ps1 --story starter
#
# Any args are forwarded to: btg play <args>
# If no args are provided, defaults to: btg play --story starter

if (!(Test-Path ".\.venv")) {
  python -m venv .venv
}

& .\.venv\Scripts\python -m pip install -U pip | Out-Host
& .\.venv\Scripts\python -m pip install -e '.[dev]' | Out-Host

$btg = ".\.venv\Scripts\btg"

$forward = $args
if ($forward.Count -gt 0 -and $forward[0] -eq "--") {
  if ($forward.Count -gt 1) {
    $forward = $forward[1..($forward.Count - 1)]
  } else {
    $forward = @()
  }
}

if ($forward.Count -eq 0) {
  & $btg play --story starter
} else {
  & $btg play @forward
}
