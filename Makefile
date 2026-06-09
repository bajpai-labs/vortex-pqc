# VORTEX-256 build automation
PYTHON := python3
PIP    := pip3

.PHONY: all install build test test-python test-c lint clean

all: install test

install:
	$(PIP) install -U pip wheel
	$(PIP) install -e ".[dev]"

build:
	$(PYTHON) -m build --wheel

test: test-python test-c

test-python:
	$(PYTHON) -m pytest src/tests/ -v --tb=short

test-c:
	$(MAKE) -C c test

lint:
	$(PYTHON) -m flake8 src/vortex_pqc/
	$(PYTHON) -m mypy src/vortex_pqc/

clean:
	rm -rf build/ dist/ *.egg-info/ .coverage .pytest_cache/
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	$(MAKE) -C c clean
