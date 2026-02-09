# Phase 2 Search Features - Test Plan

## Test Date: 2026-02-09

## Features Implemented

### 1. Person Search Mode
- **Implementation**: New search mode that searches across `person_names`, `title`, and `content` fields
- **UI**: Dropdown option "👤 Person" with placeholder "Search by person name (e.g., Maxwell, Epstein)"
- **Test Queries**:
  - "Maxwell" (should return docs mentioning Maxwell)
  - "Epstein" (should return docs mentioning Epstein)
  - "Andrew" (should return docs mentioning Prince Andrew)
  - "Clinton" (should return any Clinton references)

### 2. Location Search Mode
- **Implementation**: New search mode that searches across `locations`, `title`, and `content` fields
- **UI**: Dropdown option "📍 Location" with placeholder "Search by location (e.g., Little St. James, New York)"
- **Test Queries**:
  - "Little St. James" (should return docs about the island)
  - "New York" (should return docs mentioning New York)
  - "Palm Beach" (should return Palm Beach references)
  - "Virgin Islands" (should return USVI references)

### 3. File Number Lookup
- **Implementation**: Exact match search on `extracted_file_numbers` and `id` fields
- **UI**: Dropdown option "🔢 File number" with placeholder "Lookup file number (e.g., EFTA00004051, FBI123456)"
- **Case handling**: Converts query to uppercase for matching
- **Test Queries**:
  - "EFTA00004051" (exact match)
  - "efta00004051" (case insensitive)
  - "FBI" (partial match on FBI numbers)
  - Valid file numbers from actual documents

### 4. Fuzzy Search
- **Implementation**: Applied to full, person, and location search modes
- **Features**:
  - Edit distance 1 for typo tolerance
  - Wildcard matching (prefix/suffix) for partial matches
  - Handles OCR errors and misspellings
- **Test Queries**:
  - "Maxwel" (should find Maxwell with typo)
  - "Epstien" (should find Epstein with typo)
  - "Jamse" (should find James)
  - "Virgi" (should find Virgin/Virginia as prefix match)

### 5. Search Suggestions (Autocomplete)
- **Implementation**: Datalist populated based on search mode
- **Modes**:
  - Person mode: Shows all person names from catalog
  - Location mode: Shows all locations from catalog
  - Tags mode: Shows all tags
  - Full text mode: Mix of top person names, locations, and tags
- **Test**:
  - Switch to person mode → should show person name suggestions
  - Switch to location mode → should show location suggestions
  - Type partial name → browser native autocomplete should filter

### 6. Related Documents
- **Implementation**: Shown at bottom of each result card
- **Algorithm**:
  - High relevance (10 pts × count): Same case numbers
  - Medium relevance (3 pts × count): Same person names
  - Low relevance (2 pts × count): Same locations
  - Date proximity (up to 5 pts): Documents within 30 days
- **Displays**: Top 3 most relevant related documents
- **Test**:
  - Find document with case numbers → verify related docs shown
  - Find document with person names → verify person-based relations
  - Verify related links work (click through)

## Test Execution Plan

### Pre-Test Setup
1. Ensure catalog.json exists with Phase 1 extracted metadata
2. Verify person_names, locations, case_numbers fields populated
3. Build site: `make build` or `python scripts/build_site.py`
4. Start local server: `cd dist && python -m http.server 8000`

### Test Execution Steps

#### Test 1: Person Search Mode
1. Navigate to http://localhost:8000
2. Change search mode to "👤 Person"
3. Verify placeholder changes to "Search by person name..."
4. Type "Max" → verify autocomplete shows "Maxwell" and similar names
5. Search "Maxwell" → verify results show documents with Maxwell in person_names
6. Check result cards show person name badges (👤 Maxwell)
7. Verify fuzzy search: "Maxwel" should still find Maxwell

**Expected Results**:
- [ ] Search mode dropdown includes "👤 Person" option
- [ ] Placeholder updates correctly
- [ ] Autocomplete shows person names
- [ ] Results filtered to person-relevant documents
- [ ] Person name badges displayed
- [ ] Fuzzy matching works (typo tolerance)

#### Test 2: Location Search Mode
1. Change search mode to "📍 Location"
2. Verify placeholder changes to "Search by location..."
3. Type "Little" → verify autocomplete shows "Little St. James" if in catalog
4. Search "New York" → verify results include New York docs
5. Check result cards show location badges (📍 New York)
6. Verify fuzzy search: "Jamse" should find "James"

