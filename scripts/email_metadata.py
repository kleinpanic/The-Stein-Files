#!/usr/bin/env python3
"""
Email metadata extraction from text content.

Extracts From, To, Subject, and Date fields from email/correspondence documents.
"""
from __future__ import annotations

import re
from typing import Dict, Optional


def extract_email_metadata(text: str) -> Dict[str, Optional[str]]:
    """
    Extract email header fields from text content.
    
    Args:
        text: Extracted text content from PDF
        
    Returns:
        Dictionary with from_addr, to_addr, subject, and date fields
    """
    metadata = {
        "from_addr": None,
        "to_addr": None,
        "subject": None,
        "date": None,
    }
    
    if not text:
        return metadata
    
    # Take only first 2000 chars where headers usually appear
    header_section = text[:2000]
    
    # Pattern: "From:" followed by content until next header or double newline
    # Common variations: "From:", "FROM:", "From :", etc.
    from_match = re.search(
        r'(?:^|\n)From\s*:\s*([^\n]+?)(?=\n(?:To|Sent|Subject|Cc|Date|$))',
        header_section,
        re.IGNORECASE | re.MULTILINE
    )
    if from_match:
        metadata["from_addr"] = from_match.group(1).strip()
    
    # Pattern: "To:" followed by content
    to_match = re.search(
        r'(?:^|\n)To\s*:\s*([^\n]+?)(?=\n(?:From|Sent|Subject|Cc|Date|$))',
        header_section,
        re.IGNORECASE | re.MULTILINE
    )
    if to_match:
        metadata["to_addr"] = to_match.group(1).strip()
    
    # Pattern: "Subject:" followed by content
    subject_match = re.search(
        r'(?:^|\n)Subject\s*:\s*([^\n]+?)(?=\n(?:From|To|Sent|Cc|Date|$))',
        header_section,
        re.IGNORECASE | re.MULTILINE
    )
    if subject_match:
        metadata["subject"] = subject_match.group(1).strip()
    
    # Pattern: "Date:" or "Sent:" followed by date content
    date_match = re.search(
        r'(?:^|\n)(?:Date|Sent)\s*:\s*([^\n]+?)(?=\n(?:From|To|Subject|Cc|$))',
        header_section,
        re.IGNORECASE | re.MULTILINE
    )
    if date_match:
        metadata["date"] = date_match.group(1).strip()
    
    return metadata


def is_epstein_email(metadata: Dict[str, Optional[str]], text: str = "") -> bool:
    """
    Determine if email involves Jeffrey Epstein (sent by or received by).
    
    Args:
        metadata: Email metadata dict with from_addr and to_addr
        text: Optional full text for additional context
        
    Returns:
        True if email appears to involve Epstein
    """
    epstein_patterns = [
        r'\bepstein\b',
        r'\bjeffrey\s+epstein\b',
        r'\bj\.?\s*epstein\b',
        r'@epstein',  # email domain
    ]
    
    # Check From and To fields
    from_addr = (metadata.get("from_addr") or "").lower()
    to_addr = (metadata.get("to_addr") or "").lower()
    
    for pattern in epstein_patterns:
        if re.search(pattern, from_addr, re.IGNORECASE):
            return True
        if re.search(pattern, to_addr, re.IGNORECASE):
            return True
    
    # Also check first 1000 chars of body for strong indicators
    # (e.g., "RE: Jeffrey Epstein", "Mr. Epstein", etc.)
    if text:
        preview = text[:1000].lower()
        if re.search(r'\b(?:mr\.?|jeffrey)\s+epstein\b', preview, re.IGNORECASE):
            return True
    
    return False


if __name__ == "__main__":
    # Test with sample text
    sample = """From: sender@example.com
To: recipient@example.com
Subject: Test Email
Date: January 1, 2020

This is a test email body.
"""
    result = extract_email_metadata(sample)
    print(f"From: {result['from_addr']}")
    print(f"To: {result['to_addr']}")
    print(f"Subject: {result['subject']}")
    print(f"Date: {result['date']}")
    print(f"Is Epstein email: {is_epstein_email(result, sample)}")
