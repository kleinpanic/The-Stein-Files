# Changelog

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
