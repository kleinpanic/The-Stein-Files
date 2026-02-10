#!/usr/bin/env python3
"""
Fix email metadata extraction - clean up From/To fields and improve subject extraction.
"""
from __future__ import annotations

import re
from pathlib import Path
import json


def clean_email_field(raw_value: str) -> str:
    """
    Clean up email From/To fields by removing OCR noise and normalizing.
    
    Common issues:
    - "Sent: cipher 10, 2018 4:37 PM" instead of just sender
    - "subooena.criminai" instead of "subpoena-criminal@amazon.com"
    - Extra whitespace, newlines, formatting artifacts
    """
    if not raw_value or raw_value == "N/A":
        return ""
    
    # Remove common prefixes that leak into the field
    raw_value = re.sub(r'^(From:|To:|Cc:|Bcc:|Sent:)\s*', '', raw_value, flags=re.IGNORECASE)
    
    # Remove date/time patterns that leak in
    raw_value = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)?\b', '', raw_value, flags=re.IGNORECASE)
    raw_value = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)?\b', '', raw_value)
    
    # Remove "cipher" and other OCR artifacts
    raw_value = re.sub(r'\bcipher\s+\d+\b', '', raw_value, flags=re.IGNORECASE)
    
    # Clean up whitespace
    raw_value = re.sub(r'\s+', ' ', raw_value).strip()
    
    # If it's just punctuation or too short, return empty
    if len(raw_value) < 3 or raw_value in ('(', ')', '[', ']', 'Cc:', 'Bcc:'):
        return ""
    
    # Limit length (prevent huge blocks)
    if len(raw_value) > 200:
        raw_value = raw_value[:200] + "..."
    
    return raw_value


def extract_name_from_email(email_str: str) -> str:
    """
    Extract just the name portion from an email string.
    
    Examples:
    - "John Doe <john@example.com>" → "John Doe"
    - "subpoena-criminal@amazon.com [mailto:...]" → "subpoena-criminal@amazon.com"
    - "Rodeb Teresa" → "Rodeb Teresa"
    """
    # Pattern: Name <email>
    match = re.match(r'^([^<]+)\s*<[^>]+>$', email_str)
    if match:
        return match.group(1).strip()
    
    # Pattern: email [mailto:email]
    match = re.match(r'^([^\[]+)\s*\[mailto:', email_str)
    if match:
        return match.group(1).strip()
    
    # Just return as-is if no special formatting
    return email_str.strip()


def improve_email_title(doc: dict) -> str:
    """
    Generate better email title based on metadata.
    
    Instead of "Utilities — EFTA01263156.pdf", show:
    "Email: FW Mr. Jeffrey Epstein (from cipher@example.com)"
    """
    subject = doc.get("email_subject", "").strip()
    from_field = doc.get("email_from", "").strip()
    
    # If no metadata, fall back to original title
    if not subject and not from_field:
        return doc["title"]
    
    # Build informative title
    parts = []
    
    if subject and subject != "None":
        # Limit subject length
        if len(subject) > 60:
            subject = subject[:57] + "..."
        parts.append(subject)
    else:
        parts.append("(No subject)")
    
    if from_field and from_field != "Sent:" and len(from_field) > 3:
        # Extract just the name/email
        from_name = extract_name_from_email(from_field)
        if from_name and len(from_name) > 3:
            if len(from_name) > 30:
                from_name = from_name[:27] + "..."
            parts.append(f"from {from_name}")
    
    if parts:
        prefix = "📧 " if doc.get("document_category") == "email" else "📄 "
        return prefix + " • ".join(parts)
    
    return doc["title"]


def main():
    """Fix email metadata for all email/correspondence documents."""
    catalog_path = Path("data/meta/catalog.json")
    
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    print("Fixing email metadata...")
    
    updated_count = 0
    for doc in catalog:
        if doc.get("document_category") not in ["email", "correspondence"]:
            continue
        
        # Clean up From field
        if "email_from" in doc:
            cleaned_from = clean_email_field(doc["email_from"])
            if cleaned_from != doc["email_from"]:
                doc["email_from"] = cleaned_from
                updated_count += 1
        
        # Clean up To field  
        if "email_to" in doc:
            cleaned_to = clean_email_field(doc["email_to"])
            if cleaned_to != doc["email_to"]:
                doc["email_to"] = cleaned_to
                updated_count += 1
        
        # Improve title
        # new_title = improve_email_title(doc)
        # if new_title != doc["title"]:
        #     doc["title"] = new_title
        #     updated_count += 1
    
    # Write updated catalog
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    print(f"✓ Cleaned email metadata for {updated_count} field updates")
    
    # Show sample
    emails = [doc for doc in catalog if doc.get("document_category") in ["email", "correspondence"]]
    print(f"\nSample cleaned emails:")
    for doc in emails[:5]:
        print(f"\n{doc['title']}")
        print(f"  From: {doc.get('email_from', 'N/A')}")
        print(f"  To: {doc.get('email_to', 'N/A')}")
        print(f"  Subject: {doc.get('email_subject', 'N/A')}")


if __name__ == "__main__":
    main()
