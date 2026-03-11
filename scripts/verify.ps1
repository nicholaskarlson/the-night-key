$ErrorActionPreference = "Stop"

function Invoke-Step([string]$cmd) {
  Write-Host $cmd
  Invoke-Expression $cmd
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

python -m venv .venv
Invoke-Step ".\.venv\Scripts\python -m pip install -U pip"
Invoke-Step ".\.venv\Scripts\python -m pip install -e '.[dev]'"

Invoke-Step ".\.venv\Scripts\ruff format --check ."
Invoke-Step ".\.venv\Scripts\ruff check ."
Invoke-Step ".\.venv\Scripts\mypy src\btg"
Invoke-Step ".\.venv\Scripts\btg lint --strict"
Invoke-Step ".\.venv\Scripts\pytest -q"
Invoke-Step ".\.venv\Scripts\python scripts\build_packs.py"

Write-Host "OK: verify"
