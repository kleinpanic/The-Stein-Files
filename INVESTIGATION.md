# Eppie Deep Investigation: 97%+ Categorization & OCR

Started: 2026-02-10T15:16:38-05:00
Branch: autonomous/eppie-97-coverage

## Goals
- Categorization coverage: >= 97%
- OCR coverage (meaningful extraction): >= 97%
- Keep GitHub Pages + mobile UI clean

## Baseline (start)
- Categorization: ~80.9% (per prior session)
- OCR: ~89.2% (per prior session)

## Notes
- Prior enhanced Tesseract-based OCR attempts did not move the needle on ~37 docs.
- Prior categorization blocker: ~181 "Utilities — EFTA..." docs lacking markers.


## Findings (Utilities long tail)
The remaining "uncategorized" set was not homogeneous; it was mostly Utilities PDFs that fall into a few buckets:
- **Phone/billing call-detail style pages**: lots of "incoming/outgoing", "airtime", "long distance", minutes/charges.
- **Media/filename index pages**: dense lists of file names like DSCF*.TIF / IMG_*.JPG (often photo sets / exhibits).
- **Subscriber/online account records**: e.g., "GOOGLE SUBSCRIBER INFORMATION" with Terms-of-Service IP lines.
- **Generic covers / low-signal scans**: little semantic structure beyond Bates stamp + scattered text.

Resolution strategy:
- Prefer specific categories when detectable (`phone-record`, `internet-record`, `media-index`).
- Otherwise, avoid leaving Utilities uncategorized: default to `scanned-document`.
