#!/usr/bin/env python3
"""
Re-extract text from poor-extraction PDFs using advanced OCR.

Targets docs with <50 chars extracted text, applies advanced OCR with:
- 400+ DPI rendering
- Adaptive preprocessing
- Multiple Tesseract PSM modes
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Dict

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.common import load_catalog, DERIVED_TEXT_DIR
from scripts.advanced_ocr import extract_text_advanced


def find_poor_extractions(min_chars: int = 50) -> List[Dict]:
    """Find docs with poor text extraction."""
    catalog = load_catalog()
    poor_docs = []
    
    for doc in catalog:
        text_file = DERIVED_TEXT_DIR / f"{doc['id']}.txt"
        if text_file.exists():
            content = text_file.read_text(encoding='utf-8', errors='ignore')
            if len(content.strip()) <= min_chars and doc.get('pdf_type') == 'image':
                poor_docs.append(doc)
    
    return poor_docs


def reocr_documents(docs: List[Dict], dpi: int = 400, max_pages: int = None) -> Dict:
    """
    Re-extract text from documents using advanced OCR.
    
    Returns:
        Stats dict with improvements
    """
    stats = {
        'total': len(docs),
        'improved': 0,
        'failed': 0,
        'chars_before': 0,
        'chars_after': 0,
    }
    
    for i, doc in enumerate(docs, 1):
        doc_id = doc['id']
        pdf_path = Path(doc['file_path'])
        text_file = DERIVED_TEXT_DIR / f"{doc_id}.txt"
        
        # Get old text
        old_text = text_file.read_text(encoding='utf-8', errors='ignore').strip()
        old_len = len(old_text)
        stats['chars_before'] += old_len
        
        print(f"[{i}/{len(docs)}] Processing {doc['title'][:50]:50s}", end=' ')
        
        try:
            # Run advanced OCR
            new_text, metadata = extract_text_advanced(pdf_path, dpi=dpi, max_pages=max_pages)
            new_len = len(new_text.strip())
            stats['chars_after'] += new_len
            
            # Check improvement
            improvement = new_len - old_len
            
            if improvement > 50:  # Meaningful improvement
                # Save new text
                text_file.write_text(new_text, encoding='utf-8')
                stats['improved'] += 1
                print(f"✅ {old_len:4d} → {new_len:5d} (+{improvement:4d})")
            elif improvement > 0:
                # Minor improvement, still save
                text_file.write_text(new_text, encoding='utf-8')
                print(f"⚠️  {old_len:4d} → {new_len:5d} (+{improvement:4d})")
            else:
                stats['failed'] += 1
                print(f"❌ {old_len:4d} → {new_len:5d} (no improvement)")
        
        except Exception as e:
            stats['failed'] += 1
            print(f"❌ ERROR: {e}")
    
    return stats


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Re-OCR poor extractions')
    parser.add_argument('--limit', type=int, help='Only process first N docs (for testing)')
    parser.add_argument('--dpi', type=int, default=400, help='DPI for rendering (default: 400)')
    parser.add_argument('--max-pages', type=int, help='Max pages per PDF (default: all)')
    args = parser.parse_args()
    
    print("Finding poor-extraction documents...")
    poor_docs = find_poor_extractions(min_chars=50)
    print(f"Found {len(poor_docs)} documents with poor extraction\n")
    
    if args.limit:
        poor_docs = poor_docs[:args.limit]
        print(f"Processing first {len(poor_docs)} documents (--limit)\n")
    
    print(f"Re-OCRing with DPI={args.dpi}, max_pages={args.max_pages or 'all'}\n")
    
    stats = reocr_documents(poor_docs, dpi=args.dpi, max_pages=args.max_pages)
    
    print(f"\n{'='*80}")
    print(f"RESULTS:")
    print(f"  Total processed: {stats['total']}")
    print(f"  Improved: {stats['improved']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total chars before: {stats['chars_before']}")
    print(f"  Total chars after: {stats['chars_after']}")
    print(f"  Average improvement: {(stats['chars_after'] - stats['chars_before']) / stats['total']:.0f} chars/doc")
