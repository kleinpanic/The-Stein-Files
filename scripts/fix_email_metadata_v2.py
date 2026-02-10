#!/usr/bin/env python3
"""
Fix email metadata extraction - aggressive cleanup of From/To fields.
"""
from __future__ import annotations

import re
from pathlib import Path
import json


def clean_email_field_aggressive(raw_value: str) -> str:
    """
    Aggressively clean email From/To fields.
    
    Common issues to fix:
    - ", 2018 4:37 PM" → ""
    - "Sent: cipher 10, 2018 4:37 PM" → ""
    - "subooena.criminai" → keep as-is (OCR error but valid)
    - "(USMS)'" → keep as-is
    - Empty/whitespace only → ""
    """
    if not raw_value or raw_value == "N/A":
        return ""
    
    # Remove leading/trailing whitespace
    raw_value = raw_value.strip()
    
    # Remove common prefixes
    raw_value = re.sub(r'^(From:|To:|Cc:|Bcc:|Sent:)\s*', '', raw_value, flags=re.IGNORECASE)
    
    # Remove date/time patterns that leak in
    # Pattern: ", 2018 4:37 PM" or "cipher 10, 2018 4:37 PM"
    raw_value = re.sub(r',?\s*\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)?', '', raw_value)
    raw_value = re.sub(r'\b(?:cipher)\s+\d+,?\s*', '', raw_value, flags=re.IGNORECASE)
    
    # Remove full date patterns
    raw_value = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b', '', raw_value, flags=re.IGNORECASE)
    raw_value = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '', raw_value)
    
    # Clean up whitespace
    raw_value = re.sub(r'\s+', ' ', raw_value).strip()
    
    # If it starts with just a comma or punctuation, remove it
    raw_value = re.sub(r'^[,\.\-\s]+', '', raw_value)
    
    # If too short or just punctuation, return empty
    if len(raw_value) < 2:
        return ""
    
    # If it's JUST punctuation, return empty
    if re.match(r'^[\(\)\[\],\.\;\:\-\s]+$', raw_value):
        return ""
    
    # Limit length
    if len(raw_value) > 150:
        raw_value = raw_value[:147] + "..."
    
    return raw_value


def main():
    """Fix email metadata with aggressive cleaning."""
    catalog_path = Path("data/meta/catalog.json")
    
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    print("Applying aggressive email metadata cleanup...")
    
    updated_count = 0
    emails_processed = 0
    
    for doc in catalog:
        if doc.get("document_category") not in ["email", "correspondence"]:
            continue
        
        emails_processed += 1
        
        # Clean From field
        if "email_from" in doc:
            old_from = doc["email_from"]
            cleaned_from = clean_email_field_aggressive(old_from)
            if cleaned_from != old_from:
                doc["email_from"] = cleaned_from
                updated_count += 1
        
        # Clean To field
        if "email_to" in doc:
            old_to = doc["email_to"]
            cleaned_to = clean_email_field_aggressive(old_to)
            if cleaned_to != old_to:
                doc["email_to"] = cleaned_to
                updated_count += 1
    
    # Write updated catalog
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    print(f"✓ Processed {emails_processed} emails, made {updated_count} field updates")
    
    # Show sample
    emails = [doc for doc in catalog if doc.get("document_category") in ["email", "correspondence"]]
    print(f"\nSample cleaned emails (first 10):")
    for doc in emails[:10]:
        from_field = doc.get('email_from', 'N/A')
        to_field = doc.get('email_to', 'N/A')
        subject_field = doc.get('email_subject', 'N/A')
        
        # Show what's actually stored
        print(f"\n{doc['id']}")
        print(f"  From: '{from_field}' ({len(from_field)} chars)")
        print(f"  To: '{to_field}' ({len(to_field)} chars)")
        print(f"  Subject: {subject_field}")


if __name__ == "__main__":
    main()