**Expected Results**:
- [ ] Search mode dropdown includes "📍 Location" option
- [ ] Placeholder updates correctly
- [ ] Autocomplete shows location names
- [ ] Results filtered to location-relevant documents
- [ ] Location badges displayed
- [ ] Fuzzy matching works

#### Test 3: File Number Lookup
1. Find a valid EFTA number from catalog (e.g., open catalog.json, find extracted_file_numbers)
2. Change search mode to "🔢 File number"
3. Verify placeholder changes to "Lookup file number..."
4. Search exact file number (e.g., "EFTA00004051")
5. Verify only documents with that file number appear
6. Test case insensitivity: search "efta00004051" (lowercase)
7. Test partial match: search "EFTA" → should return all EFTA docs

**Expected Results**:
- [ ] Search mode dropdown includes "🔢 File number" option
- [ ] Exact file number returns correct document
- [ ] Case insensitive matching works
- [ ] Partial matching works (prefix search)
- [ ] File number badges displayed in results

#### Test 4: Fuzzy Search Quality
1. Switch to "Full text (fuzzy)" mode
2. Test typo tolerance:
   - Search "Epstien" → should find "Epstein"
   - Search "correspondance" → should find "correspondence"
3. Test partial matching:
   - Search "Vir" → should find "Virgin", "Virginia"
   - Search "Max" → should find "Maxwell", "Maximus", etc.
4. Verify boost scoring: exact match should rank higher than fuzzy match

**Expected Results**:
- [ ] Typos within edit distance 1 return correct results
- [ ] Partial/prefix matching works
- [ ] Exact matches rank higher than fuzzy matches
- [ ] OCR error patterns handled (common misreads)

#### Test 5: Search Suggestions
1. For each search mode, verify appropriate suggestions appear:
   - Person mode → person names
   - Location mode → locations
   - Tags mode → tags
   - Full text mode → mixed suggestions
2. Type partial text and verify browser filters suggestions
3. Select a suggestion → verify search executes

**Expected Results**:
- [ ] Datalist element created with id="searchSuggestions"
- [ ] Input has list="searchSuggestions" attribute
- [ ] Suggestions match current search mode
- [ ] Suggestions update when mode changes
- [ ] Browser native autocomplete works

#### Test 6: Related Documents
1. Search for a document that has case_numbers populated
2. Verify "Related:" section appears at bottom of result card
3. Verify 0-3 related documents shown
4. Click a related document link → verify it navigates correctly
5. Test various relation types:
   - Same case number (should have high relevance)
   - Same person names (medium relevance)
   - Same date range (low-medium relevance)

**Expected Results**:
- [ ] Related section only shows when relations exist
- [ ] Related docs sorted by relevance
- [ ] Links work correctly
- [ ] Truncated titles with ellipsis (...) if > 60 chars
- [ ] Styled with border-left accent color

### Integration Tests

#### Test 7: Combined Features
1. Search "Maxwell" in person mode → verify fuzzy search + related docs
2. Select location from suggestions → verify autocomplete + location search works
3. Use file number lookup → verify related docs based on case numbers
4. Apply filters (year, source) with new search modes → verify compatibility

**Expected Results**:
- [ ] All features work together harmoniously
- [ ] No JavaScript errors in console
- [ ] Performance acceptable (search completes < 500ms)
- [ ] URL state reflects new search modes

#### Test 8: Edge Cases
1. Search with no results in each mode
2. Search with special characters: "St. James", "O'Brien"
3. Search with very long queries (> 100 chars)
4. Search with Unicode/emoji
5. Rapidly switch between search modes while typing

**Expected Results**:
- [ ] Graceful handling of no results
- [ ] Special characters handled correctly
- [ ] Long queries don't break UI
- [ ] Unicode handled properly
- [ ] No race conditions when switching modes

### Browser Compatibility
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

### Performance Metrics
- [ ] Initial page load < 3 seconds (3G connection)
- [ ] Search execution < 500ms
- [ ] Autocomplete responsive (< 100ms)
- [ ] Related docs calculation < 50ms per result

## Test Results

### Execution Date: ___________
### Tester: dev agent (autonomous)

| Test | Pass/Fail | Notes |
|------|-----------|-------|
| Person Search Mode | | |
| Location Search Mode | | |
| File Number Lookup | | |
| Fuzzy Search | | |
| Search Suggestions | | |
| Related Documents | | |
| Combined Features | | |
| Edge Cases | | |
| Browser Compatibility | | |
| Performance | | |

## Known Issues
(Document any bugs or limitations discovered during testing)

## Recommendations
(Suggest improvements or follow-up work)
