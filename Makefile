.PHONY: venv install fmt lint lint-story test packs verify verify-sh clean

VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

venv:
	python3 -m venv $(VENV)
	$(PIP) install -U pip

install: venv
	$(PIP) install -e ".[dev]"

fmt: install
	$(VENV)/bin/ruff format .

lint: install
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/ruff check .
	$(VENV)/bin/mypy src/btg

lint-story: install
	$(VENV)/bin/btg lint --strict

test: install
	$(VENV)/bin/pytest -q

packs: install
	$(PY) scripts/build_packs.py

verify: lint lint-story test packs
	@echo "OK: verify"

verify-sh:
	bash scripts/verify.sh

clean:
	rm -rf $(VENV) dist .pytest_cache .mypy_cache .ruff_cache
