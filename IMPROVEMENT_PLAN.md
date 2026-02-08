# Eppie Improvement Plan - 2026-02-08

## Critical Issues

### 1. PDF Viewer Not Working ❌ BLOCKING
**Problem:** PDFs don't render in iframe on GitHub Pages
**Root cause:** GitHub raw URLs for LFS files don't work in iframes (CORS/headers)
**Solutions:**
- **Option A:** Use PDF.js (client-side PDF rendering) - RECOMMENDED
- **Option B:** Serve PDFs through GitHub Pages directly (copy to dist/)
- **Option C:** Use external PDF viewer service (https://mozilla.github.io/pdf.js/web/viewer.html?file=...)

**Implementation:** Option A (PDF.js)
- Add PDF.js to site/assets/
- Modify viewer.html to use PDF.js instead of iframe
- Keep fallback link to GitHub raw

### 2. Text Extraction Failure ❌ BLOCKING
**Problem:** All extracted text files are 0 bytes
**Root cause:** After LFS migration, local files are pointers, not PDFs
**Solution:** `git lfs pull` before extraction in CI and locally

### 3. Poor Text Quality (OCR Issues)
**Problem:** Extracted text shows garbled content like "DATE ___17-/_ 42-/"
**Root cause:** Image-only PDFs with poor OCR or no embedded text
**Solutions:**
- Detect PDF type (text-based vs image-only)
- For image-only: use better OCR (Tesseract, AWS Textract, etc.)
- Label files by type in catalog

## Feature Enhancements

### 4. File Type Detection & Labeling
**Add to catalog:**
- `pdf_type`: "text" | "image" | "hybrid"
- `has_extractable_text`: boolean
- `ocr_quality`: "high" | "medium" | "low" | "none"
- `page_count`: number
- `file_size`: number
- `document_type`: "evidence-list" | "correspondence" | "memo" | etc.

### 5. Content-Based Tagging
**Auto-extract:**
- Dates (from filename and content)
- Case numbers (regex patterns)
- Named entities (people, organizations, locations)
- Document categories

### 6. Mobile Responsiveness
**Current issues:**
- UI not optimized for small screens
- Tables overflow
- Buttons too close
**Fixes:**
- CSS media queries
- Touch-friendly buttons
- Collapsible filters
- Responsive grid

### 7. Source Completeness
**Check for missing sources:**
- House Committee disclosures (33K pages) - requires Google Drive adapter
- Any new DOJ releases
- Other agency releases

### 8. Enhanced Metadata Display
**Show in UI:**
- File numbers (EFTA00000001, etc.)
- File types with icons
- Page counts
- File sizes
- Quality indicators
- Content summary

## Implementation Plan

### Phase 1: Fix Critical Issues (PRIORITY)
1. Pull LFS files: `git lfs pull`
2. Re-run extraction locally
3. Implement PDF.js viewer
4. Test locally
5. Push and verify on Pages

### Phase 2: Text Extraction Improvements
1. Add PDF type detection (pypdf2 or pdfminer)
2. Implement Tesseract OCR for image PDFs
3. Quality scoring algorithm
4. Update catalog with new fields
5. Re-extract all files

### Phase 3: UI/UX Enhancements
1. Add file type icons and labels
2. Mobile CSS improvements
3. Advanced filters (by type, quality, date, etc.)
4. Content-based tags display
5. Metadata enrichment

### Phase 4: Source Expansion
1. Research available sources
2. Implement Google Drive adapter (if needed)
3. Add any new sources
4. Re-index

## Autonomy Directives

**Level:** Medium
- Make technical decisions independently
- Ask for design/UX choices
- Escalate on major architecture changes

**Subagents:**
- OCR/text extraction: dedicated agent
- UI/CSS: dedicated agent
- Source discovery: dedicated agent

**Crons:**
- None for this project (temporary testing only if needed, then remove)

## Success Criteria

- [ ] PDFs render in browser on GitHub Pages
- [ ] All text files have content (not empty)
- [ ] Files labeled by type (text/image/hybrid)
- [ ] Mobile-friendly UI
- [ ] Searchable by file number, type, content
- [ ] Quality indicators visible
- [ ] All available sources ingested
