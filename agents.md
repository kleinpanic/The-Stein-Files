# Repository Operating Rules

This repository follows the global AGENTS.md baseline plus these repo-scoped rules. If anything conflicts, repo-scoped rules win.

## Git workflow
- Always use Git.
- If on `main`/`master`, create a new working branch `work/<short-topic>`.
- Commit early and often with meaningful messages.
- Never rewrite history on the default branch.

## Versioning
- Canonical version is stored in `VERSION` (format `x.y.z`).
- **Never change `x`** unless explicitly instructed by the user.
- `y` bump = major feature/addition or behavior change. Requires `CHANGELOG.md` update.
- `z` bump = minor fix/maintenance. No changelog update required unless specified.

## Build + test
- Provide `make` targets: `dev`, `ingest`, `extract`, `build`, `test`, `fmt`, `lint`.
- Tests are required for any behavior change.
- Validation must include: metadata schema validation, file existence, sha256 match, index references validity, and build consistency.

## Data integrity
- Only ingest official U.S. federal government releases or clearly official court releases.
- Preserve raw files exactly as released. Derived artifacts must be separate and labeled.

## Automation
- Ingestion and site rebuild are automated via GitHub Actions with minimal permissions.
