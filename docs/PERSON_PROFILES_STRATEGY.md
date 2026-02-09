# Person Profiles Strategy & Decision Matrix

**Date:** 2026-02-09  
**Branch:** phase-2-advanced-search  
**Task:** Strategic planning for person-specific sections in Eppie

---

## 1. Data Analysis Summary

### Extracted Data Reality
- **Total unique people:** 124 (not 194 as initially estimated)
- **Major people (5+ mentions):** 4 (but 1 is data quality issue)
- **Total documents:** 947

### Major People Ranking

| Rank | Name | Mentions | Document Types | Status |
|------|------|----------|----------------|--------|
| 1 | Jeffrey Epstein | 119 | Deposition (22), Memorandum (20), Correspondence (17), Subpoena (15), Email (9), Flight logs (5) | ✓ Real person |
| 2 | Ghislaine Maxwell | 67 | Correspondence (14), Deposition (13), Legal filing (9), Subpoena (7), Email (7) | ✓ Real person |
| 3 | Lesley Groff | 20 | Correspondence (12), Email (4), Flight log (2) | ✓ Real person (assistant) |
| 4 | Supervising Title | 5 | Subpoena (5) | ✗ Data extraction error |

### Notable Near-Threshold People (Below 5 mentions)
- **Prince Andrew:** 4 mentions (famous, high interest)
- **Alan Dershowitz:** 3 mentions (lawyer, famous)

### Data Quality Issues
- Many extraction errors: "Epstein\nDate", "Maxwell Trial", "Epstein\n\n\n       Sure", etc.
- These are parsing artifacts, not real people
- Need to clean data before building person profiles

---

## 2. Upgrade Ideas Evaluation

### ✅ ACCEPTED IDEAS

#### A1. Dedicated Person Pages (Top 2-3 only)
**Example:** `/people/jeffrey-epstein.html`, `/people/ghislaine-maxwell.html`

**Pros:**
- High value: Core figures people research
- Follows existing emails.html pattern
- Centralizes all info about a person
- SEO-friendly individual URLs

**Cons:**
- Medium effort: Template + build script changes
- Only valuable for major figures (not worth it for 1-2 mention people)

**Decision:** ACCEPT for Jeffrey Epstein and Ghislaine Maxwell only. Possibly Lesley Groff.

**Implementation Effort:** Medium (2-3 hours)
- Create `site/templates/person.html` 
- Add `build_person_pages()` function to `build_site.py`
- Generate JSON data per person
- Add JavaScript for filtering/sorting

---

#### A2. Person Hub Landing Page
**Example:** `/people/index.html` or `/people.html`

**Pros:**
- Low effort: Simple list with counts
- Good entry point for discovery
- Shows data at a glance
- Links to individual person pages

**Cons:**
- Limited value with only 2-3 major people
- Might feel empty

**Decision:** ACCEPT - creates a clear navigation structure even with few people.

**Implementation Effort:** Low (1 hour)
- Simple template with sorted list
- Links to person detail pages
- Show mention counts and top document types

---

#### A3. Timeline View (on person pages)
**Example:** Chronological list of document appearances

**Pros:**
- High value: Shows involvement over time
- Dates already extracted from documents
- Easy to implement with existing data
- Helps understand sequence of events

**Cons:**
- Some documents lack dates (will need "unknown date" bucket)
- Requires date parsing/sorting

**Decision:** ACCEPT - integrate into person detail pages, not standalone.

**Implementation Effort:** Low (integrated into A1, ~1 hour additional)
- Sort documents by `extracted_dates` or `release_date`
- Group by year
- Simple chronological list

---

#### A4. Document Type Breakdown (on person pages)
**Example:** Visual breakdown: "Deposition (22), Email (9), Flight logs (5)..."

**Pros:**
- Very low effort: data already computed
- Shows nature of involvement
- Helps users understand context
- Could use simple bar charts or percentages

**Cons:**
- None significant

**Decision:** ACCEPT - integrate into person detail pages.

**Implementation Effort:** Very Low (30 min)
- Already have category counts from analysis
- Simple HTML/CSS visualization
- No JavaScript needed

---

#### A5. Quick Filters on Main Search
**Example:** Click "Jeffrey Epstein" → search filtered to his documents

**Pros:**
- High value: Makes search more powerful
- Low effort: Just URL parameter handling
- Leverages existing search infrastructure
- Improves discoverability

**Cons:**
- Need to ensure person names are clickable
- URL state management

**Decision:** ACCEPT - add clickable person tags to search results and person pages.

**Implementation Effort:** Low (1 hour)
- Add click handlers to person names in search results
- Set `?mode=person&q=Jeffrey+Epstein` URL params
- Existing search already supports person mode

