# Endpoint Review Checklist

Review these endpoints/pages after every change. Take screenshots, note issues, verify functionality.

## Site URLs

**Local**: http://localhost:8000  
**Production**: https://kleinpanic.github.io/The-Stein-Files/

---

## Endpoints to Review

### 1. Main Search Page
**URL**: `/` or `/index.html`

**Check**:
- [ ] Search box functional
- [ ] All 8 search modes selectable
- [ ] Filters populate correctly (sources, years, categories, etc.)
- [ ] Advanced filters work (date range, file size, page count, OCR quality)
- [ ] Search results display (should show 947 total)
- [ ] Document cards show: title, date, type, quality, preview text
- [ ] Pagination/infinite scroll works
- [ ] Export CSV button present
- [ ] Share button present
- [ ] No JavaScript console errors

**Screenshot**: `screenshots/index-YYYY-MM-DD.png`

**Changes this session**:
- (Document what changed)

---

### 2. Document Detail Page
**URL**: `/detail.html?id=<doc-id>`  
**Test with**: Random document ID from catalog

**Check**:
- [ ] Document title displays
- [ ] Metadata grid shows all fields
- [ ] File info (size, pages, type) correct
- [ ] Quality score visible
- [ ] Category displays
- [ ] Person names (if present)
- [ ] Locations (if present)
- [ ] Dates extracted (if present)
- [ ] "View PDF" button works
- [ ] Related documents section (if implemented)
- [ ] No missing data (or "[Not visible]" shown appropriately)

**Screenshot**: `screenshots/detail-YYYY-MM-DD.png`

**Changes this session**:
- (Document what changed)

---

### 3. PDF Viewer
**URL**: `/viewer.html?pdf=<path>`  
**Test with**: Any PDF from catalog

**Check**:
- [ ] PDF loads and renders
- [ ] Page navigation works (prev/next)
- [ ] Page indicator correct (e.g., "Page 1 of 10")
- [ ] Loading states display
- [ ] Error messages if PDF fails to load
- [ ] Link to original file works
- [ ] No CORS errors (check console)
- [ ] Fallback UI shows if LFS bandwidth exhausted

**Screenshot**: `screenshots/viewer-YYYY-MM-DD.png`

**Changes this session**:
- (Document what changed)

---

### 4. People Page
**URL**: `/people.html`

**Check**:
- [ ] Number of people matches threshold (currently 1+ = 23 people)
- [ ] Accordion UI works (click to expand)
- [ ] Each person shows: mention count, top categories
- [ ] Timeline displays when expanded
- [ ] Document list shows when expanded
- [ ] Links to documents work
- [ ] No duplicate people
- [ ] People sorted by mention count (descending)

**Screenshot**: `screenshots/people-YYYY-MM-DD.png`

**Changes this session**:
- (Document what changed)

**People visible** (document count):
- Jeffrey Epstein: 221
- Ghislaine Maxwell: 112
- Leon Black: 41
- (List others if changed)

---

### 5. Emails Page
**URL**: `/emails.html`

**Check**:
- [ ] Email count correct (currently ~155)
- [ ] From/To/Subject fields populated (or show "[Not visible]")
- [ ] No blank fields without explanation
- [ ] Group by options work (Chronological, Sender, Recipient)
- [ ] Sort options work (Newest first, Oldest first)
- [ ] Filter tabs work (All, Epstein-Related, Email, Correspondence)
- [ ] Email cards display correctly
- [ ] Click to expand shows full email
- [ ] Export CSV button works

**Screenshot**: `screenshots/emails-YYYY-MM-DD.png`

**Changes this session**:
- (Document what changed)

**Email Quality Check** (sample 5 random):
| Document | From | To | Subject | Issue? |
|----------|------|----|---------|----|
| 1. | | | | |
| 2. | | | | |
| 3. | | | | |
| 4. | | | | |
| 5. | | | | |

---

### 6. Sources Page
**URL**: `/sources.html`

**Check**:
- [ ] All sources listed (currently 4 active)
- [ ] Document counts correct per source
- [ ] Links to source descriptions work
- [ ] Status indicators correct

