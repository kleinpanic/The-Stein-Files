#!/usr/bin/env python3
"""Re-classify documents in catalog with improved logic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.common import load_catalog, write_json, DATA_META_DIR, DERIVED_TEXT_DIR
from scripts.pdf_analyzer import classify_document_type

def main():
    catalog = load_catalog()
    updated = 0
    
    for entry in catalog:
        # Get text sample
        text_file = DERIVED_TEXT_DIR / f"{entry['id']}.txt"
        if not text_file.exists():
            continue
        
        text_sample = text_file.read_text(encoding='utf-8', errors='ignore')
        
        # Re-classify
        new_category = classify_document_type(entry['title'], text_sample)
        
        if new_category and new_category != entry.get('document_category'):
            old_cat = entry.get('document_category')
            entry['document_category'] = new_category
            print(f"[UPDATE] {entry['title']}: {old_cat} → {new_category}")
            updated += 1
    
    # Save
    write_json(DATA_META_DIR / "catalog.json", catalog)
    print(f"\n✅ Re-classified {updated} documents")

if __name__ == "__main__":
    main()
