#!/usr/bin/env python3
"""
Re-extract text from low-quality image PDFs using OCR.

This script:
1. Identifies PDFs with type='image' and quality_score < 30
2. Applies OCR to extract text
3. Updates catalog with improved metadata
4. Saves enhanced text to derived/text/
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

from scripts.common import load_catalog, write_json, DATA_META_DIR, DERIVED_TEXT_DIR
from scripts.pdf_analyzer import apply_ocr_to_pdf, calculate_text_quality_score, classify_document_type, extract_file_numbers, extract_dates


def find_low_quality_image_pdfs(catalog: List[Dict]) -> List[Dict]:
    """Find PDFs that need OCR."""
    candidates = []
    for entry in catalog:
        pdf_type = entry.get('pdf_type', '')
        quality = entry.get('text_quality_score', 0)
        ocr_applied = entry.get('ocr_applied', False)
        
        # Target: image PDFs with low quality, not yet OCR'd
        if pdf_type == 'image' and quality < 30 and not ocr_applied:
            candidates.append(entry)
    
    return candidates


def apply_ocr_and_update(entry: Dict) -> Dict:
    """Apply OCR to a PDF and update its metadata."""
    file_path = Path(entry['file_path'])
    
    if not file_path.exists():
        print(f"[SKIP] File not found: {file_path}")
        return entry
    
    print(f"[OCR] Processing {file_path.name}...")
    
    try:
        # Apply OCR (max 10 pages for thoroughness)
        ocr_text = apply_ocr_to_pdf(file_path, max_pages=10)
        
        if not ocr_text or len(ocr_text.strip()) < 50:
            print(f"[SKIP] OCR yielded minimal text: {len(ocr_text)} chars")
            return entry
        
        # Calculate new quality score
        new_quality = calculate_text_quality_score(ocr_text)
        print(f"[OCR] Quality improved: {entry['text_quality_score']:.1f} → {new_quality:.1f}")
        
        # Re-classify document
        new_category = classify_document_type(entry['title'], ocr_text)
        
        # Extract metadata from OCR text
        file_numbers = extract_file_numbers(ocr_text)
        dates = extract_dates(ocr_text)
        
        # Update entry
        entry['text_quality_score'] = new_quality
        entry['ocr_applied'] = True
        entry['document_category'] = new_category or entry.get('document_category')
        entry['extracted_file_numbers'] = file_numbers[:10]
        entry['extracted_dates'] = dates[:20]
        
        # Save enhanced text
        text_file = DERIVED_TEXT_DIR / f"{entry['id']}.txt"
        text_file.parent.mkdir(parents=True, exist_ok=True)
        text_file.write_text(ocr_text, encoding='utf-8')
        
        return entry
        
    except Exception as exc:
        print(f"[ERROR] OCR failed for {file_path.name}: {exc}")
        return entry


def main():
    """Re-extract with OCR."""
    catalog = load_catalog()
    
    print(f"Loaded {len(catalog)} documents")
    
    # Find candidates
    candidates = find_low_quality_image_pdfs(catalog)
    print(f"Found {len(candidates)} image PDFs needing OCR")
    
    if not candidates:
        print("No documents need OCR. Exiting.")
        return
    
    # Process each
    updated_count = 0
    for i, entry in enumerate(candidates, 1):
        print(f"\n[{i}/{len(candidates)}] {entry['title']}")
        updated_entry = apply_ocr_and_update(entry)
        
        if updated_entry.get('ocr_applied'):
            updated_count += 1
            # Update in catalog
            for j, cat_entry in enumerate(catalog):
                if cat_entry['id'] == updated_entry['id']:
                    catalog[j] = updated_entry
                    break
    
    # Save updated catalog
    catalog_path = DATA_META_DIR / "catalog.json"
    write_json(catalog_path, catalog)
    
    print(f"\n✅ OCR complete: {updated_count}/{len(candidates)} documents improved")
    print(f"Updated catalog saved to {catalog_path}")


if __name__ == "__main__":
    main()
