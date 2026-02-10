# Eppie Site UX Audit & Improvement Roadmap
**Date:** February 10, 2026  
**Audited by:** Dev Agent (Subagent)  
**Scope:** UX issues, search functionality, categorization accuracy, missing features

---

## Executive Summary

**Overall Assessment:** The Eppie site has a solid foundation with advanced search capabilities and mobile optimization. However, **54.8% of documents lack categorization**, limiting discoverability. The site would significantly benefit from **timeline visualizations, document relationship graphs, enhanced previews**, and better document clustering.

**Critical Issues:**
1. 🔴 **519 of 947 documents (54.8%) are uncategorized** - major metadata gap
2. 🟡 **No timeline visualization** - users can't see temporal relationships
3. 🟡 **No relationship graphs** - connections between documents are hidden
4. 🟡 **Limited document previews** - text snippets only, no thumbnails
5. 🟢 Search functionality is comprehensive and working well

---

## 1. Template UX Issues

### 1.1 **index.html** (Main Search Page)
**Issues Found:**
- ✅ **Good:** Comprehensive filter system with multi-select support
- ✅ **Good:** Accessible skip links and ARIA labels
- ⚠️ **Issue:** No visual preview/thumbnail of documents in results
- ⚠️ **Issue:** Related documents section exists but limited to 3 docs
- ⚠️ **Issue:** No timeline view toggle option
- ⚠️ **Issue:** Category filter shows empty option first (should hide if no categories)
- ⚠️ **Issue:** Search mode dropdown doesn't explain what "fuzzy" means

**Recommendations:**
1. Add document thumbnail previews (first page of PDF as image)
2. Add timeline view toggle (chronological visualization)
3. Add "View as: [Grid | List | Timeline]" switcher
4. Improve category filter to show count of categorized vs uncategorized
5. Add tooltip explaining "fuzzy search" means "tolerates typos"

### 1.2 **detail.html** (Document Detail Page)
**Issues Found:**
- ⚠️ **Issue:** Very minimal - just title, metadata grid, and notes
- ⚠️ **Issue:** No "Related Documents" section (despite app.js having the logic)
- ⚠️ **Issue:** No navigation to next/previous document in results
- ⚠️ **Issue:** No document relationship visualization
- ⚠️ **Issue:** No "People mentioned in this document" section
- ⚠️ **Issue:** No "Locations mentioned" section

**Recommendations:**
1. Add "Related Documents" carousel (use existing `findRelatedDocuments()` function)
2. Add "Next/Previous" navigation based on search context
3. Add "People in this document" expandable section with links to person profiles
4. Add "Locations in this document" section
5. Add "Document Timeline" showing where this doc fits chronologically
6. Add visual preview of first page as thumbnail

### 1.3 **viewer.html** (PDF Viewer)
**Issues Found:**
- ✅ **Good:** Page navigation with prev/next buttons
- ⚠️ **Issue:** No zoom controls (in/out/fit-width/fit-height)
- ⚠️ **Issue:** No text search within PDF
- ⚠️ **Issue:** No page thumbnails sidebar
- ⚠️ **Issue:** No rotation controls
- ⚠️ **Issue:** No download button (only "Original file" link)

**Recommendations:**
1. Add zoom controls (+/- buttons, fit-width, fit-height, percentage dropdown)
2. Add in-PDF text search with highlights
3. Add page thumbnails sidebar for quick navigation
4. Add 90° rotation buttons
5. Add direct "Download PDF" button
6. Add "Copy link to this page" button for deep linking

### 1.4 **emails.html** (Email Browser)
**Issues Found:**
- ✅ **Good:** Email-specific filtering and grouping
- ✅ **Good:** From/To/Subject extraction working
- ⚠️ **Issue:** No threaded conversation view
- ⚠️ **Issue:** No email timeline visualization
- ⚠️ **Issue:** No network graph of email correspondents
- ⚠️ **Issue:** Preview is limited to 200 chars

**Recommendations:**
1. Add conversation threading (group by subject/in-reply-to)
2. Add timeline view showing email activity over time
3. Add network graph visualization of who emailed whom
4. Increase preview to 400 chars or make expandable
5. Add "Show only threads with ≥3 emails" filter
6. Add export to MBOX/EML format

### 1.5 **people.html** (Person Profiles)
**Issues Found:**
- ✅ **Good:** Accordion UI with expandable details
- ✅ **Good:** Timeline and document breakdown
- ⚠️ **Issue:** No relationship graph showing connections between people
- ⚠️ **Issue:** No co-occurrence analysis (who appears in docs together)
- ⚠️ **Issue:** Timeline is text-based, not visual
- ⚠️ **Issue:** No filtering by time period
- ⚠️ **Issue:** Threshold of 5+ mentions is arbitrary - should be configurable

