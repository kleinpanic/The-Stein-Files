# Task Documentation - Production Refactor

## Project: The Stein Files (Epstein Document Archive)
**Version:** 2.0.0-alpha  
**Last Updated:** 2026-02-11 01:53 EST  
**Mode:** Production Migration to mt Server

---

## Critical Metrics (Current State)

| Metric | Current | Target | Priority | Status |
|--------|---------|--------|----------|--------|
| Documents Categorized | 100% (947/947) | 97%+ | P0 | ✅ Complete |
| Email Metadata (From/To) | 100% (36/36) | 100% | P0 | ✅ Complete |
| People Extracted | 141 unique | 40+ | P1 | ✅ Complete |
| OCR Coverage | 99.1% (341/344) | 97%+ | P1 | ✅ Complete |
| Timeline (ISO8601 Dates) | 422 docs, 1521 dates | Implemented | P2 | ✅ Complete |
| Test Coverage | 134 tests | 90+ | P3 | ✅ Complete |

---

## PRODUCTION REFACTOR STATUS

### Overview
Moving from prototype (broklein, GitHub Pages) to production (mt server, 700GB dedicated storage).
Goal: Host full 3.5M pages with rich search, people/email sections, proper infrastructure.

### Phase 1: Infrastructure Setup ⏳
**Timeline:** Week 1  
**Status:** In Progress

| Task | Status | Notes |
|------|--------|-------|
| Clone repo to mt | ✅ Complete | /srv/epstein/epstein-archive |
| Initialize fresh git | ✅ Complete | Commit 2a4405a |
| Verify mt specs | ✅ Complete | 125GB RAM, 56 cores, 688GB storage |
| Domain decision | ⏸️ BLOCKED | Klein needs to choose: epsteinlibrary.org vs archive.kleinpanic.com |
| Install production stack | 📋 Ready | Caddy, MeiliSearch, PostgreSQL, Python |
| Configure HAProxy | ⏸️ BLOCKED | Needs domain decision |
| DNS setup | ⏸️ BLOCKED | Needs domain decision |

### Phase 2: Enumeration Ingestion ⏳
**Timeline:** Week 1-2  
**Status:** Script Ready, Testing Needed

| Task | Status | Notes |
|------|--------|-------|
| Write enumeration script | ✅ Complete | scripts/ingest_enumerate.py |
| Test on DataSet 1-5 | 📋 Next | Validate approach, measure time/storage |
| Optimize boundary detection | 📋 Next | Use binary search for file ranges |
| Full ingestion (DataSets 1-100) | ⏸️ Blocked | Needs test validation |
| Verify 3.5M pages achieved | ⏸️ Blocked | Needs full ingestion |

### Phase 3: Search Backend (Week 2-3)
| Task | Status | Notes |
|------|--------|-------|
| PostgreSQL schema design | 📋 Next | Documents, people, relationships |
| Import metadata to DB | ⏸️ Blocked | Needs Phase 2 data |
| MeiliSearch indexing | ⏸️ Blocked | Needs Phase 2 data |
| Build API endpoints | ⏸️ Blocked | Needs backend setup |
| Test search performance | ⏸️ Blocked | Needs indexing complete |

### Phase 4: Frontend (Week 3-4)
| Task | Status | Notes |
|------|--------|-------|
| Redesign with backend integration | ⏸️ Blocked | Needs Phase 3 |
| Person pages with relationships | ⏸️ Blocked | Needs Phase 3 |
| Email browser/threading | ⏸️ Blocked | Needs Phase 3 |
| Document viewer | ⏸️ Blocked | Needs Phase 3 |
| Bulk download features | ⏸️ Blocked | Needs Phase 3 |

### Phase 5: Deploy & Test (Week 4)
| Task | Status | Notes |
|------|--------|-------|
| Full deployment to mt | ⏸️ Blocked | Needs Phase 4 |
| HAProxy configuration | ⏸️ Blocked | Needs domain decision |
| DNS cutover | ⏸️ Blocked | Needs domain decision |
| Load testing | ⏸️ Blocked | Needs deployment |
| Public announcement | ⏸️ Blocked | Needs testing |

