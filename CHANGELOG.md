# Changelog

All notable changes to The Stein Files (Epstein Files Library) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.2] - 2026-02-10

### Fixed
- CI/CD build failure caused by duplicate pdf2image dependency
- Removed conflicting pdf2image>=1.17.0 line from requirements.txt

### Added
- AUTONOMOUS_WORKFLOW.md: Corrected autonomous work protocol
- ENDPOINT_CHECKLIST.md: Review checklist for all site endpoints
- LESSONS_LEARNED.md: Documentation of mistakes and corrections

### Changed
- Workflow approach: Feature branches, local validation, atomic commits
- Release cadence: Merge to main only for validated releases

## [1.5.1] - 2026-02-10

### Added
- Fuzzy categorization for OCR-garbled text (edit distance matching)
- Batch OCR processing script (process documents by ID file)
- Maintenance document category for service/inspection records
- Autonomous progress tracking and documentation
- Comprehensive UX audit with 7-phase roadmap (157h estimated)
- CHANGELOG.md following Keep a Changelog format
- REVIEW_CHECKLIST.md for post-change validation

### Changed
- Person threshold lowered from 3+ to 1+ mentions (now showing 23 people)
- Email metadata now shows "[Not visible in document]" instead of blank fields
- Improved email metadata re-extraction from document text

### Fixed
- Empty email From/To/Subject fields now display meaningful text (35% had blank fields)
- Re-extracted metadata for 59 emails from document text
- OCR text quality acknowledged as categorization blocker

## [1.5.0] - 2026-02-09

### Added
- Enhanced OCR module with adaptive DPI (200-300) and preprocessing
- Enhanced metadata extraction (FBI numbers, person names, locations, case numbers)
- New document categories: email, deposition, subpoena, case-photo, handwritten-note
- Person profiles with expandable accordion UI (single page)
- Stats dashboard with comprehensive analytics
- Phase 3 UX enhancements: CSV export, keyboard shortcuts, share URL
- Mobile optimization: swipe gestures, WCAG 2.1 AAA touch targets, optimized rendering
- OCR extraction for 279 image PDFs
- Comprehensive person extraction (44 known people)
- Auto-categorization for uncategorized documents

### Changed
- Person data threshold from 5+ to 3+ mentions
- Site-wide people.json generation during CI/CD build
- Person profiles converted from multiple pages to single accordion page

### Fixed
- PDF viewer and asset loading issues post-deployment
- Person extraction gaps (added Leon Black, Ken Starr, Jay Lefkowitz, Roy Black)
- Email metadata cleanup (removed OCR noise from From/To fields)

## [1.4.0] - 2026-02-08

### Added
- In-page PDF viewer with GitHub raw integration
- Git LFS for binary storage (947 PDFs, ~1.5GB)
- LFS caching in GitHub Actions workflow
- Auto-release workflow for future tags

### Changed
- Switched to Git LFS media CDN for PDF storage
- Base tag for asset path resolution

### Fixed
- GitHub Actions for LFS compatibility
- Text extraction after LFS migration
- Ingest workflow optimized (skip LFS downloads)

## [1.3.0] - 2026-02-07

### Added
- DOJ Memoranda source with DirectListAdapter
- Index completeness validation with bidirectional checks
- Search UI case-sensitivity fixes
- Asset cache-busting using git SHA versioning

### Changed
- DOJ cookie jar fallback for verification
- Ingest robustness for HTTP 404 handling

### Fixed
- DOJ "age-verify" gate with automatic cookie injection
- Local environment (.venv recreation after breakage)

### Removed
- Non-existent DOJ sources (court-records, foia)

## [1.2.0] - 2026-02-06

### Added
- Massive ingest completed: 947 PDFs (~1.5GB) from DOJ disclosures
- Document categorization system
- Phase 1 metadata extraction (file numbers, person names, locations)

## [1.1.0] - 2026-02-05

### Added
- Initial site structure with search functionality
- Basic document metadata extraction
- Source configuration system

## [1.0.0] - 2026-02-04

### Added
- Initial release
- Basic document ingestion from DOJ sources
- Simple catalog and index generation
