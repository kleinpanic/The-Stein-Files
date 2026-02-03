.PHONY: dev ingest extract build test fmt lint

PY := python3


dev:
	$(PY) scripts/build_site.py
	$(PY) -m http.server --directory dist 8000

ingest:
	$(PY) scripts/ingest.py

extract:
	$(PY) scripts/extract.py

build:
	$(PY) scripts/build_site.py

test:
	$(PY) scripts/validate.py
	$(PY) -m pytest -q

fmt:
	$(PY) -m ruff format .

lint:
	$(PY) -m ruff check .
