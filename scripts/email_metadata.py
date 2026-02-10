#!/usr/bin/env python3
"""
Email metadata extraction from text content.

Extracts From, To, Subject, and Date fields from email/correspondence documents.
Handles OCR-garbled text and various email format variations.
"""
from __future__ import annotations

import re
from typing import Dict, Optional, List, Tuple


def clean_ocr_text(text: str) -> str:
    """Clean common OCR artifacts from text."""
    # Common OCR mistakes
    replacements = [
        (r'[|l]', 'I'),  # Pipe/lowercase-l to I (but be careful)
        (r'\s{2,}', ' '),  # Multiple spaces to single
    ]
    cleaned = text
    for old, new in replacements:
        cleaned = re.sub(old, new, cleaned)
    return cleaned.strip()


def extract_email_address(text: str) -> Optional[str]:
    """Extract email address from text."""
    # Standard email pattern
    email_match = re.search(
        r'[\w\.\-+]+@[\w\.\-]+\.\w+',
        text
    )
    if email_match:
        return email_match.group(0)
    return None


def extract_name_from_line(text: str) -> Optional[str]:
    """Extract name from email header line, handling various formats."""
    if not text or len(text.strip()) < 2:
        return None
    
    text = text.strip()
    
    # Skip if it's just numbers, dates, or garbage
    if re.match(r'^[\d\s\-/:.]+$', text):
        return None
    
    # Skip if too short or obviously wrong
    if len(text) < 3 or text.lower() in ['from', 'to', 'sent', 'date', 'subject']:
        return None
    
    # Format: "Name <email>" or "Name [mailto:email]"
    name_match = re.match(r'^([^<\[]+?)(?:\s*[<\[]|$)', text)
    if name_match:
        name = name_match.group(1).strip()
        if name and len(name) >= 2:
            return name
    
    # If we have an email, try to extract name before it
    if '@' in text:
        parts = text.split('@')[0]
        # email might be name.last@domain or just text before @
        return parts.split()[-1] if parts else None
    
    return text if len(text) >= 2 else None


def find_email_headers(text: str) -> List[Tuple[int, str, str]]:
    """
    Find all email header patterns in text.
    
    Returns list of (position, header_type, content) tuples.
    """
    headers = []
    
    # Patterns for headers with content on same line
    patterns = [
        (r'(?:^|\n)\s*From\s*:\s*(.+?)(?=\n|$)', 'from'),
        (r'(?:^|\n)\s*To\s*:\s*(.+?)(?=\n|$)', 'to'),
        (r'(?:^|\n)\s*Subject\s*:\s*(.+?)(?=\n|$)', 'subject'),
        (r'(?:^|\n)\s*(?:Sent|Date)\s*:\s*(.+?)(?=\n|$)', 'date'),
        (r'(?:^|\n)\s*Cc\s*:\s*(.+?)(?=\n|$)', 'cc'),
    ]
    
    for pattern, header_type in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            content = match.group(1).strip()
            if content and len(content) > 1:
                headers.append((match.start(), header_type, content))
    
    return sorted(headers, key=lambda x: x[0])


def is_valid_from_content(content: str) -> bool:
    """Check if From content appears valid (has a name or email)."""
    if not content or len(content) < 3:
        return False
    
    # Must have at least some alphabetic characters
    if not re.search(r'[a-zA-Z]{2,}', content):
        return False
    
    # Skip if it's just a date/time
    if re.match(r'^[\d\s\-/:.,]+(?:am|pm)?$', content, re.IGNORECASE):
        return False
    
    # Skip common OCR garbage and wrong field captures
    garbage_patterns = [
        r'^(?:cipher|cipher\s+\d)',  # OCR for "December" etc
        r'^(?:sent|date)\s*[:\s]',   # Captured "Sent:" line instead
        r'^\d+:\d+\s*(?:am|pm)',     # Time only
        r'^(?:to|cc|subject)\s*:',   # Captured wrong header
        r'^(?:to|cc)\s*$',           # Just "To" or "Cc"
        r'^sent\s+\w+\s+\d',         # "Sent Mon 5/15/2017..."
    ]
    for pattern in garbage_patterns:
        if re.match(pattern, content, re.IGNORECASE):
            return False
    
    return True


