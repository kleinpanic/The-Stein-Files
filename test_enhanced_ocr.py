#!/usr/bin/env python3
"""Test enhanced OCR on better sample (documents with some text)."""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))

from scripts.pdf_analyzer import analyze_pdf

# Load better sample
with open("phase1_better_sample.json") as f:
    sample_ids = json.load(f)

# Load catalog
with open("data/meta/catalog.json") as f:
    catalog = json.load(f)

# Enable enhanced OCR
os.environ["EPPIE_ENHANCED_OCR"] = "1"

results = []
print("Running enhanced OCR on 5 medium-quality PDFs...\n")

for doc_id in sample_ids:
    entry = next((e for e in catalog if e["id"] == doc_id), None)
    if not entry:
        continue
    
    pdf_path = Path(entry["file_path"])
    text_path = Path(f"data/derived/text/{doc_id}.txt")
    
    if text_path.exists():
        extracted_text = text_path.read_text(encoding="utf-8", errors="ignore")
    else:
        extracted_text = ""
    
    old_quality = entry.get("text_quality_score", 0)
    
    print(f"Processing {entry['title']}...")
    print(f"  Old quality: {old_quality:.1f}")
    
    result = analyze_pdf(pdf_path, extracted_text, enable_ocr=True)
    
    new_quality = result["text_quality_score"]
    improvement = new_quality - old_quality
    
    results.append({
        "id": doc_id,
        "title": entry["title"],
        "old_quality": old_quality,
        "new_quality": new_quality,
        "improvement": improvement,
        "ocr_confidence": result.get("ocr_confidence"),
        "person_names": result.get("person_names", []),
        "locations": result.get("locations", []),
        "category": result["document_category"]
    })
    
    print(f"  New quality: {new_quality:.1f} ({improvement:+.1f})")
    print(f"  OCR Confidence: {result.get('ocr_confidence', 'N/A')}")
    print(f"  Category: {result['document_category']}")
    print(f"  Person names: {result.get('person_names', [])}")
    print(f"  Locations: {result.get('locations', [])}")
    print()

# Summary
avg_old = sum(r["old_quality"] for r in results) / len(results)
avg_new = sum(r["new_quality"] for r in results) / len(results)
avg_improvement = avg_new - avg_old
total_with_names = sum(1 for r in results if r["person_names"])
total_with_locations = sum(1 for r in results if r["locations"])

print("\n" + "="*60)
print("ENHANCED OCR TEST RESULTS (Better Sample)")
print("="*60)
print(f"Sample size: {len(results)} PDFs")
print(f"Average quality: {avg_old:.1f} → {avg_new:.1f} ({avg_improvement:+.1f})")
print(f"PDFs with person names extracted: {total_with_names}/{len(results)}")
print(f"PDFs with locations extracted: {total_with_locations}/{len(results)}")

# Save results
with open("phase1_better_results.json", "w") as f:
    json.dump({"summary": {
        "avg_old_quality": avg_old,
        "avg_new_quality": avg_new,
        "avg_improvement": avg_improvement,
        "total_with_names": total_with_names,
        "total_with_locations": total_with_locations
    }, "results": results}, f, indent=2)

print("\nResults saved to phase1_better_results.json")
print("\nTest complete!")
