# Eppie Autonomous Improvement Plan
**Project**: Advanced Epstein Files Document Search & Archive
**Goal**: Better character extraction, searchability, usability, and tagging
**Autonomous Mode**: Overnight work, dev agent
**Created**: 2026-02-09

---

## 🎯 Objectives

Transform Eppie into a highly advanced document research platform with:
1. **Better character extraction** - Improved OCR, metadata extraction, file number detection
2. **Advanced searchability** - Enhanced tagging, categorization, filtering
3. **Better usability** - Improved UI, shareable searches, mobile experience
4. **GitHub Pages optimization** - Fast loading, progressive enhancement

---

## 📋 Implementation Phases

### Phase 1: Enhanced Character Extraction (Priority: HIGH)

**Goal**: Improve text extraction quality and coverage

#### Tasks:
1. **Upgrade OCR Pipeline**
   - [ ] Add Tesseract language hints (eng+deu for German names)
   - [ ] Implement adaptive DPI (200-300 based on page size)
   - [ ] Add image preprocessing (deskew, denoise, contrast enhancement)
   - [ ] Extend OCR to all pages (not just first 5) for image PDFs
   - [ ] Add OCR confidence scoring per page
   - [ ] Implement multi-pass OCR (different preprocessing strategies)

2. **Enhanced Metadata Extraction**
   - [ ] Improve file number patterns (add FBI, court case number formats)
   - [ ] Extract person names (NER with spaCy or simple pattern matching)
   - [ ] Extract locations (cities, addresses in evidence photos)
   - [ ] Detect photographer/camera metadata from EXIF (if embedded in PDFs)
   - [ ] Extract case numbers from evidence photos more reliably
   - [ ] Add batch/exhibit number extraction

3. **Document Type Detection**
   - [ ] Add "email" category detection (From:, To:, Subject:, Date: headers)
   - [ ] Add "case-photo" subcategory (distinct from evidence-photo)
   - [ ] Detect handwritten notes (low quality + short text + image PDF)
   - [ ] Add "deposition" category (Q:, A: patterns)
   - [ ] Add "subpoena" category (legal keyword patterns)

**Validation**:
- Run on 50 random image PDFs, verify OCR quality improvement
- Test file number extraction accuracy (target: 95%+ recall on EFTA numbers)
- Verify new categories appear in catalog

---

### Phase 2: Advanced Tagging & Search (Priority: HIGH)

**Goal**: Multi-dimensional tagging and powerful filtering

#### Tasks:
1. **Auto-Tagging System**
   - [ ] Implement keyword-based auto-tagging (scan content for terms like "flight", "victim", "witness")
   - [ ] Add person-name tags (extract and tag by person mentioned)
   - [ ] Add location tags (cities, islands, addresses)
   - [ ] Add date-range tags (1990s, 2000s, 2010s)
   - [ ] Add document-source tags (FBI, court, deposition, etc.)
   - [ ] Make tags case-insensitive, normalized (remove special chars)

2. **Enhanced Search Features**
   - [ ] Add "person search" mode (search by person name across all docs)
   - [ ] Add "location search" mode (search by place)
   - [ ] Add "file number lookup" (exact match on EFTA/FBI numbers)
   - [ ] Implement fuzzy search (handle typos, OCR errors)
   - [ ] Add search suggestions (autocomplete on tags, names, locations)
   - [ ] Add "related documents" links (same case number, same date range)

3. **Advanced Filters**
   - [ ] Multi-select filters (select multiple tags, sources, years)
   - [ ] Date range picker (from YYYY-MM-DD to YYYY-MM-DD)
   - [ ] File size filter (useful for finding photos vs text docs)
   - [ ] Page count filter (single page vs multi-page)
   - [ ] "Has photos" filter (detect embedded images in PDFs)
   - [ ] "OCR quality" slider (show only high-quality extractions)