**Recommendations:**
1. Add relationship graph showing people who appear together in documents
2. Add visual timeline (horizontal bar chart by year)
3. Add "Co-mentioned with" section showing top 5 people in same docs
4. Add slider to adjust mention threshold (1-50)
5. Add export person profile as JSON/CSV
6. Add "Compare People" feature (side-by-side comparison)

### 1.6 **stats.html** (Statistics Dashboard)
**Issues Found:**
- ✅ **Good:** Clean layout with charts
- ⚠️ **Issue:** Charts are populated by JavaScript but no visual timeline
- ⚠️ **Issue:** No trend analysis over time
- ⚠️ **Issue:** No heatmap of document releases by source/year
- ⚠️ **Issue:** No quality improvement metrics

**Recommendations:**
1. Add timeline chart showing document releases over time
2. Add heatmap: sources (Y) × years (X) with cell color = doc count
3. Add "Quality Trend" chart showing OCR accuracy improvements
4. Add "Coverage Gap Analysis" showing missing date ranges
5. Add comparison metrics (before/after OCR)

---

## 2. Search Functionality Analysis

### 2.1 **What's Working Well ✅**
1. **Fuzzy search** with edit distance and wildcards - excellent for OCR errors
2. **Multi-field search** with 8 specialized modes (full, person, location, etc.)
3. **Advanced filters** including:
   - Multi-select sources, years, tags
   - Date range filters
   - File size and page count presets
   - OCR quality slider
   - Document type and category
4. **Smart shard loading** - only loads relevant data based on filters
5. **URL-based state** - shareable search links
6. **Autocomplete suggestions** - adapts to search mode
7. **Person name clickability** - filters by person from results

