# Changelog

## 1.5.0
- **OCR Extraction**: Applied Tesseract OCR to 279 image PDFs for improved text extraction and searchability
- **Stats Dashboard**: Added comprehensive `/stats.html` page with quality breakdowns, type distributions, OCR status, and source-level analytics
- **Enhanced Classification**: Improved document categorization with robust FBI evidence photo detection (handles OCR errors), redaction detection, and better pattern matching
- **Photo Detection**: Added evidence-photo category for FBI evidence photographs with case ID, photographer, and location metadata
- **Redaction Detection**: Identifies heavily redacted documents based on FOIA markers and sparse text patterns
- **Quality Analysis**: 
  - Text PDFs: 497 docs @ 78.1/100 avg quality
  - Hybrid PDFs: 106 docs @ 76.0/100 avg quality  
  - Image PDFs: 344 docs @ 11.0/100 avg quality (279 OCR'd)
- **Category Distribution**: 416 categorized documents across correspondence, memorandum, legal filings, evidence lists, flight logs, reports, and photos
- **Batch Re-classification**: Added `reclassify_catalog.py` script for applying improved classification logic to existing catalog
- **Mirror Mode**: Enabled PDF mirroring in GitHub Pages deployment to serve all PDFs locally (solves CORS issues with DOJ sources)
- **Mobile Optimizations**: Enhanced CSS for iOS/mobile devices with better touch targets and responsive layouts

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
