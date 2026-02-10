# AI-Powered Document Extraction Workflow

**Goal**: Use AI models to extract high-quality metadata from documents before ingestion/indexing.

## Problem Statement

Current extraction methods have limitations:
- **OCR quality**: Heavily garbled text (35% email fields blank, 51% docs uncategorized)
- **Pattern matching**: Brittle, requires exact keyword matches
- **Manual effort**: 485 documents can't be auto-categorized
- **Missing data**: Person names, dates, relationships not fully extracted

## Proposed Solution

**AI-powered extraction pipeline** using vision + language models:
1. Process PDFs with vision model (read directly, no OCR)
2. Extract structured metadata using LLM
3. Validate and store in catalog
4. Run before push to ensure quality

## Architecture

```
New Document → AI Extraction → Structured Metadata → Catalog → Git Push → Deploy
                    ↓
              Vision Model (read PDF)
              Language Model (extract fields)
              Validation (check quality)
```

## Implementation Phases

### Phase 1: Single Document AI Extraction (MVP)

**Script**: `scripts/ai_extract.py`

**Functionality**:
- Takes PDF path as input
- Sends first 3 pages to vision model (Gemini Pro Vision / GPT-4 Vision)
- Prompts for structured metadata:
  - Document type/category
  - From/To/Subject (if email/correspondence)
  - People mentioned (full names)
  - Locations mentioned
  - Dates mentioned
  - Key topics/tags
  - Summary (100 words)
- Returns JSON with extracted fields
- Confidence scores for each field

**Models to Consider**:
- Google Gemini 3 Pro Vision (available, free tier)
- GPT-4 Vision (paid, higher quality)
- Claude 3 Opus Vision (when available)

**Cost Estimate**:
- Gemini: ~$0.002 per document (3 pages)
- GPT-4V: ~$0.05 per document (3 pages)
- 947 documents = $1.89 (Gemini) or $47.35 (GPT-4V)

### Phase 2: Batch Processing

**Script**: `scripts/batch_ai_extract.py`

**Functionality**:
- Process multiple documents in parallel
- Rate limiting and retry logic
- Progress tracking and checkpointing
- Fallback to traditional extraction if AI fails
- Quality validation (flag low-confidence extractions)

**Makefile Target**:
```makefile
transcribe:
	@echo "Running AI extraction on uncategorized documents..."
	.venv/bin/python scripts/batch_ai_extract.py --uncategorized --limit 50
```

### Phase 3: Pre-Push Workflow

**Git Hook**: `.git/hooks/pre-push`

**Functionality**:
- Detect new/modified PDFs in data/raw/
- Run AI extraction automatically
- Block push if extraction fails
- Generate report of changes

**Manual Override**:
```bash
make transcribe  # Run AI extraction manually
git push origin main  # Hook runs automatically
```

### Phase 4: Continuous Validation

**Script**: `scripts/validate_extraction_quality.py`

**Functionality**:
- Compare AI extraction vs existing data
- Flag inconsistencies
- Generate quality report
- Suggest re-extraction candidates

## Prompt Engineering

### Document Classification Prompt

```
You are analyzing a legal document from the Epstein case files.

Read this PDF and extract the following information in JSON format:

{
  "document_type": "email | correspondence | legal-filing | deposition | flight-log | evidence-list | memorandum | report | maintenance | other",
  "confidence": 0.0-1.0,
  "from": "sender name/email or null",
  "to": "recipient name/email or null",
  "subject": "subject line or null",
  "date": "YYYY-MM-DD or null",
  "people_mentioned": ["Full Name 1", "Full Name 2", ...],
  "locations_mentioned": ["Location 1", "Location 2", ...],
  "organizations": ["Org 1", "Org 2", ...],
  "key_topics": ["topic1", "topic2", ...],
  "summary": "2-3 sentence summary",
  "is_redacted": true/false,
  "quality_issues": "description of OCR/scan issues or null"
}

Rules:
- Only extract information that is clearly visible
- If a field is not visible/readable, set to null (do NOT guess)
- For people_mentioned: use full names only (first + last)
- For dates: use ISO format (YYYY-MM-DD)
- For document_type: pick the most specific category
- Set is_redacted: true if you see black boxes or [REDACTED] markers
```

### Person Extraction Prompt

