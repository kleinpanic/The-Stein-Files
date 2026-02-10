#!/usr/bin/env python3
"""
Batch OCR + categorization for uncategorized documents.
Strategy: Process in batches with progress reporting.
"""
import json
from pathlib import Path
import subprocess
import sys

def main():
    catalog_path = Path("data/meta/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    # Get uncategorized image/low-quality docs
    uncategorized = [
        doc for doc in catalog 
        if (not doc.get("document_category") or doc["document_category"] == "None")
        and doc.get("quality", 0) < 20
    ]
    
    print(f"Found {len(uncategorized)} uncategorized low-quality documents")
    
    # Process first batch
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    batch = uncategorized[:batch_size]
    
    print(f"\nProcessing batch of {len(batch)} documents with OCR...")
    print(f"Estimated time: {len(batch) * 3} seconds (~{len(batch) * 3 / 60:.1f} minutes)")
    print(f"Full dataset would take: ~{len(uncategorized) * 3 / 60:.1f} minutes")
    
    # Create temporary file list
    doc_ids = [doc["id"] for doc in batch]
    
    with open("/tmp/ocr_batch_ids.txt", "w") as f:
        f.write("\n".join(doc_ids))
    
    # Run OCR (using reextract_with_ocr.py)
    print("\nStarting OCR extraction...")
    result = subprocess.run(
        [".venv/bin/python", "scripts/reextract_with_ocr.py", "--ids-file", "/tmp/ocr_batch_ids.txt"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"OCR failed: {result.stderr}")
        return 1
    
    print(result.stdout)
    
    # Re-run categorization
    print("\nRe-running categorization on OCR'd documents...")
    result = subprocess.run(
        [".venv/bin/python", "scripts/auto_categorize_documents.py"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    print(f"\n✓ Batch complete: {len(batch)} documents processed")
    print(f"✓ Remaining uncategorized: {len(uncategorized) - len(batch)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