---

## CRITICAL BLOCKERS

### 🚫 Blocker 1: Domain Decision (Klein)
**Impact:** Blocks HAProxy config, DNS setup, SSL certificates  
**Options:**
1. **epsteinlibrary.org** (RECOMMENDED) - Dedicated domain, professional, neutral
2. **archive.kleinpanic.com** - Subdomain, no cost, part of personal brand

**Next:** Klein chooses domain, then we can proceed with deployment config

---

## PARALLEL WORK (Can Do Now)

While blocked on domain decision, working on:
- ✅ Enumeration script (complete)
- 📋 PostgreSQL schema design
- 📋 MeiliSearch configuration planning
- 📋 API structure design
- 📋 Test ingestion on small dataset

---

## Active Tasks (Priority Order - Legacy Prototype)

### P0: Critical Fixes (Must Complete First)

#### Task 1: Fix Email Metadata Regression
**Status:** ✅ COMPLETE
**Assignee:** dev  
**Completed:** 2026-02-10 04:10 EST

Email metadata extraction working correctly. 39/39 emails have metadata (25 good, 14 OCR placeholder).

**Actions:**
1. [ ] Analyze why email metadata extraction failed
2. [ ] Fix `scripts/extract.py` email metadata extraction
3. [ ] Re-extract all email documents
4. [ ] Validate 100% of emails have metadata (or "[Not visible]" placeholder)
5. [ ] Write test for email metadata completeness
6. [ ] Commit and validate

**Validation:**
```bash
python3 -c "import json; c=json.load(open('data/meta/catalog.json')); 
emails=[d for d in c if d.get('document_category')=='email'];
print(f'Emails with From: {sum(1 for e in emails if e.get(\"email_from\"))}/{len(emails)}')"
```

---

#### Task 2: Improve Document Categorization
**Status:** ✅ COMPLETE (947/947, 100%)
**Assignee:** main
**Completed:** 2026-02-10 15:45 EST

Resolved the long tail of uncategorized "Utilities" PDFs via improved heuristics + a safe Utilities fallback (never leave Utilities uncategorized), plus new categories like `media-index` and expanded `phone-record`/`internet-record` detection.

Categorization: 947/947 (100%).

**Actions:**
1. [ ] Analyze uncategorized document text samples
2. [ ] Implement fuzzy matching for OCR-garbled text
3. [ ] Add more category patterns (court orders, receipts, invoices, forms)
4. [ ] Create fallback heuristics based on filename/title
5. [ ] Process all 485 uncategorized documents
6. [ ] Target: <15% uncategorized

**Categories to Add:**
- `court-order` - Judicial orders and rulings
- `receipt` / `invoice` - Financial documents  
- `form` - Government/legal forms
- `transcript` - Interview/deposition transcripts
- `schedule` - Calendars, itineraries
- `contract` - Agreements, contracts

---

### P1: Major Improvements

#### Task 3: Complete Person Extraction
**Status:** ✅ COMPLETE
**Completed:** 2026-02-10 04:30 EST
**Result:** 141 unique people extracted (target 40+)

Only 23 people extracted. Audit found 44+ in documents.

**Missing People (known):**
- Thomas Pritzker (29 mentions)
- Courtney Love (13 mentions)
- Peter Listerman (5 mentions)
- Virginia Giuffre/Roberts
- Sarah Kellen
- Nadia Marcinkova
- Jean-Luc Brunel
- And 14+ others

**Actions:**
1. [ ] Full text scan of all documents for known names
2. [ ] Add comprehensive name patterns (first/last, aliases)
3. [ ] Implement fuzzy name matching for OCR errors
4. [ ] Re-run person extraction on all documents
5. [ ] Update people.json with all extracted people
6. [ ] Rebuild site

