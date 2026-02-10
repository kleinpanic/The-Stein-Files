# Task Documentation - Autonomous Improvement System

## Project: The Stein Files (Epstein Document Archive)
**Version:** 1.5.2  
**Last Updated:** 2026-02-10 03:30 EST  
**Mode:** Fully Autonomous Recursive Improvement

---

## Critical Metrics (Current State)

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| Documents Categorized | 48.8% (462/947) | 95%+ | P0 |
| Email Metadata (From/To) | 0% (0/39) | 100% | P0 |
| People Extracted | 23 unique | 50+ | P1 |
| OCR Coverage | 29.6% (280/947) | 100% of image PDFs | P1 |
| Image PDFs with OCR | 280/344 | 344/344 | P2 |
| Text Quality Avg | 69.4/100 | 80+ | P2 |
| Test Coverage | 77 tests | 100+ | P3 |

---

## Active Tasks (Priority Order)

### P0: Critical Fixes (Must Complete First)

#### Task 1: Fix Email Metadata Regression
**Status:** NOT STARTED  
**Assignee:** dev  
**Estimated Time:** 2h

All 39 emails have NO from/to/subject fields - complete regression from claimed v1.5.1 fix.

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
print(f'Emails with From: {sum(1 for e in emails if e.get(\"from\"))}/{len(emails)}')"
```

---

#### Task 2: Improve Document Categorization
**Status:** NOT STARTED  
**Assignee:** dev  
**Estimated Time:** 6h

485/947 documents (51.2%) are uncategorized. Pattern matching hit OCR quality ceiling.

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
**Status:** NOT STARTED  
**Assignee:** dev (can delegate to subagent)  
**Estimated Time:** 4h

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
**Status:** PARTIAL (280/344 image PDFs)  
**Assignee:** dev  
**Estimated Time:** 8h (can run overnight)

344 image PDFs exist, only 280 have OCR applied.

**Actions:**
1. [ ] Identify 64 missing OCR documents
2. [ ] Run Tesseract OCR on missing documents
3. [ ] Validate OCR text quality
4. [ ] Re-categorize newly OCR'd documents
5. [ ] Update catalog with OCR results

---

### P2: Quality Improvements

#### Task 5: Add Relationship Extraction
**Status:** NOT STARTED  
**Assignee:** research subagent  
**Estimated Time:** 12h

Extract connections between people and build network data.

**Actions:**
1. [ ] Parse "X to Y" patterns in emails/memos
2. [ ] Extract meeting attendees from documents
3. [ ] Build relationship graph JSON
4. [ ] Create visualization component
5. [ ] Add to stats dashboard

---

#### Task 6: Timeline Extraction & Normalization
**Status:** NOT STARTED  
**Assignee:** dev  
**Estimated Time:** 4h

Normalize all dates to ISO8601 for timeline queries.

**Actions:**
1. [ ] Parse all date formats (MM/DD/YYYY, Month DD, YYYY, etc.)
2. [ ] Normalize to ISO8601
3. [ ] Add date range filtering to UI
4. [ ] Create timeline visualization

---

### P3: Polish & Testing

#### Task 7: Increase Test Coverage
**Status:** 77 tests  
**Target:** 100+ tests  
**Assignee:** dev

**Actions:**
1. [ ] Add tests for email metadata extraction
2. [ ] Add tests for person extraction accuracy
3. [ ] Add tests for categorization accuracy
4. [ ] Add integration tests for full pipeline
5. [ ] Add UI snapshot tests

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
- [ ] Categorization: 85%+ documents categorized
- [ ] People: 40+ unique people extracted
- [ ] OCR: 100% of image PDFs processed
- [ ] Tests: 90+ tests passing
- [ ] No regressions from current functionality
- [ ] All changes deployed to GitHub Pages

---

## Notes for Next Session

_Updated each heartbeat with learnings and blockers_

