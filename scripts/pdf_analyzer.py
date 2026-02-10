#!/usr/bin/env python3
"""
PDF analysis utilities for type detection, OCR, and metadata extraction.

Phase 1 enhancements:
- Enhanced OCR with language hints, adaptive DPI, preprocessing
- Enhanced metadata extraction (FBI numbers, person names, locations)
- Enhanced document classification (email, deposition, subpoena)
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# Phase 1: Import enhanced modules
try:
    from scripts.enhanced_ocr import apply_enhanced_ocr, HAS_OCR as HAS_ENHANCED_OCR
except ImportError:
    HAS_ENHANCED_OCR = False

try:
    from scripts.enhanced_metadata import extract_case_metadata
except ImportError:
    extract_case_metadata = None


def detect_pdf_type(pdf_path: Path, extracted_text: str) -> str:
    """
    Detect if PDF is text-based, image-only, or hybrid.
    
    Returns:
        "text" - mostly extractable text
        "image" - mostly images (needs OCR)
        "hybrid" - mix of both
    """
    text_len = len(extracted_text.strip())
    
    # Get file size for ratio calculation
    file_size = pdf_path.stat().st_size
    
    # Heuristics:
    # - <100 chars: likely image-only
    # - >1000 chars: likely text-based
    # - 100-1000: check ratio of text to file size
    
    if text_len < 100:
        return "image"
    
    if text_len > 1000:
        # Check text density (chars per KB)
        chars_per_kb = text_len / (file_size / 1024)
        if chars_per_kb < 10:
            return "hybrid"
        return "text"
    
    # 100-1000 chars: ambiguous, check density
    chars_per_kb = text_len / (file_size / 1024)
    if chars_per_kb < 5:
        return "image"
    elif chars_per_kb > 15:
        return "text"
    else:
        return "hybrid"


def calculate_text_quality_score(text: str) -> float:
    """
    Score text quality from 0-100 based on readability indicators.
    
    Factors:
    - Length (longer = better, up to a point)
    - Readable words vs gibberish
    - Sentence structure
    - Special character ratio
    """
    if not text:
        return 0.0
    
    text_len = len(text.strip())
    
    # Base score from length
    if text_len < 50:
        base_score = text_len / 50 * 30  # 0-30 points
    elif text_len < 500:
        base_score = 30 + ((text_len - 50) / 450 * 40)  # 30-70 points
    else:
        base_score = 70 + min((text_len - 500) / 5000 * 30, 30)  # 70-100 points
    
    # Penalty for high special character ratio
    alpha_count = sum(c.isalpha() for c in text)
    special_ratio = 1 - (alpha_count / max(text_len, 1))
    quality_penalty = special_ratio * 30  # Up to -30 points
    
    # Bonus for sentence structure
    sentence_count = text.count('.') + text.count('!') + text.count('?')
    if sentence_count > 0:
        words_per_sentence = len(text.split()) / sentence_count
        if 5 < words_per_sentence < 40:  # Reasonable sentence length
            base_score += 10
    
    final_score = max(0, min(100, base_score - quality_penalty))
    return round(final_score, 1)


def apply_ocr_to_pdf(pdf_path: Path, max_pages: int = 5) -> str:
    """
    Apply OCR to PDF using Tesseract.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Max pages to OCR (prevent long processing)
    
    Returns:
        Extracted text from OCR
    """
    if not HAS_OCR:
        return ""
    
    try:
        # Convert PDF pages to images
        images = convert_from_path(
            str(pdf_path),
            first_page=1,
            last_page=max_pages,
            dpi=200,  # Balance quality vs speed
        )
        
        # OCR each page
        text_parts = []
        for i, image in enumerate(images, 1):
            try:
                page_text = pytesseract.image_to_string(image, lang='eng')
                if page_text.strip():
                    text_parts.append(f"[Page {i}]\n{page_text}")
            except Exception as e:
                print(f"[OCR] Page {i} failed: {e}")
                continue
        
        return "\n\n".join(text_parts)
    
    except Exception as e:
        print(f"[OCR] Failed for {pdf_path.name}: {e}")
        return ""


def extract_file_numbers(text: str) -> List[str]:
    """
    Extract file/document numbers like EFTA00000001, etc.
    """
    patterns = [
        r'\bEFTA\d{8}\b',  # EFTA00000001
        r'\b[A-Z]{2,4}[-_]?\d{5,}\b',  # ABC-12345, ABC12345
        r'\b\d{4}-\d{4}-\d{4}\b',  # 1234-5678-9012
    ]
    
    numbers = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        numbers.update(matches)
    
    return sorted(numbers)


def extract_dates(text: str) -> List[str]:
    """
    Extract dates in various formats.
    """
    patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
        r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
    ]
    
    dates = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.update(matches)
    
    return sorted(dates)


def classify_document_type(title: str, text_sample: str) -> Optional[str]:
    """
    Enhanced document classification with photo/redaction detection.
    
    Phase 1 additions:
    - email category
    - case-photo subcategory
    - handwritten notes detection
    - deposition category
    - subpoena category
    
    Returns:
        Category slug or None for uncategorized
    """
    title_lower = title.lower()
    text_lower = text_sample.lower()
    
    # Email detection (new in Phase 1)
    has_email_headers = any(header in text_lower for header in ['from:', 'to:', 'subject:', 'sent:', 'date:'])
    has_email_pattern = '@' in text_lower and bool(re.search(r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b', text_lower, re.IGNORECASE))
    if has_email_headers and has_email_pattern:
        return 'email'
    
    # NEW: Booking/arrest records
    booking_markers = ['booking system', 'date arrested', 'fbi no:', 'fbi name:', 'charges:', 'trans id:']
    if any(marker in text_lower for marker in booking_markers):
        return 'booking-record'
    
    # NEW: Travel/entry records (CBP, TECS, passport control)
    travel_markers = ['customs and border protection', 'tecs', 'person encounter', 'entry inspection', 
                     'automated passport control', 'apis', 'on board', 'departure', 'arrival']
    if sum(1 for marker in travel_markers if marker in text_lower) >= 2:
        return 'travel-record'
    
    # NEW: Government forms (passport applications, etc.)
    form_markers = ['passport renewal', 'passport application', 'form approved', 'omb no.', 
                   'application for', 'applicant information', 'department of state']
    if sum(1 for marker in form_markers if marker in text_lower) >= 2:
        return 'government-form'
    
    # NEW: Financial records (bank statements, wire transfers)
    financial_markers = ['wire transfer', 'bank statement', 'account number', 'account no.',
                        'transaction', 'balance', 'deposit', 'withdrawal', 'swift', 'iban']
    if sum(1 for marker in financial_markers if marker in text_lower) >= 2:
        return 'financial-record'
    
    # NEW: Court orders
    order_markers = ['it is ordered', 'it is hereby ordered', 'the court orders', 'order of the court',
                    'this order', 'so ordered', 'judgment is entered']
    if any(marker in text_lower for marker in order_markers):
        return 'court-order'
    
    # NEW: Receipts/invoices
    receipt_markers = ['invoice', 'receipt', 'bill to', 'ship to', 'subtotal', 'total amount',
                      'payment received', 'amount due', 'purchase order']
    if sum(1 for marker in receipt_markers if marker in text_lower) >= 2:
        return 'receipt'
    
    # NEW: Transcripts (interview, phone, etc.)
    transcript_markers = ['transcript of', 'interview of', 'interviewed by', 'recording of',
                         'call transcript', 'phone call', 'begins at', 'ends at']
    if any(marker in text_lower for marker in transcript_markers):
        return 'transcript'
    
    # NEW: Contracts/agreements
    contract_markers = ['agreement between', 'contract between', 'party of the first', 'hereby agree',
                       'terms and conditions', 'in witness whereof', 'executed this']
    if any(marker in text_lower for marker in contract_markers):
        return 'contract'
    
    # NEW: Address/contact lists
    contact_markers = ['contact list', 'address book', 'phone numbers', 'directory', 'rolodex']
    if any(marker in text_lower for marker in contact_markers):
        return 'contact-list'
    
    # NEW: Schedules/calendars
    schedule_markers = ['schedule', 'calendar', 'itinerary', 'appointment', 'agenda']
    # Need both a schedule word and date-like patterns
    has_schedule_word = any(marker in text_lower for marker in schedule_markers)
    has_dates = bool(re.search(r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', text_lower))
    if has_schedule_word and has_dates:
        return 'schedule'
    
    # NEW: Phone/telecom records (AT&T, Verizon, etc.)
    telecom_markers = ['at&t', 'verizon', 'sprint', 't-mobile', 'voice usage', 'call record',
                      'phone records', 'wireline', 'mobility voice', 'originating number',
                      'terminating number', 'elapsed time', 'queried for records']
    if sum(1 for marker in telecom_markers if marker in text_lower) >= 2:
        return 'phone-record'
    
    # NEW: Internet/data records
    internet_markers = ['ip address', 'subscriber information', 'internet protocol', 'browser history',
                       'email account', 'login history', 'session log', 'isp records']
    if sum(1 for marker in internet_markers if marker in text_lower) >= 2:
        return 'internet-record'
    
    # NEW: Search warrants/affidavits
    warrant_markers = ['search warrant', 'affidavit', 'probable cause', 'magistrate judge',
                      'authorize the search', 'premises described']
    if any(marker in text_lower for marker in warrant_markers):
        return 'search-warrant'
    
    # NEW: Indictments/criminal charges
    indictment_markers = ['indictment', 'grand jury', 'count one', 'count two', 'conspiracy to',
                         'in violation of', 'united states of america v.', 'criminal complaint']
    if sum(1 for marker in indictment_markers if marker in text_lower) >= 2:
        return 'indictment'
    
    # NEW: FBI/law enforcement records
    fbi_markers = ['federal bureau of investigation', 'fbi', 'case id:', 'case number:',
                  'special agent', 'date of report', 'synopsis', 'details:']
    if sum(1 for marker in fbi_markers if marker in text_lower) >= 2:
        return 'fbi-record'
    
    # Deposition detection (new in Phase 1)
    has_qa_pattern = bool(re.search(r'\bQ:.*?\bA:', text_lower, re.DOTALL))
    has_deposition_markers = any(word in text_lower for word in ['deposition', 'deposed', 'sworn testimony', 'court reporter'])
    if has_qa_pattern or has_deposition_markers:
        return 'deposition'
    
    # Subpoena detection (new in Phase 1)
    has_subpoena_markers = any(word in text_lower for word in ['subpoena', 'compel', 'appear and testify', 'bring with you'])
    has_court_command = 'you are commanded' in text_lower or 'you are hereby ordered' in text_lower
    if has_subpoena_markers or has_court_command:
        return 'subpoena'
    
    # Photo detection (FBI evidence photos) - robust against OCR errors
    has_photographer = 'photographer' in text_lower
    has_location = 'location' in text_lower
    has_case_marker = 'case' in text_lower and any(marker in text_lower for marker in ['case id', 'case ip', 'case 1d', 'caseid'])
    has_fbi_case_number = bool(re.search(r'\b\d{1,3}[a-z]{1,3}-[a-z]{2,5}-\d{5,7}\b', text_lower, re.IGNORECASE))
    
    if has_photographer and has_location and (has_case_marker or has_fbi_case_number):
        return 'evidence-photo'
    
    # Case photo detection (new in Phase 1) - photos that aren't FBI evidence photos
    # Characteristics: very short text, mentions of photo/image, large file size
    text_len = len(text_sample.strip())
    if text_len < 100 and any(word in text_lower for word in ['photo', 'image', 'picture', 'photograph']):
        return 'case-photo'
    
    # Handwritten notes detection (new in Phase 1)
    # Low quality + short text + image PDF indicators
    if text_len < 150:
        handwriting_indicators = ['handwritten', 'written by hand', 'manuscript', 'note', 'scrawl']
        if any(word in text_lower for word in handwriting_indicators):
            return 'handwritten-note'
    
    # Flight logs (check early - specific pattern)
    if 'flight' in text_lower and ('log' in text_lower or 'manifest' in text_lower):
        return 'flight-log'
    if 'tail number' in text_lower or ('aircraft' in text_lower and 'date' in text_lower):
        return 'flight-log'
    
    # Evidence lists
    if 'evidence' in text_lower and ('list' in text_lower or 'index' in text_lower):
        return 'evidence-list'
    if any(word in title_lower for word in ['evidence', 'exhibit']) and 'list' in title_lower:
        return 'evidence-list'
    
    # Legal filings
    if 'plaintiff' in text_lower or 'defendant' in text_lower:
        return 'legal-filing'
    if 'united states district court' in text_lower or 'docket' in text_lower:
        return 'legal-filing'
    
    # Correspondence
    if any(word in text_lower for word in ['dear ', 'sincerely', 'regards', 'cc:']):
        return 'correspondence'
    
    # Memorandum
    if 'memorandum' in text_lower or 'memo' in title_lower:
        return 'memorandum'
    if text_lower.strip().startswith('to:') or text_lower.strip().startswith('from:'):
        return 'memorandum'
    
    # Reports
    if any(word in title_lower for word in ['report', 'analysis', 'summary']):
        return 'report'
    if 'findings' in text_lower or 'investigation' in text_lower:
        return 'report'
    
    # Fallback: scanned-document for low-quality image PDFs
    # This catches image PDFs that don't match any specific category
    text_len = len(text_sample.strip())
    if text_len < 200:  # Very little extractable text (likely image-only PDF)
        return 'scanned-document'
    
    return None


def analyze_pdf(pdf_path: Path, extracted_text: str, enable_ocr: bool = True) -> Dict:
    """
    Comprehensive PDF analysis with Phase 1 enhancements.
    
    Returns dict with:
        - pdf_type: str
        - has_extractable_text: bool
        - ocr_applied: bool
        - text_quality_score: float
        - extracted_file_numbers: List[str]
        - extracted_dates: List[str]
        - document_category: Optional[str]
        - file_size_bytes: int
        - person_names: List[str] (Phase 1)
        - locations: List[str] (Phase 1)
        - case_numbers: List[str] (Phase 1)
        - ocr_confidence: float (Phase 1)
    """
    pdf_type = detect_pdf_type(pdf_path, extracted_text)
    quality_score = calculate_text_quality_score(extracted_text)
    
    # Apply OCR if needed - use enhanced OCR if available
    ocr_applied = False
    ocr_confidence = None
    final_text = extracted_text
    use_enhanced = os.getenv("EPPIE_ENHANCED_OCR", "1") == "1"
    
    if enable_ocr and pdf_type == "image" and quality_score < 30:
        print(f"[PDF Analysis] Applying OCR to {pdf_path.name}")
        
        if use_enhanced and HAS_ENHANCED_OCR:
            # Use enhanced OCR with all Phase 1 improvements
            print(f"[PDF Analysis] Using enhanced OCR for {pdf_path.name}")
            ocr_result = apply_enhanced_ocr(pdf_path, max_pages=None, multipass=True)
            if ocr_result["text"]:
                final_text = ocr_result["text"]
                ocr_applied = True
                ocr_confidence = ocr_result["avg_confidence"]
                quality_score = calculate_text_quality_score(ocr_result["text"])
                print(f"[PDF Analysis] Enhanced OCR: {ocr_confidence:.1f}% confidence, strategy={ocr_result['ocr_strategy']}")
        else:
            # Fallback to basic OCR
            ocr_text = apply_ocr_to_pdf(pdf_path, max_pages=5)
            if ocr_text:
                final_text = ocr_text
                ocr_applied = True
                quality_score = calculate_text_quality_score(ocr_text)
    
    # Extract metadata - use enhanced extraction if available
    if extract_case_metadata:
        enhanced_metadata = extract_case_metadata(final_text)
        file_numbers = enhanced_metadata["file_numbers"]
        person_names = enhanced_metadata["person_names"]
        locations = enhanced_metadata["locations"]
        case_numbers = enhanced_metadata["case_numbers"]
    else:
        # Fallback to basic extraction
        file_numbers = extract_file_numbers(final_text)
        person_names = []
        locations = []
        case_numbers = []
    
    dates = extract_dates(final_text)
    
    # Classify document
    title = pdf_path.name
    doc_category = classify_document_type(title, final_text)
    
    result = {
        "pdf_type": pdf_type,
        "has_extractable_text": len(extracted_text.strip()) > 50,
        "ocr_applied": ocr_applied,
        "text_quality_score": quality_score,
        "extracted_file_numbers": file_numbers[:10],
        "extracted_dates": dates[:20],
        "document_category": doc_category,
        "file_size_bytes": pdf_path.stat().st_size,
        "enhanced_text": final_text if ocr_applied else None,
        # Phase 1 additions
        "person_names": person_names,
        "locations": locations,
        "case_numbers": case_numbers,
    }
    
    if ocr_confidence is not None:
        result["ocr_confidence"] = ocr_confidence
    
    return result


def detect_photo_content(pdf_path: Path) -> bool:
    """
    Detect if PDF contains primarily photographic content (people, scenes)
    vs document scans (text pages, forms).
    
    Heuristics:
    - Very low text extraction (<50 chars)
    - File size patterns (photos tend to be larger)
    - Filename patterns (IMG_, DSC_, photo, etc.)
    
    Returns:
        True if likely a photo, False if likely a document scan
    """
    filename = pdf_path.name.lower()
    
    # Check filename patterns
    photo_patterns = ['img_', 'dsc_', 'photo', 'image', '_img', 'picture']
    if any(pattern in filename for pattern in photo_patterns):
        return True
    
    # Check file size - single-page photos tend to be >200KB
    file_size_kb = pdf_path.stat().st_size / 1024
    if file_size_kb > 300:  # Likely high-res photo
        # Would need to check page count here, but that requires pypdf
        pass
    
    return False


def detect_redaction(extracted_text: str, pdf_path: Path) -> bool:
    """
    Detect if document contains significant redactions.
    
    Indicators:
    - Repeated REDACTED markers in text
    - Very sparse text with large file size (blacked out areas)
    - Special redaction markers
    
    Returns:
        True if document appears heavily redacted
    """
    text_lower = extracted_text.lower()
    
    # Check for explicit redaction markers
    redaction_indicators = [
        'redacted', '[redacted]', '(redacted)', 'xxxxx', '[x]',
        'withheld', 'exemption', 'b(1)', 'b(2)', 'b(3)'  # FOIA exemptions
    ]
    
    redaction_count = sum(text_lower.count(indicator) for indicator in redaction_indicators)
    if redaction_count > 3:
        return True
    
    # Check for sparse text with large file (possible visual redactions)
    text_len = len(extracted_text.strip())
    file_size_kb = pdf_path.stat().st_size / 1024
    
    if text_len < 200 and file_size_kb > 100:
        # Very little text, large file = likely redacted/blacked out
        chars_per_kb = text_len / file_size_kb
        if chars_per_kb < 2:
            return True
    
    return False


