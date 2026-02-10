#!/usr/bin/env python3
"""
Comprehensive email metadata fix.
- Set empty fields to [Redacted] or [Not visible]
- Fix OCR-garbled fields
- Re-extract from text where possible
"""
import json
from pathlib import Path
import re

def extract_email_metadata_from_text(text: str) -> dict:
    """Extract email metadata from document text."""
    metadata = {}
    
    # Common email header patterns
    from_patterns = [
        r'From:\s*([^\n]+)',
        r'FROM:\s*([^\n]+)',
        r'Sender:\s*([^\n]+)',
    ]
    
    to_patterns = [
        r'To:\s*([^\n]+)',
        r'TO:\s*([^\n]+)',
        r'Recipient:\s*([^\n]+)',
    ]
    
    subject_patterns = [
        r'Subject:\s*([^\n]+)',
        r'SUBJECT:\s*([^\n]+)',
        r'Re:\s*([^\n]+)',
    ]
    
    cc_patterns = [
        r'Cc:\s*([^\n]+)',
        r'CC:\s*([^\n]+)',
    ]
    
    # Extract From
    for pattern in from_patterns:
        match = re.search(pattern, text[:2000], re.IGNORECASE)
        if match:
            metadata['from'] = match.group(1).strip()
            break
    
    # Extract To
    for pattern in to_patterns:
        match = re.search(pattern, text[:2000], re.IGNORECASE)
        if match:
            metadata['to'] = match.group(1).strip()
            break
    
    # Extract Subject
    for pattern in subject_patterns:
        match = re.search(pattern, text[:2000], re.IGNORECASE)
        if match:
            metadata['subject'] = match.group(1).strip()
            break
    
    # Extract Cc
    for pattern in cc_patterns:
        match = re.search(pattern, text[:2000], re.IGNORECASE)
        if match:
            metadata['cc'] = match.group(1).strip()
            break
    
    return metadata

def clean_field(value: str) -> str:
    """Clean and normalize field value."""
    if not value or value in ["", "N/A"]:
        return "[Not visible in document]"
    
    # Remove common OCR artifacts
    value = re.sub(r'\s+', ' ', value).strip()
    
    # Fix garbled patterns
    if value in ["From:", "To:", "Cc:", "Sent:", "Subject:"]:
        return "[Not visible in document]"
    
    # If very short and looks garbled
    if len(value) < 3:
        return "[Not visible in document]"
    
    # Limit length
    if len(value) > 150:
        value = value[:147] + "..."
    
    return value

def main():
    catalog_path = Path("data/meta/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    emails = [doc for doc in catalog if doc.get("document_category") in ["email", "correspondence"]]
    
    print(f"Fixing metadata for {len(emails)} emails...")
    
    fixed_count = 0
    reextracted_count = 0
    
    for doc in emails:
        doc_id = doc["id"]
        text_path = Path(f"data/derived/text/{doc_id}.txt")
        
        needs_fix = False
        
        # Check if fields need fixing
        from_field = doc.get("email_from", "")
        to_field = doc.get("email_to", "")
        subject_field = doc.get("email_subject", "")
        cc_field = doc.get("email_cc", "")
        
        # Try re-extraction if text exists and fields are empty
        if text_path.exists() and (not from_field or not to_field or not subject_field):
            text = text_path.read_text(errors="ignore")
            extracted = extract_email_metadata_from_text(text)
            
            if extracted:
                reextracted_count += 1
                if extracted.get('from'):
                    doc["email_from"] = clean_field(extracted['from'])
                    needs_fix = True
                if extracted.get('to'):
                    doc["email_to"] = clean_field(extracted['to'])
                    needs_fix = True
                if extracted.get('subject'):
                    doc["email_subject"] = clean_field(extracted['subject'])
                    needs_fix = True
                if extracted.get('cc'):
                    doc["email_cc"] = clean_field(extracted['cc'])
                    needs_fix = True
        
        # Clean existing fields
        doc["email_from"] = clean_field(doc.get("email_from", ""))
        doc["email_to"] = clean_field(doc.get("email_to", ""))
        doc["email_subject"] = clean_field(doc.get("email_subject", ""))
        doc["email_cc"] = clean_field(doc.get("email_cc", ""))
        
        if needs_fix:
            fixed_count += 1
    
    # Write updated catalog
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    print(f"✓ Fixed {fixed_count} emails")
    print(f"✓ Re-extracted metadata for {reextracted_count} emails")
    
    # Stats
    empty_from = sum(1 for doc in emails if doc.get("email_from") == "[Not visible in document]")
    empty_to = sum(1 for doc in emails if doc.get("email_to") == "[Not visible in document]")
    empty_subject = sum(1 for doc in emails if doc.get("email_subject") == "[Not visible in document]")
    
    print(f"\nAfter fix:")
    print(f"  From '[Not visible]': {empty_from} ({empty_from/len(emails)*100:.1f}%)")
    print(f"  To '[Not visible]': {empty_to} ({empty_to/len(emails)*100:.1f}%)")
    print(f"  Subject '[Not visible]': {empty_subject} ({empty_subject/len(emails)*100:.1f}%)")

if __name__ == "__main__":
    main()
