# Build and Dependency Notes

This project uses pinned dependencies for reproducible builds.

## Python
- Requirements are pinned in `requirements.txt`.
- Key packages: `requests`, `pypdf`, `pdfminer.six`, `jsonschema`, `Markdown`, `pytest`, `ruff`.

## Node
- Dependencies are pinned in `package-lock.json`.
- `lunr` is used for client-side search (loaded via a pinned CDN version).

## Tooling
- Text extraction uses `pdftotext` when available, otherwise `pdfminer.six`.
