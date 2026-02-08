# Changelog

## 1.4.0
- Added in-page PDF viewer with GitHub raw integration for lightweight Pages deployment (viewer.html + build-sha/repo-slug meta tags).
- Implemented case-insensitive search with query normalization (toLowerCase) for better UX.
- Added asset cache-busting using git SHA as version parameter for CSS/JS to prevent stale cache issues.
- Fixed DOJ age-verify gate with automatic cookie injection (justiceGovAgeVerified=true) for PDF URL access.
- Fixed ingest crash on 404 responses due to falsey HTTPError.response handling (added status_code_from_http_error utility).
- Strengthened index completeness validation to ensure all catalog entries are present in search shards (bidirectional check).
- Updated verify-doj cookie jar fallback to match ingest behavior (.txt → .json).
- Raised CI ingest limits for bulk ingestion (EPPIE_MAX_DOWNLOADS_PER_SOURCE=0, EPPIE_TIME_BUDGET_SECONDS=20000).
- Successfully ingested 946 PDFs from DOJ Epstein Library disclosures (4 URLs returned 404).

## 1.3.0
- Removed default ingest caps and added explicit throttling/backoff knobs with time budgets for CI.
- Made ingest resumable with per-source seen/failed tracking and conditional requests (ETag/Last-Modified).
- Added mirror mode toggle for build output and improved tests for backoff, state, and shard extraction.

## 1.2.0
- Added interactive DOJ auth capture (`make auth-doj`) with local cookie jar handling for gated sources.
- Added explicit search modes (full/title/tags/source/file) with shareable URL params.
- Treat `data/derived/` as build output and expand test coverage for cookies, gating, and manifests.
- Added cookie jar format support for both JSON and Netscape plus incremental ingest cursors and CI caps.

## 1.1.0
- UI overhaul with a clearer layout, improved results cards, mobile filter drawer, loading and empty states, and shareable URL filters.
- Expanded ingestion architecture with official DOJ Epstein Library adapters, deterministic discovery, size caps, and sharded search index output.
- Developer ergonomics updates: `make venv`, `make node`, and `make setup` with venv-first execution.
- CI updates to rely on Makefile targets for setup, test, and build.
