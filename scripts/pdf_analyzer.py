#!/usr/bin/env python3
"""
PDF analysis utilities for type detection, OCR, and metadata extraction.
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
    Classify document type based on title and content.
    """
    title_lower = title.lower()
    text_lower = text_sample[:1000].lower()
    
    # Evidence/exhibits
    if any(word in title_lower for word in ['evidence', 'exhibit', 'list']):
        return "evidence-list"
    
    # Correspondence
    if any(word in text_lower for word in ['dear ', 'sincerely', 'regards', 'cc:']):
        return "correspondence"
    
    # Legal/court
    if any(word in text_lower for word in ['plaintiff', 'defendant', 'court', 'docket']):
        return "legal-filing"
    
    # Memos
    if any(word in title_lower for word in ['memo', 'memorandum']):
        return "memorandum"
    
    # Reports
    if any(word in title_lower for word in ['report', 'analysis', 'summary']):
        return "report"
    
    # Flight logs
    if any(word in title_lower for word in ['flight', 'log', 'manifest']):
        return "flight-log"
    
    return None


def analyze_pdf(pdf_path: Path, extracted_text: str, enable_ocr: bool = True) -> Dict:
    """
    Comprehensive PDF analysis.
    
    Returns dict with:
        - pdf_type: str
        - has_extractable_text: bool
        - ocr_applied: bool
        - text_quality_score: float
        - extracted_file_numbers: List[str]
        - extracted_dates: List[str]
        - document_category: Optional[str]
        - file_size_bytes: int
    """
    pdf_type = detect_pdf_type(pdf_path, extracted_text)
    quality_score = calculate_text_quality_score(extracted_text)
    
    # Apply OCR if needed
    ocr_applied = False
    final_text = extracted_text
    
    if enable_ocr and pdf_type == "image" and quality_score < 30:
        print(f"[PDF Analysis] Applying OCR to {pdf_path.name}")
        ocr_text = apply_ocr_to_pdf(pdf_path, max_pages=5)
        if ocr_text:
            final_text = ocr_text
            ocr_applied = True
            quality_score = calculate_text_quality_score(ocr_text)
    
    # Extract metadata from final text
    file_numbers = extract_file_numbers(final_text)
    dates = extract_dates(final_text)
    
    # Classify document
    title = pdf_path.name
    doc_category = classify_document_type(title, final_text)
    
    return {
        "pdf_type": pdf_type,
        "has_extractable_text": len(extracted_text.strip()) > 50,
        "ocr_applied": ocr_applied,
        "text_quality_score": quality_score,
        "extracted_file_numbers": file_numbers[:10],  # Limit to top 10
        "extracted_dates": dates[:20],  # Limit to top 20
        "document_category": doc_category,
        "file_size_bytes": pdf_path.stat().st_size,
        "enhanced_text": final_text if ocr_applied else None,
    }
