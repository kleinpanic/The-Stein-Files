# Build and Dependency Notes

This project uses pinned dependencies for reproducible builds.

## Python
- Requirements are pinned in `requirements.txt`.

## Node
- Dependencies are pinned in `package-lock.json`.

## Tooling
- Text extraction uses `pdftotext` when available, otherwise a pinned Python fallback.