### 2.2 **Missing Search Features**
1. ❌ **Boolean operators** (AND, OR, NOT)
2. ❌ **Phrase search** ("exact phrase" in quotes)
3. ❌ **Proximity search** (words within N words of each other)
4. ❌ **Date range syntax** (e.g., `date:2020..2023`)
5. ❌ **Wildcard search in UI** (users can't enter `Epst*` explicitly)
6. ❌ **Field-specific search** (e.g., `from:Maxwell` in email search)
7. ❌ **Save searches** (bookmark/name common queries)
8. ❌ **Search history** (recently searched terms)
9. ❌ **Similar documents** ("Find more like this" button)
10. ❌ **Export results** to CSV/JSON (only mentioned in README, not visible in UI)

### 2.3 **Search UX Issues**
- No "Search Tips" or "Advanced Search" help modal
- No indication of how many shards are loaded (status is small/hidden)
- Search mode dropdown is not explained to users
- No visual feedback for fuzzy matching (e.g., "Showing results for 'Epstein' including 'Epstien'")

---

## 3. Document Categorization Analysis

### 3.1 **Current State (20 Document Sample)**
Out of 20 randomly sampled documents:
- **17 documents** (85%) had `category: None`
- **3 documents** (15%) were categorized (2 memorandum, 1 email)

### 3.2 **Full Catalog Analysis**
**Total documents:** 947

**Category Distribution:**
| Category | Count | Percentage |
|----------|-------|-----------|
| **Uncategorized** | **519** | **54.8%** |
| Correspondence | 113 | 11.9% |
| Memorandum | 105 | 11.1% |
| Subpoena | 59 | 6.2% |
| Email | 36 | 3.8% |
| Legal Filing | 32 | 3.4% |
| Deposition | 23 | 2.4% |
| Flight Log | 21 | 2.2% |
| Evidence List | 20 | 2.1% |
| Report | 15 | 1.6% |
| Evidence Photo | 2 | 0.2% |
| Case Photo | 2 | 0.2% |

**Categorized:** 428 (45.2%)  
**Uncategorized:** 519 (54.8%)

### 3.3 **Categorization Issues**
1. 🔴 **Over half of documents lack categories** - major discoverability issue
2. Most uncategorized docs are from "DOJ Epstein Library — DOJ Disclosures" source
3. Many documents titled "Utilities — EFTA[number].pdf" - likely generic/administrative
4. No confidence scores for auto-assigned categories
5. No category hierarchy (e.g., "Legal" > "Filing", "Deposition")

### 3.4 **Recommendations**
1. **Priority 1:** Run ML-based categorization on all uncategorized docs
   - Use title + first page OCR text
   - Train classifier on existing 428 categorized docs
   - Assign confidence score (0-100%)
2. Add "Uncategorized" as explicit category in filters with count
3. Add "Suggest Category" crowdsourcing feature (user feedback)
4. Add category hierarchy/tree structure
5. Show category confidence in UI when <80%
6. Regular re-categorization as models improve

---

## 4. Missing Features from Similar Archives

Based on best practices from CourtListener, PACER, National Archives, and other document repositories:

### 4.1 **Timeline Visualizations**
**Status:** ❌ Missing  
**Impact:** High  
**What other archives have:**
- Horizontal timeline showing document releases by date
- Interactive scrubber to filter by time period
- Visual clustering of documents by temporal proximity
- Annotations for major events/milestones

**Implementation:**
- Use D3.js or Chart.js for timeline rendering
- Add "View: Timeline" toggle to search results
- Show document density over time (histogram)
- Click on timeline bar to filter to that time range

### 4.2 **Relationship Graphs**
**Status:** ❌ Missing  
**Impact:** High  
**What other archives have:**
- Network graph showing connections between:
  - People (co-mentions, email threads)
  - Documents (shared case numbers, cross-references)
  - Entities (locations, organizations)
- Interactive graph with zoom, pan, node selection
- Filter graph by relationship type

**Implementation:**
- Use Cytoscape.js or Vis.js for graph rendering
- Build graph data from existing extracted entities (person_names, locations, case_numbers)
- Add "Relationships" tab to person profiles
- Add "Document Network" visualization to stats page

### 4.3 **Document Previews**
**Status:** ⚠️ Partial (text snippets only)  
**Impact:** Medium  
**What other archives have:**
- Thumbnail of first page in search results
- Hover preview showing first 2-3 pages
- Quick preview modal without leaving results
- Preview of highlighted search terms in context

**Implementation:**
- Generate thumbnail images during build (PDF → PNG of page 1)
- Add `data/derived/thumbnails/{id}.png` directory
- Update result cards to show thumbnail + text snippet
- Add hover preview modal with lazy loading

### 4.4 **Advanced Search Filters**
**Status:** ✅ Good, but missing:**
- ❌ Boolean search (AND/OR/NOT)
- ❌ Regex search
- ❌ Batch operations (download multiple, bulk tag)
- ❌ Saved searches
- ❌ Search alerts (notify when new docs match)

### 4.5 **Document Annotations**
**Status:** ❌ Missing  
**Impact:** Medium  
**What other archives have:**
- User highlights (local storage)
- Notes on documents (local or account-based)
- Bookmarks/favorites
- Collections/folders

**Implementation:**
- Use localStorage for client-side annotations
- Add "Annotate" button in viewer
- Add "My Bookmarks" page
- Export annotations as JSON

### 4.6 **Citation & Export**
**Status:** ⚠️ Partial  
**What's missing:**
- Formatted citations (APA, MLA, Chicago, Bluebook)
- BibTeX export
- Bulk download (ZIP of selected docs)
- Print-friendly view
- Email document link

**Implementation:**
- Add "Cite" button with citation formats
- Add "Export" dropdown: [JSON | CSV | BibTeX | ZIP]
- Add "Share" button: [Copy Link | Email | Print]

### 4.7 **Comparative Analysis**
**Status:** ❌ Missing  
**Impact:** Low-Medium  
**What other archives have:**
- Side-by-side document comparison
- Diff view for different versions
- Compare person profiles
- Compare time periods

### 4.8 **Full-Text Highlighting**
**Status:** ⚠️ Partial (in search snippets only)  
**What's missing:**
- Highlight search terms in PDF viewer
- Navigate between highlights (next/prev match)
- Highlight count ("5 matches")

---

## 5. Improvement Roadmap (Prioritized)

### **Phase 1: Critical UX Improvements** (1-2 weeks)
**Priority:** 🔴 High  
**Impact:** High user satisfaction

#### 1.1 Document Thumbnails
- Generate 200x280px PNG thumbnails of first page during build
- Add to search result cards (left side, with text snippet on right)
- Estimated effort: 4 hours

#### 1.2 Related Documents on Detail Page
- Use existing `findRelatedDocuments()` function in detail template
- Show top 5 related docs with relevance explanation
- Estimated effort: 2 hours

#### 1.3 Timeline View Toggle
- Add "View: [List | Timeline]" switcher to search page
- Implement horizontal timeline with year grouping
- Use existing `release_date` field
- Estimated effort: 6 hours

#### 1.4 Enhanced PDF Viewer Controls
- Add zoom controls (+/-, fit-width, fit-height)
- Add rotation buttons (90° increments)
- Add "Download PDF" button
- Estimated effort: 4 hours

#### 1.5 Search Help Modal
- Add "?" button next to search bar
- Explain search modes, fuzzy matching, filters
- Show example queries
- Estimated effort: 3 hours

**Total Phase 1 Effort:** ~19 hours

---

### **Phase 2: Categorization Overhaul** (2-3 weeks)
**Priority:** 🔴 Critical  
**Impact:** Dramatically improves discoverability

#### 2.1 ML-Based Auto-Categorization
- Train classifier on 428 pre-categorized docs
- Use title + first 500 chars of OCR text as features
- Run on all 519 uncategorized docs
- Add confidence score field
- Estimated effort: 16 hours (including data prep, training, validation)

#### 2.2 Category Confidence UI
- Show confidence badges for categories <80%
- Add "Suggest better category" feedback button
- Track user suggestions for model retraining
- Estimated effort: 4 hours

#### 2.3 Category Hierarchy
- Group categories: Legal (filing, deposition, subpoena), Communication (email, correspondence), Evidence (photo, list), etc.
- Update filters to support hierarchy
- Estimated effort: 6 hours

**Total Phase 2 Effort:** ~26 hours

---

### **Phase 3: Relationship Graphs** (2-3 weeks)
**Priority:** 🟡 Medium  
**Impact:** High user engagement, unique feature

#### 3.1 Person Relationship Graph
- Build co-mention graph from existing `person_names` data
- Visualize with Cytoscape.js or Vis.js
- Add to people.html as new tab
- Estimated effort: 12 hours

#### 3.2 Document Relationship Graph
- Build document graph from case numbers, shared people, shared locations
- Add "Document Network" page
- Clickable nodes navigate to document
- Estimated effort: 10 hours

#### 3.3 Email Network Graph
- Visualize email correspondents (From → To)
- Add to emails.html as visualization tab
- Show email volume by edge thickness
- Estimated effort: 8 hours

**Total Phase 3 Effort:** ~30 hours

---

### **Phase 4: Timeline Enhancements** (1 week)
**Priority:** 🟡 Medium  
**Impact:** Better temporal understanding

#### 4.1 Interactive Timeline on Stats Page
- Add D3.js timeline showing doc releases over time
- Interactive scrubber to filter main search
- Histogram with configurable bins (day/week/month/year)
- Estimated effort: 8 hours

#### 4.2 Person Timeline Visualization
- Convert text-based timeline on people.html to visual timeline
- Horizontal bars showing document mentions by year
- Estimated effort: 6 hours

#### 4.3 Email Timeline
- Add timeline view to emails.html
- Show email activity over time
- Estimated effort: 4 hours

**Total Phase 4 Effort:** ~18 hours

---

### **Phase 5: Advanced Search Features** (1-2 weeks)
**Priority:** 🟢 Low-Medium  
**Impact:** Power users, researchers

#### 5.1 Boolean Search
- Parse query for AND, OR, NOT operators
- Update Lunr.js query builder
- Add to search help documentation
- Estimated effort: 6 hours

#### 5.2 Saved Searches
- Store in localStorage or backend (if added)
- Add "Save Search" button
- Add "My Searches" dropdown
- Estimated effort: 5 hours

#### 5.3 Search History
- Track last 20 searches in localStorage
- Add dropdown showing recent searches
- Estimated effort: 3 hours

#### 5.4 Batch Operations
- Add checkboxes to result cards
- "Download selected" → ZIP file
- "Export selected" → CSV/JSON
- Estimated effort: 8 hours

**Total Phase 5 Effort:** ~22 hours

---

### **Phase 6: Document Annotations** (1-2 weeks)
**Priority:** 🟢 Low  
**Impact:** User engagement, return visits

#### 6.1 Local Bookmarks
- Add "Bookmark" button to documents
- Store in localStorage
- Add "My Bookmarks" page
- Estimated effort: 6 hours

#### 6.2 Document Notes
- Add notes field to localStorage
- Show in detail page
- Export notes with document metadata
- Estimated effort: 5 hours

#### 6.3 Highlights
- Add highlight functionality in PDF viewer
- Store highlight regions in localStorage
- Estimated effort: 10 hours

**Total Phase 6 Effort:** ~21 hours

---

### **Phase 7: Polish & Accessibility** (1 week)
**Priority:** 🟢 Low  
**Impact:** Professional appearance, compliance

#### 7.1 Citation Generator
- Add "Cite this document" button
- Support APA, MLA, Chicago, Bluebook formats
- Estimated effort: 4 hours

#### 7.2 Print-Friendly Views
- Add CSS `@media print` rules
- "Print this document" button
- Estimated effort: 3 hours

#### 7.3 Accessibility Audit
- Run WAVE and Lighthouse tests
- Fix any WCAG 2.1 AA violations
- Add keyboard shortcuts documentation
- Estimated effort: 6 hours

#### 7.4 Performance Optimization
- Lazy load images
- Optimize Lunr.js index size
- Service worker for offline support
- Estimated effort: 8 hours

**Total Phase 7 Effort:** ~21 hours

---

## 6. Summary & Recommendations

### **Top 5 Priority Improvements**
1. **Auto-categorize 519 uncategorized documents** (54.8% gap) → ML classifier
2. **Add timeline view** → Users want to see temporal patterns
3. **Add relationship graphs** → Unique feature, high engagement
4. **Add document thumbnails** → Visual search is faster
5. **Enhance PDF viewer** → Zoom, rotation, in-PDF search

### **Quick Wins (< 4 hours each)**
- Add related documents to detail page (2h)
- Add search help modal (3h)
- Add download button to viewer (1h)
- Show category confidence badges (3h)
- Add person relationship stats to profiles (3h)

### **Long-Term Vision**
- Become the most feature-rich public document archive
- Add ML-powered document understanding (summarization, entity extraction)
- Crowdsource metadata improvements
- Build API for researchers
- Add citation tracking (see who's referencing these docs)

### **Estimated Total Effort**
- **Phase 1 (Critical):** 19 hours
- **Phase 2 (Categorization):** 26 hours
- **Phase 3 (Graphs):** 30 hours
- **Phase 4 (Timeline):** 18 hours
- **Phase 5 (Search):** 22 hours
- **Phase 6 (Annotations):** 21 hours
- **Phase 7 (Polish):** 21 hours
- **Total:** ~157 hours (~4 weeks of focused work)

---

## 7. Technical Implementation Notes

### 7.1 **Dependencies to Add**
```json
{
  "chart.js": "^4.4.0",         // Timeline charts
  "cytoscape": "^3.28.1",       // Relationship graphs
  "cytoscape-cose-bilkent": "^4.1.0",  // Graph layout
  "pdf-thumbnail-generator": "^2.0.0"  // Thumbnail generation
}
```

### 7.2 **Build Pipeline Updates**
- Add thumbnail generation step in `scripts/build.py`
- Add ML categorization step (can use scikit-learn or simple rules-based initially)
- Pre-compute relationship graph data during build

### 7.3 **Data Schema Extensions**
Add to `catalog.json`:
```json
{
  "document_category_confidence": 0.87,
  "thumbnail_path": "data/derived/thumbnails/abc123.png",
  "related_document_ids": ["xyz789", "def456"],
  "co_mentioned_people": [["Maxwell", 12], ["Clinton", 8]]
}
```

### 7.4 **Performance Considerations**
- Thumbnails: WebP format for smaller file size
- Graphs: Lazy render on tab switch
- Timeline: Virtual scrolling for large datasets
- Search: Consider switching to MiniSearch (faster than Lunr.js)

---

## 8. Comparable Archives Analysis

### 8.1 **CourtListener (courtlistener.com)**
**Features Eppie is missing:**
- Citation network graphs
- PACER integration
- Judge database
- Opinion clustering by similarity
- Advanced docket search
- Alerts for new filings

**What Eppie does better:**
- Cleaner UI
- Better mobile experience
- More granular filters (OCR quality, file size, etc.)

### 8.2 **DocumentCloud (documentcloud.org)**
**Features Eppie is missing:**
- Inline annotations (public or private)
- Document sections/chapters
- Collaborative projects
- API for embedding documents
- OCR status tracking

**What Eppie does better:**
- Person profiles
- Email-specific browser
- Advanced search modes (person, location, file number)

### 8.3 **The National Archives (archives.gov)**
**Features Eppie is missing:**
- High-resolution image viewer
- Research room booking
- Finding aids
- Collection-level metadata

**What Eppie does better:**
- Full-text search (National Archives has limited search)
- Modern UI/UX
- Mobile optimization
- CSV export

---

## Conclusion

The Eppie site is a **strong foundation** with excellent search capabilities and mobile UX. The **most critical gap is the 54.8% uncategorized documents**, which should be addressed immediately with ML-based categorization.

Adding **timeline views** and **relationship graphs** would differentiate Eppie from other document archives and significantly improve user engagement. **Document thumbnails** and **enhanced PDF viewer controls** are quick wins that dramatically improve UX.

With the proposed 7-phase roadmap (~157 hours), Eppie could become the **gold standard for public document archives**.

---

**End of Audit Report**