---

### ❌ REJECTED IDEAS

#### R1. Network Graph (Co-occurrence Visualization)
**Example:** D3.js graph showing person connections

**Pros:**
- Cool visualization
- Shows relationships

**Cons:**
- High effort: Requires D3.js, complex layout algorithms
- Low value: With only 2-3 major people, connections are obvious
- Overkill for dataset size
- Maintenance burden

**Decision:** REJECT - not worth the effort for this dataset size. Could reconsider if data grows to 20+ major people.

---

#### R2. Co-occurrence Analysis Tables
**Example:** "Most frequently mentioned alongside: Maxwell (45 docs), Groff (12 docs)..."

**Pros:**
- Shows relationships
- Interesting data mining

**Cons:**
- Medium effort: Requires pairwise analysis across all documents
- Medium value: Limited insight with so few major people
- Most co-occurrences are obvious (Epstein + Maxwell)

**Decision:** REJECT for now - can add later if dataset grows. Would be 1-2 hours of work for limited value.

---

## 3. Implementation Plan

### Phase 1: Data Preparation (30 min)
1. ✓ Run person analysis script (already done)
2. Create cleaned person data JSON (filter out extraction errors)
3. Generate per-person document lists with full metadata

### Phase 2: Person Hub Page (1 hour)
1. Create `site/templates/people.html`
2. Add `build_people_hub()` to `build_site.py`
3. List all major people with:
   - Mention count
   - Top 3 document types
   - Link to detail page

### Phase 3: Person Detail Pages (2-3 hours)
1. Create `site/templates/person.html` (follow emails.html pattern)
2. Add `build_person_pages()` to `build_site.py`
3. For each major person, show:
   - Total mentions
   - Document type breakdown (bar chart or list)
   - Timeline view (chronological list grouped by year)
   - Full document list with filters
   - Link back to hub

### Phase 4: Search Integration (1 hour)
1. Make person names clickable in search results
2. Add URL param support: `?mode=person&q=Name`
3. Add "View profile" link next to person names (if major person)

### Phase 5: Navigation & Polish (30 min)
1. Add "People" link to main navigation
2. Update README/docs
3. Test all links and filters

**Total estimated effort:** 5-6 hours

---

## 4. Technical Requirements Checklist

- [x] Must work on GitHub Pages (static site only)
- [x] Must use existing Phase 1 data (catalog.json person_names)
- [x] Threshold: 5+ mentions for "major person" (only 2-3 qualify)
- [x] Must integrate cleanly with existing UI
- [x] Follow existing patterns (emails.html as template)

---

## 5. Data Quality Improvements Needed

Before implementation, clean person_names data:
- Remove obvious extraction errors ("Epstein\nDate", "Maxwell Trial", etc.)
- Normalize names (handle variations like "Jeffrey Epstein" vs "Epstein, Jeffrey")
- Add manual corrections for high-value people
- Document cleaning process in scripts

---

## 6. Success Metrics

**What defines success:**
1. Users can quickly find all documents mentioning Epstein or Maxwell
2. Timeline view helps understand chronology
3. Document type breakdown provides context
4. Search integration makes person filtering seamless
5. Load time remains fast (static generation)

**What we're NOT trying to do:**
- Build a social network graph
- Compete with interactive visualization tools
- Handle 100+ people (current dataset: 2-3 major people)
- Real-time updates (static site is fine)

---

## 7. Future Considerations (Post-Implementation)

**If dataset grows (50+ major people):**
- Consider adding network graph
- Add co-occurrence tables
- Implement faceted search by person
- Add person photo galleries (if available)

**If new data sources added:**
- Automated person name normalization
- Entity resolution (same person, different name formats)
- Relationship extraction from text

**For now:** Keep it simple, focused, and maintainable.

---

## 8. Final Decision Summary

| Feature | Status | Reason | Effort |
|---------|--------|--------|--------|
| Person detail pages (top 2-3) | ✅ ACCEPT | High value, follows existing patterns | Medium |
| Person hub page | ✅ ACCEPT | Good entry point | Low |
| Timeline view | ✅ ACCEPT | High value, easy to implement | Low |
| Document type breakdown | ✅ ACCEPT | Already have data, very easy | Very Low |
| Search quick filters | ✅ ACCEPT | Makes search powerful | Low |
| Network graph | ❌ REJECT | Overkill for 2-3 people | High |
| Co-occurrence analysis | ❌ REJECT | Limited value with small dataset | Medium |

**Total accepted features:** 5  
**Total rejected features:** 2  
**Estimated total implementation time:** 5-6 hours

---

**Next Step:** Proceed with implementation, starting with data preparation.