**Validation**:
- Search for "Maxwell" and verify person-tagged results appear
- Search for "Little St. James" and verify location-tagged results
- Test fuzzy search with intentional typos
- Verify multi-tag filtering works (e.g., "flight-log + 1990s")

---

### Phase 3: UI/UX Enhancements (Priority: MEDIUM)

**Goal**: Modern, intuitive, mobile-friendly interface

#### Tasks:
1. **Search Interface**
   - [ ] Add search history (last 10 searches, stored in localStorage)
   - [ ] Add "saved searches" feature (bookmark complex queries)
   - [ ] Implement keyboard shortcuts (Ctrl+K to focus search, Esc to clear)
   - [ ] Add search result count ("Showing 47 of 947 documents")
   - [ ] Add "export results" button (CSV with metadata)
   - [ ] Add "share search" button (copy URL to clipboard)

2. **Document Viewer**
   - [ ] Add side-by-side view (PDF + extracted text)
   - [ ] Highlight search terms in PDF viewer
   - [ ] Add "jump to page" for multi-page PDFs
   - [ ] Add thumbnail view for image PDFs (gallery mode)
   - [ ] Implement zoom controls for photos
   - [ ] Add download original PDF button (direct link)

3. **Mobile Optimization**
   - [ ] Optimize filter panel for mobile (swipe-up drawer)
   - [ ] Make result cards tap-friendly (larger touch targets)
   - [ ] Add mobile-specific search bar (sticky at top)
   - [ ] Optimize PDF.js rendering for mobile (lower resolution)
   - [ ] Add "request desktop site" hint for complex searches

