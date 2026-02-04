.PHONY: dev ingest extract build test fmt lint

PY := python3


dev:
	$(PY) -m scripts.build_site
	$(PY) -m http.server --directory dist 8000

ingest:
	$(PY) -m scripts.ingest

extract:
	$(PY) -m scripts.extract

build:
	$(PY) -m scripts.build_site

test:
	$(PY) -m scripts.validate
	$(PY) -m pytest -q

fmt:
	$(PY) -m ruff format .

lint:
	$(PY) -m ruff check .
