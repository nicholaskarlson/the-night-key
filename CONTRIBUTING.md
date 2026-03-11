# Contributing

Thanks for taking an interest in **storygame-engine**.

## Quickstart (dev)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
make verify
```

## Style + proof gate

Before opening a PR, run:

- Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1`
- macOS/Ubuntu: `make verify` (or `bash scripts/verify.sh`)

## What to contribute

- story authoring UX (docs, examples, better errors)
- engine robustness (determinism, linting, schema checks)
- tests + fixtures

## License

By contributing, you agree your contributions are licensed under the MIT License.