```
Extract all person names from this document.

Return JSON:
{
  "people": [
    {
      "name": "Full Name",
      "context": "brief context where mentioned",
      "confidence": 0.0-1.0
    }
  ]
}

Rules:
- Extract ONLY full names (first + last), not titles alone
- Include middle names/initials if present
- Flag OCR errors with lower confidence
- Skip: "Mr. Smith" (no first name), "John" (no last name)
```

## Integration Points

### 1. Ingest Pipeline

**Modify**: `scripts/ingest.py`

**Add**: After downloading PDF, before adding to catalog:
```python
from scripts.ai_extract import extract_metadata_ai

pdf_path = Path(f"data/raw/{filename}")
if pdf_path.exists():
    ai_metadata = extract_metadata_ai(pdf_path)
    if ai_metadata['confidence'] > 0.7:
        # Use AI-extracted metadata
        entry.update(ai_metadata)
    else:
        # Fall back to traditional extraction
        entry.update(extract_metadata_traditional(pdf_path))
```

### 2. Catalog Generation

**Modify**: `scripts/extract.py`

**Add**: Option to use AI for uncategorized documents:
```bash
# Traditional extraction (default)
make extract

# AI-enhanced extraction
make extract EPPIE_AI_EXTRACT=1
```

### 3. Quality Review

**New Script**: `scripts/review_ai_extractions.py`

**Functionality**:
- Show side-by-side comparison: AI vs traditional
- Let user approve/reject AI extractions
- Build training data for fine-tuning

## Cost Management

### Strategies
1. **Selective AI**: Only use AI for low-quality/uncategorized docs
2. **Caching**: Store AI results, don't re-extract
3. **Batch processing**: Group documents to optimize API calls
4. **Free tier first**: Start with Gemini (free), upgrade if needed
5. **Incremental**: Process 50 docs/week, not all at once

### Budget
- **Phase 1 (MVP)**: $2 (50 test documents with Gemini)
- **Phase 2 (Full)**: $50 (all 485 uncategorized with GPT-4V)
- **Monthly**: $10 (new documents only)

## Success Metrics

### Before AI Extraction
- Categorized: 462/947 (48.8%)
- Email fields empty: 35%
- People extracted: 23/44 (52%)

### After AI Extraction (Target)
- Categorized: >850/947 (>90%)
- Email fields empty: <5%
- People extracted: >40/44 (>90%)

## Timeline

| Phase | Duration | Effort | Cost |
|-------|----------|--------|------|
| Phase 1: MVP | 2-4 hours | Implement ai_extract.py, test on 10 docs | $0.20 |
| Phase 2: Batch | 2-3 hours | batch_ai_extract.py, rate limiting | $1.00 |
| Phase 3: Pre-push | 1-2 hours | Git hook, make target | $0 |
| Phase 4: Validation | 2-3 hours | Quality reports, review UI | $0 |
| **Total** | **7-12 hours** | | **$1.20** |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| API costs too high | Use Gemini free tier, batch selectively |
| AI hallucinations | Confidence thresholds, human review |
| API rate limits | Exponential backoff, queue system |
| Quality worse than OCR | A/B test, use best of both |
| Dependency on external API | Cache results, fallback to traditional |

## Next Steps (Immediate)

1. **Create ai_extract.py** (2h)
   - Implement Gemini Pro Vision integration
   - Test on 5 sample documents
   - Validate output quality

2. **Test on uncategorized subset** (1h)
   - Run on 50 worst-quality documents
   - Compare results to traditional extraction
   - Calculate accuracy improvement

3. **Decision point**: 
   - If quality >80% better → proceed to batch processing
   - If quality similar → investigate alternatives
   - If quality worse → abandon approach

4. **Implement batch processing** (2h)
   - Create batch_ai_extract.py
   - Add make target
   - Process remaining uncategorized docs

## Alternative Approaches

If AI extraction doesn't work well:

1. **Better OCR preprocessing**: Image enhancement, noise reduction
2. **Crowd-sourced validation**: Manual review interface
3. **Rule-based improvements**: More sophisticated patterns
4. **Hybrid approach**: AI for specific fields, traditional for others
5. **Document type specialization**: Different extractors per category

## References

- Gemini Pro Vision API: https://ai.google.dev/gemini-api/docs/vision
- GPT-4 Vision: https://platform.openai.com/docs/guides/vision
- Keep a Changelog: https://keepachangelog.com/
- Semantic Versioning: https://semver.org/
