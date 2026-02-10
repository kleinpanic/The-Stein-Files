#!/usr/bin/env python3
"""
Batch OCR processor - reads document IDs from file and applies OCR.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.common import load_catalog, write_json, DATA_META_DIR, DERIVED_TEXT_DIR
from scripts.pdf_analyzer import apply_ocr_to_pdf, calculate_text_quality_score, classify_document_type, extract_file_numbers, extract_dates


def apply_ocr_and_update(entry: dict) -> dict:
    """Apply OCR to a PDF and update its metadata."""
    file_path = Path(entry['file_path'])
    
    if not file_path.exists():
        print(f"[SKIP] File not found: {file_path}")
        return entry
    
    print(f"[OCR] Processing {file_path.name}...")
    
    try:
        # Apply OCR (max 10 pages)
        ocr_text = apply_ocr_to_pdf(file_path, max_pages=10)
        
        if not ocr_text or len(ocr_text.strip()) < 50:
            print(f"[SKIP] OCR yielded minimal text: {len(ocr_text)} chars")
            return entry
        
        # Calculate new quality score
        new_quality = calculate_text_quality_score(ocr_text)
        old_quality = entry.get('text_quality_score', 0)
        print(f"[OCR] Quality: {old_quality:.1f} → {new_quality:.1f}")
        
        # Re-classify document
        new_category = classify_document_type(entry['title'], ocr_text)
        
        # Extract metadata
        file_numbers = extract_file_numbers(ocr_text)
        dates = extract_dates(ocr_text)
        
        # Update entry
        entry['text_quality_score'] = new_quality
        entry['ocr_applied'] = True
        if new_category:
            entry['document_category'] = new_category
        entry['extracted_file_numbers'] = file_numbers[:10]
        entry['extracted_dates'] = dates[:20]
        
        # Save enhanced text
        text_file = DERIVED_TEXT_DIR / f"{entry['id']}.txt"
        text_file.parent.mkdir(parents=True, exist_ok=True)
        text_file.write_text(ocr_text, encoding='utf-8')
        
        return entry
        
    except Exception as exc:
        print(f"[ERROR] OCR failed: {exc}")
        return entry


def main():
    if len(sys.argv) < 2:
        print("Usage: batch_ocr_from_ids.py <ids_file>")
        sys.exit(1)
    
    ids_file = Path(sys.argv[1])
    if not ids_file.exists():
        print(f"Error: {ids_file} not found")
        sys.exit(1)
    
    # Load IDs
    with open(ids_file) as f:
        doc_ids = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(doc_ids)} document IDs from {ids_file}")
    
    # Load catalog
    catalog = load_catalog()
    
    # Find matching entries
    entries_to_process = [
        entry for entry in catalog 
        if entry['id'] in doc_ids
    ]
    
    print(f"Found {len(entries_to_process)} matching documents in catalog")
    
    if not entries_to_process:
        print("No matching documents. Exiting.")
        return
    
    # Process each
    updated_count = 0
    for i, entry in enumerate(entries_to_process, 1):
        print(f"\n[{i}/{len(entries_to_process)}] {entry['title']}")
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
    
    print(f"\n✅ OCR complete: {updated_count}/{len(entries_to_process)} documents improved")
    print(f"Updated catalog saved")


if __name__ == "__main__":
    main()
