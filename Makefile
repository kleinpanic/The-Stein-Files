.PHONY: dev ingest extract build test fmt lint venv node setup

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(PY) -m pip
VENV_STAMP := $(VENV)/.stamp
NODE_STAMP := node_modules/.stamp

$(VENV_STAMP): requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	touch $(VENV_STAMP)

venv: $(VENV_STAMP)

$(NODE_STAMP): package.json package-lock.json
	npm ci
	@mkdir -p node_modules
	touch $(NODE_STAMP)

node: $(NODE_STAMP)

setup: venv node

dev: venv
	$(PY) -m scripts.build_site
	$(PY) -m http.server --directory dist 8000

ingest: venv
	$(PY) -m scripts.ingest

extract: venv
	$(PY) -m scripts.extract

build: venv
	$(PY) -m scripts.build_site

test: venv
	$(PY) -m scripts.validate
	$(PY) -m pytest -q

fmt: venv
	$(PY) -m ruff format .

lint: venv
	$(PY) -m ruff check .