def extract_email_metadata(text: str) -> Dict[str, Optional[str]]:
    """
    Extract email header fields from text content.
    
    Args:
        text: Extracted text content from PDF
        
    Returns:
        Dictionary with from_addr, to_addr, subject, date, and cc fields
    """
    metadata = {
        "from_addr": None,
        "to_addr": None,
        "subject": None,
        "date": None,
        "cc": None,
    }
    
    if not text:
        return metadata
    
    # Look in first 4000 chars - emails can have forwarded content with real headers further in
    header_section = text[:4000]
    
    # Find all headers
    headers = find_email_headers(header_section)
    
    # For each type, find the best (valid) match
    from_candidates = []
    to_candidates = []
    subject_candidates = []
    date_candidates = []
    cc_candidates = []
    
    for pos, header_type, content in headers:
        if header_type == 'from' and is_valid_from_content(content):
            from_candidates.append((pos, content))
        elif header_type == 'to' and len(content) > 2:
            to_candidates.append((pos, content))
        elif header_type == 'subject' and len(content) > 1:
            subject_candidates.append((pos, content))
        elif header_type == 'date' and len(content) > 5:
            date_candidates.append((pos, content))
        elif header_type == 'cc' and len(content) > 2:
            cc_candidates.append((pos, content))
    
    # Pick best candidate (prefer those with email addresses, then first valid)
    for candidates, field, is_email_field in [
        (from_candidates, 'from_addr', True),
        (to_candidates, 'to_addr', True),
        (subject_candidates, 'subject', False),
        (date_candidates, 'date', False),
        (cc_candidates, 'cc', True),
    ]:
        if not candidates:
            continue
        
        if is_email_field:
            # Prefer entries with @ sign
            with_email = [(p, c) for p, c in candidates if '@' in c]
            if with_email:
                metadata[field] = with_email[0][1]
                continue
        
        # Otherwise take first valid
        metadata[field] = candidates[0][1]
    
    # Special handling: look for "From: Name [mailto:email]" pattern
    mailto_match = re.search(
        r'From:\s*([^<\[\n]+?)\s*[\[<]mailto:([^\]>]+)',
        header_section,
        re.IGNORECASE
    )
    if mailto_match and not metadata['from_addr']:
        name = mailto_match.group(1).strip()
        email = mailto_match.group(2).strip()
        if name and email:
            metadata['from_addr'] = f"{name} <{email}>"
        elif email:
            metadata['from_addr'] = email
    
    # Clean up extracted values
    for field in ['from_addr', 'to_addr', 'subject', 'date', 'cc']:
        if metadata[field]:
            # Remove excessive whitespace
            metadata[field] = re.sub(r'\s+', ' ', metadata[field]).strip()
            # Truncate overly long values (likely garbage)
            if len(metadata[field]) > 200:
                metadata[field] = metadata[field][:200] + '...'
    
    # If still no From, mark explicitly
    if not metadata['from_addr']:
        metadata['from_addr'] = "[Not visible in document]"
    if not metadata['to_addr']:
        metadata['to_addr'] = "[Not visible in document]"
    
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
        r'\bdarren\s*(?:k\.?\s*)?indyke\b',  # Epstein's lawyer
        r'\blesley\s+groff\b',  # Epstein's assistant
    ]
    
    # Check From and To fields
    from_addr = (metadata.get("from_addr") or "").lower()
    to_addr = (metadata.get("to_addr") or "").lower()
    subject = (metadata.get("subject") or "").lower()
    
    for pattern in epstein_patterns:
        if re.search(pattern, from_addr, re.IGNORECASE):
            return True
        if re.search(pattern, to_addr, re.IGNORECASE):
            return True
        if re.search(pattern, subject, re.IGNORECASE):
            return True
    
    # Also check first 2000 chars of body for strong indicators
    if text:
        preview = text[:2000].lower()
        if re.search(r'\b(?:mr\.?|jeffrey)\s+epstein\b', preview, re.IGNORECASE):
            return True
        # References to Epstein properties
        if re.search(r'\b(?:little\s+st\.?\s*james|great\s+st\.?\s*james|palm\s+beach)\b', preview, re.IGNORECASE):
            return True
    
    return False


if __name__ == "__main__":
    # Test with sample text (similar to OCR output)
    sample = """From:
Sent:                                   cipher 10, 2018 4:37 PM
To:                                      (USMS)'
Subject:                   FW Mr. Jeffrey Epstein.




From: Darren Indyke AOL [mailto:dindyke@aol.com]
Sent: Sunday September 30, 2018 1:45 PM
To: registry@doj.vi.gov
Subject: Mr. Jeffrey Epstein.


This is a test email body about Jeffrey Epstein travel.
"""
    result = extract_email_metadata(sample)
    print(f"From: {result['from_addr']}")
    print(f"To: {result['to_addr']}")
    print(f"Subject: {result['subject']}")
    print(f"Date: {result['date']}")
    print(f"Is Epstein email: {is_epstein_email(result, sample)}")
