# CI/CD Pipeline Upgrades for Eppie Improvements

## Current State (v1.4.0)
- ✅ Git LFS enabled (`lfs: true` in checkout)
- ✅ Python 3.11 setup
- ✅ Node 20 setup
- ✅ `make setup` installs requirements.txt
- ✅ Tests run on all 947 PDFs
- ✅ Build pipeline working

## Phase 2 Requirements: OCR & File Type Detection

### System Dependencies Needed
```yaml
- name: Install system dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y \
      tesseract-ocr \
      tesseract-ocr-eng \
      libtesseract-dev \
      poppler-utils \
      libmagic1
```

**Why:**
- `tesseract-ocr` + `tesseract-ocr-eng`: OCR engine for image-only PDFs
- `libtesseract-dev`: Development headers for pytesseract
- `poppler-utils`: For `pdfinfo` (page count, metadata extraction)
- `libmagic1`: For file type detection (`python-magic`)

### Python Dependencies to Add to requirements.txt
```python
pytesseract==0.3.10
pdf2image==1.16.3
python-magic==0.4.27
pillow==10.2.0
```

**Why:**
- `pytesseract`: Python wrapper for Tesseract OCR
- `pdf2image`: Convert PDF pages to images for OCR
- `python-magic`: File type detection
- `pillow`: Image processing (required by pdf2image)

### Updated Workflow Step
```yaml
- name: Install system dependencies
  run: |
    sudo apt-get update -qq
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev poppler-utils libmagic1
  
- name: Install Python dependencies
  run: make setup
  
- name: Run extraction (with OCR)
  run: make extract
  env:
    EPPIE_OCR_ENABLED: "1"
```

## Phase 3 Requirements: Enhanced Metadata

### Additional System Dependencies (Optional)
```yaml
- exiftool  # For deep PDF metadata extraction (optional)
```

### Additional Python Dependencies
```python
spacy==3.7.2
en-core-web-sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0.tar.gz
```

**Why:**
- `spacy` + `en-core-web-sm`: Named entity recognition for content-based tagging

### Installation in CI
```yaml
- name: Install NLP models
  run: python -m spacy download en_core_web_sm
```

## Estimated Build Time Impact

| Phase | Current | With OCR | With NLP |
|-------|---------|----------|----------|
| Setup | 30s | 2m | 3m |
| Extraction | 2m | 8-12m | 10-15m |
| Tests | 9m | 10m | 10m |
| Build | 1m | 1m | 1m |
| **Total** | **~13m** | **~22m** | **~30m** |

**Notes:**
- OCR adds ~4x time to extraction (10 sec/PDF → 40 sec/PDF for image-only)
- Can optimize with caching: only re-OCR if text extraction returns < 100 chars
- Can parallelize OCR (multiprocessing)

## Timeout Adjustments
```yaml
jobs:
  deploy:
    timeout-minutes: 45  # Current: default (360min)
```

## Caching Strategy (Optional - Reduce Build Times)
```yaml
- name: Cache Python dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

- name: Cache Tesseract language data
  uses: actions/cache@v3
  with:
    path: /usr/share/tesseract-ocr
    key: ${{ runner.os }}-tesseract-eng
```

## Environment Variables for Control
```yaml
env:
  EPPIE_OCR_ENABLED: "1"           # Enable OCR for image-only PDFs
  EPPIE_OCR_QUALITY_THRESHOLD: "100"  # Min chars before triggering OCR
  EPPIE_NLP_ENABLED: "1"            # Enable NER tagging
  EPPIE_PARALLEL_WORKERS: "2"       # Parallel extraction workers
```

## Validation Additions
```yaml
- name: Validate OCR output
  run: |
    python -c "
    import json
    catalog = json.load(open('data/meta/catalog.json'))
    ocr_count = sum(1 for doc in catalog if doc.get('ocr_applied'))
    print(f'OCR applied to {ocr_count} documents')
    "
```

## GitHub Pages Compatibility
- ✅ PDF.js already added (no further changes needed)
- ✅ Static site generation unchanged
- ✅ LFS serves files transparently
- No additional Pages configuration required

## Implementation Order
1. ✅ **Phase 1 (Done)**: PDF.js viewer, text extraction fixes
2. **Phase 2a**: Add Tesseract + system deps to CI workflow
3. **Phase 2b**: Update requirements.txt with OCR deps
4. **Phase 2c**: Implement OCR fallback in `scripts/extract.py`
5. **Phase 2d**: Test locally with `EPPIE_OCR_ENABLED=1 make extract`
6. **Phase 2e**: Push and verify CI passes
7. **Phase 3**: Add NLP deps + content tagging

## Rollback Plan
If CI fails or times out:
1. Set `EPPIE_OCR_ENABLED=0` in workflow
2. OCR logic skipped, falls back to current behavior
3. Fix issues, re-enable in next commit

## Monitoring
- Track `make extract` duration in CI logs
- Monitor LFS bandwidth usage (GitHub limits: 1GB free, then $5/50GB)
- Watch for timeout failures (adjust `timeout-minutes`)

## Cost Considerations
- **GitHub Actions**: Free for public repos (2,000 min/month), OCR adds ~10min/build
- **LFS Storage**: 1GB free, then $5/month per 50GB pack
- **LFS Bandwidth**: 1GB/month free, then $5 per 50GB pack
- **Current usage**: ~1.5GB storage, minimal bandwidth (Pages caches PDFs)