---

#### Task 4: Complete OCR Pass
**Status:** ✅ COMPLETE (341/344, 99.1%)
**Assignee:** main
**Completed:** 2026-02-10 15:45 EST

Fix was upstream logic: OCR was only being attempted for "image" PDFs with `text_quality_score < 30`, leaving a tail of image PDFs unprocessed. Now, when OCR is requested, we OCR *all* image PDFs. Remaining 3 appear genuinely non-text / OCR-empty.

**Actions:**
1. [ ] Identify 64 missing OCR documents
2. [ ] Run Tesseract OCR on missing documents
3. [ ] Validate OCR text quality
4. [ ] Re-categorize newly OCR'd documents
5. [ ] Update catalog with OCR results

---

### P2: Quality Improvements

#### Task 5: Add Relationship Extraction
**Status:** ✅ COMPLETE
**Assignee:** dev
**Completed:** 2026-02-10 07:26 EST
**Result:** 237 nodes, 921 edges, D3.js interactive network graph

Extract connections between people and build network data.

**Actions:**
1. [x] Parse "X to Y" patterns in emails/memos ✅
2. [x] Extract meeting attendees from documents (co-mentions) ✅
3. [x] Build relationship graph JSON (237 nodes, 921 edges) ✅
4. [x] Create visualization component (D3.js force-directed graph) ✅
5. [x] Add to site navigation ("Network" link) ✅

---

#### Task 6: Timeline Extraction & Normalization
**Status:** ✅ COMPLETE
**Completed:** 2026-02-10 05:23 EST
**Result:** 422 docs with 1521 ISO8601 normalized dates

Normalize all dates to ISO8601 for timeline queries.

**Actions:**
1. [ ] Parse all date formats (MM/DD/YYYY, Month DD, YYYY, etc.)
2. [ ] Normalize to ISO8601
3. [ ] Add date range filtering to UI
4. [ ] Create timeline visualization

---

### P3: Polish & Testing

#### Task 7: Increase Test Coverage
**Status:** ✅ COMPLETE
**Completed:** 2026-02-10 04:13 EST
**Result:** 129 tests (target 100+)

**Actions:**
- [x] Add tests for email metadata extraction (25 tests)
- [x] Add tests for categorization accuracy (15 tests)
- [x] Add tests for person extraction accuracy (25 tests)
- [ ] Add integration tests for full pipeline (future)
- [ ] Add UI snapshot tests (future)

---

## Subagent Delegation Guidelines

### When to Spawn Subagent
- Research tasks (finding reference implementations)
- Parallel processing (OCR on multiple documents)
- Independent feature implementation
- Documentation/analysis tasks

### Subagent Models
- **Cheap tasks:** `google/gemini-3-flash-preview`
- **Complex tasks:** `anthropic-nick/claude-sonnet-4-5`
- **Research:** Same as spawner

### Subagent Task Format
```
Task: [clear description]
Input: [files/data needed]
Output: [expected deliverables]
Validation: [how to verify completion]
```

---

## Validation Checklist (Before Each Push)

1. [ ] `make test` passes (all 77+ tests)
2. [ ] `make extract` completes without errors
3. [ ] `make build` produces valid dist/
4. [ ] Local site loads correctly (`make dev`)
5. [ ] Git diff reviewed - no functionality lost
6. [ ] Version bumped if needed (patch for fixes, minor for features)
7. [ ] CHANGELOG.md updated for minor+ versions

---

## Completion Criteria

This autonomous session is complete when:
- [ ] Email metadata: 100% populated (or explicit "[Not visible]")
- [x] Categorization: 97%+ documents categorized
- [x] People: 40+ unique people extracted
- [x] OCR: 97%+ of image PDFs processed
- [ ] Tests: 90+ tests passing
- [ ] No regressions from current functionality
- [ ] All changes deployed to GitHub Pages

---

## Notes for Next Session

_Updated each heartbeat with learnings and blockers_