4. **Statistics Dashboard**
   - [ ] Add timeline visualization (docs by release date)
   - [ ] Add word cloud (most common terms in corpus)
   - [ ] Add network graph (person-to-person connections)
   - [ ] Add top 10 most referenced people/places
   - [ ] Add coverage metrics (% OCR'd, % categorized)

**Validation**:
- Test on mobile (iOS Safari, Android Chrome)
- Verify keyboard shortcuts work
- Test export CSV feature
- Verify search history persists across page reloads

---

### Phase 4: Performance & Deployment (Priority: MEDIUM)

**Goal**: Fast loading, efficient indexing, reliable deployment

#### Tasks:
1. **Index Optimization**
   - [ ] Compress Lunr.js index shards (gzip)
   - [ ] Implement lazy index loading (load shards only when needed)
   - [ ] Add service worker for offline search (cache index shards)
   - [ ] Pre-build index statistics (avoid client-side computation)
   - [ ] Add index version tracking (detect stale indexes)

2. **Build Pipeline**
   - [ ] Add incremental build (only re-extract changed PDFs)
   - [ ] Parallelize text extraction (use multiprocessing)
   - [ ] Add build progress reporting (console + log file)
   - [ ] Implement build resume (checkpoint failed builds)
   - [ ] Add dry-run mode (preview changes without committing)

3. **CI/CD Integration**
   - [ ] Add GitHub Actions workflow for OCR (Tesseract in CI)
   - [ ] Implement scheduled ingest (daily check for new releases)
   - [ ] Add build artifact caching (speed up CI builds)
   - [ ] Add deployment preview (test builds on PR branches)
   - [ ] Add link checker (verify source URLs still work)

4. **Documentation**
   - [ ] Update README with new features (auto-tagging, advanced search)
   - [ ] Add user guide (how to search, filter, export)
   - [ ] Add developer guide (how to add new sources, adapters)
   - [ ] Document API (catalog.json structure, shard format)
   - [ ] Add FAQ (common search tips, OCR limitations)

**Validation**:
- Run full build and verify it completes without errors
- Measure index load time (target: <2s on 3G connection)
- Test offline mode (disconnect network, verify search still works)
- Run link checker and fix broken source URLs

---

## 🔬 Testing Strategy

### Automated Tests
- [ ] Add pytest tests for PDF analyzer (test all document categories)
- [ ] Add tests for file number extraction (known test cases)
- [ ] Add tests for auto-tagging (verify tag accuracy)
- [ ] Add tests for search index builder (verify shard structure)
- [ ] Add integration test (ingest → extract → build → validate)

### Manual Testing
- [ ] Test search with real queries ("flight logs 1990s", "evidence photos FBI")
- [ ] Verify all filters work correctly
- [ ] Test on mobile devices (real devices, not just emulators)
- [ ] Test PDF viewer with large PDFs (100+ pages)
- [ ] Test export feature with large result sets

### Regression Testing
- [ ] Verify existing docs still searchable after changes
- [ ] Check that all 947 docs still indexed
- [ ] Verify no broken links in site
- [ ] Test backward compatibility (old URLs still work)

---

## 📊 Success Metrics

| Metric | Before | Target | Validation |
|--------|--------|--------|------------|
| OCR Coverage | 279/344 (81%) | 340/344 (99%) | Count OCR'd image PDFs |
| High Quality Docs | 443/947 (47%) | 700/947 (74%) | Quality score distribution |
| Auto-Tagged Docs | 0 | 900+ (95%) | Count docs with auto-tags |
| Search Categories | 7 | 12+ | Count unique categories |
| Mobile Load Time | ~5s | <2s | Lighthouse mobile score |
| Index Shards | ~30 | ~50 (finer granularity) | Count shard files |

---

## 🚀 Autonomous Execution Plan

### Night 1: Character Extraction & Tagging
1. Implement enhanced OCR pipeline
2. Add new file number patterns
3. Implement auto-tagging system
4. Run full re-extraction on all docs
5. Validate improvements (sample 50 docs)

### Night 2: Search & Filtering
1. Implement advanced search modes
2. Add person/location search
3. Implement multi-select filters
4. Add fuzzy search
5. Test all search modes

### Night 3: UI/UX Enhancements
1. Add search history and saved searches
2. Implement keyboard shortcuts
3. Improve document viewer (side-by-side, highlights)
4. Optimize mobile experience
5. Test on real mobile devices

### Night 4: Performance & Polish
1. Optimize index loading
2. Add service worker for offline
3. Implement incremental builds
4. Add comprehensive tests
5. Update documentation

---

## 🔐 Safety Guardrails

- **No commits to main without testing**: All changes tested locally first
- **Backup before re-extraction**: Copy `data/` to `data.backup/` before full re-run
- **Preserve original files**: Never modify `data/raw/` PDFs
- **Validate catalog integrity**: Run `make test` after each phase
- **Test in dev environment**: Build to `dist.test/` before overwriting `dist/`
- **Git branching**: Create feature branches per phase (phase-1-ocr, phase-2-search, etc.)
- **Commit messages**: Follow convention (feat:, fix:, docs:, test:)

---

## 📝 Deliverables

1. **Enhanced OCR**: Higher quality text extraction, better metadata
2. **Auto-tagging**: Person, location, date-range, category tags
3. **Advanced search**: Multi-dimensional filtering, fuzzy search, person/location modes
4. **Better UI**: Search history, saved searches, improved viewer, mobile-optimized
5. **Tests**: Comprehensive test suite (pytest + manual)
6. **Documentation**: Updated README, user guide, developer guide
7. **GitHub Pages**: Deployed with all improvements

---

## 🎯 Final Outcome

**Eppie will be a world-class research tool** with:
- ✅ Near-complete OCR coverage (99%+ of image PDFs)
- ✅ Rich auto-tagging (people, places, dates, categories)
- ✅ Powerful multi-dimensional search
- ✅ Fast, mobile-friendly UI
- ✅ Offline-capable (service worker)
- ✅ Comprehensive documentation

**Users will be able to**:
- Search by person name ("Maxwell", "Epstein", "Andrew")
- Search by location ("Little St. James", "New York")
- Filter by date range, document type, quality
- Export search results to CSV
- Use on mobile devices effectively
- Save and share complex searches

---

_Autonomous execution: dev agent, overnight work, report progress via Discord_
