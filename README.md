# Epstein Files Public Document Library

This repository collects and preserves officially released Epstein-related public documents from U.S. federal government sources or clearly official court releases, and publishes a searchable static site.

## Sources
See `docs/SOURCES.md` for the canonical list of official upstream sources.

## Integrity
- Raw files are stored exactly as released under `data/raw/`.
- Derived artifacts (text, index) are stored under `data/derived/`.

## How to run locally

### Requirements
- Python 3.11+
- Node.js 20+
- Optional: `pdftotext` from poppler

### Setup
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
npm ci
```

### Common commands
- `make ingest` to download/update official releases
- `make extract` to extract text and build the search index
- `make build` to build the static site into `dist/`
- `make test` to run validation checks

### Serve the site
```bash
python3 -m http.server 8000 --directory dist
```

## Build pipeline
GitHub Actions runs a scheduled ingestion workflow that downloads new releases (if any), extracts text, rebuilds the site, validates integrity, and commits updates. Pushes to the default branch deploy to GitHub Pages.

## License
Code is MIT licensed. Documents remain under their original terms as published by the source authority.
