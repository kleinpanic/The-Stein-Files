#!/usr/bin/env python3
"""
Force re-OCR on specific documents by removing ocr_applied flag.

For documents that failed OCR or have poor quality OCR, this script
temporarily removes the ocr_applied flag so extract.py will retry OCR.
"""
from __future__ import annotations

import json
from pathlib import Path


def main():
    """Remove ocr_applied flag from image PDFs without OCR."""
    catalog_path = Path('data/meta/catalog.json')
    catalog = json.load(catalog_path.open())
    
    # Find image PDFs without successful OCR
    to_reocr = [
        entry for entry in catalog
        if 'image' in entry.get('pdf_type', '').lower()
        and not entry.get('ocr_applied', False)
    ]
    
    print(f'Found {len(to_reocr)} documents to re-OCR')
    
    # Remove ocr_applied field to force re-processing
    for entry in to_reocr:
        if 'ocr_applied' in entry:
            del entry['ocr_applied']
        if 'ocr_text' in entry:
            # Keep existing text for comparison
            entry['ocr_text_old'] = entry.get('ocr_text', '')
    
    # Save updated catalog
    with catalog_path.open('w') as f:
        json.dump(catalog, f, indent=2)
    
    print(f'Removed ocr_applied flag from {len(to_reocr)} documents')
    print(f'Run: .venv/bin/python -m scripts.extract')
    print(f'to re-extract with enhanced OCR')


if __name__ == '__main__':
    main()