**Screenshot**: `screenshots/sources-YYYY-MM-DD.png`

**Changes this session**:
- (Document what changed)

---

### 7. Stats Page
**URL**: `/stats.html`

**Check**:
- [ ] PDF type breakdown (text/image/hybrid) correct
- [ ] Quality distribution chart displays
- [ ] OCR status shows correct counts
- [ ] Category breakdown matches catalog
- [ ] Source-level statistics correct
- [ ] Charts render without errors

**Screenshot**: `screenshots/stats-YYYY-MM-DD.png`

**Changes this session**:
- (Document what changed)

**Current Stats** (for validation):
- Total documents: 947
- Categorized: 462/947 (48.8%)
- OCR applied: 321
- PDF types: text (497), hybrid (106), image (344)

---

## API/Data Endpoints

### 8. Catalog JSON
**URL**: `/data/meta/catalog.json`

**Check**:
- [ ] Valid JSON (no parse errors)
- [ ] Document count: 947
- [ ] Required fields present: id, title, file_path, text_quality_score
- [ ] New fields added (if applicable)
- [ ] No null/undefined where not expected
- [ ] File size reasonable (<50MB)

**Sample check**: First 3 documents have complete metadata

---

### 9. People JSON
**URL**: `/data/derived/people.json`

**Check**:
- [ ] Valid JSON
- [ ] threshold_mentions field correct
- [ ] People count matches UI
- [ ] Each person has: name, mentions, documents array
- [ ] No duplicate entries

**Current count**: 23 people (1+ mentions)

---

### 10. Search Index Shards
**URLs**: `/data/derived/search_index_shard_*.json`

**Check**:
- [ ] All 3 shards present (shard_0, shard_1, shard_2)
- [ ] Valid JSON
- [ ] Total documents across shards = 947
- [ ] No missing documents
- [ ] Search fields populated (title, content, metadata)

---

## Regression Checks

After any change, verify these still work:

- [ ] Search functionality (try 3 different queries)
- [ ] Filtering (try different categories/years)
- [ ] Navigation between pages
- [ ] PDF viewing
- [ ] Mobile responsiveness (check on narrow viewport)
- [ ] No broken links
- [ ] No 404 errors in console
- [ ] No JavaScript errors in console

---

## Screenshot Protocol

**When to take screenshots**:
- Before starting work (baseline)
- After each significant change
- Before merging to main
- After deployment (verify live matches local)

**Naming convention**:
```
screenshots/
  index-baseline-2026-02-10.png
  index-after-person-fix-2026-02-10.png
  people-before-threshold-change-2026-02-10.png
  people-after-threshold-change-2026-02-10.png
  emails-after-metadata-fix-2026-02-10.png
```

**Storage**:
- Keep in `screenshots/` directory
- Add to .gitignore (don't commit)
- Reference in commit messages/documentation
- Delete old screenshots after 30 days

---

## Review Template

Use this template after each review:

```markdown
## Endpoint Review - YYYY-MM-DD

### Changes Made:
- (Brief description)

### Endpoints Checked:
- [x] Main Search: ✅ Working, no issues
- [x] Document Detail: ✅ Working, metadata improved
- [x] PDF Viewer: ⚠️ Minor issue: loading spinner not showing
- [x] People: ✅ Now showing 23 people (was 12)
- [x] Emails: ✅ Blank fields fixed
- [x] Sources: ✅ No changes, still working
- [x] Stats: ✅ No changes, still working
- [ ] Catalog JSON: Skipped (no changes)
- [ ] People JSON: Checked, valid
- [x] Search Index: ✅ No changes

### Issues Found:
1. PDF viewer loading spinner missing → Fixed in next commit
2. Email #47 still has garbled From field → Investigated, OCR limitation

### Screenshots Taken:
- screenshots/people-after-threshold-2026-02-10.png
- screenshots/emails-after-metadata-fix-2026-02-10.png

### Regressions:
None found

### Ready for merge to main?
Yes / No (explain why)
```

---

## Automation (Future)

Consider automating some checks:
- Playwright tests for UI regression
- JSON schema validation
- Link checker
- Console error detection
- Screenshot diff tool

But for now: **manual review every time**.
