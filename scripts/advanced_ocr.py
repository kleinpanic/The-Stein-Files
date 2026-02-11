#!/usr/bin/env python3
"""
Advanced OCR with adaptive preprocessing based on image statistics.

Handles low-quality scans by:
- Adaptive DPI (400+ for low-res sources)
- Adaptive thresholding (Otsu's method)
- Multiple Tesseract PSM modes
- Contrast enhancement based on image stats
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple, List, Optional
import subprocess

try:
    from pdf2image import convert_from_path
    from PIL import Image, ImageEnhance, ImageFilter, ImageStat, ImageOps
    import pytesseract
    import numpy as np
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


def analyze_image_quality(img: Image.Image) -> dict:
    """
    Analyze image statistics to determine preprocessing strategy.
    
    Returns:
        Dict with: mean, stddev, is_dark, is_low_contrast, is_blank
    """
    # Convert to grayscale
    img_gray = img.convert('L')
    stat = ImageStat.Stat(img_gray)
    
    mean = stat.mean[0]
    stddev = stat.stddev[0]
    
    return {
        'mean': mean,
        'stddev': stddev,
        'is_dark': mean < 80,
        'is_bright': mean > 180,
        'is_low_contrast': stddev < 30,
        'is_blank': mean > 240 or (mean > 200 and stddev < 10),
    }


def adaptive_preprocess(img: Image.Image, quality: dict) -> Image.Image:
    """
    Apply adaptive preprocessing based on image quality metrics.
    """
    # Convert to grayscale
    img_gray = img.convert('L')
    
    # Handle dark images
    if quality['is_dark']:
        # Increase brightness and contrast
        enhancer = ImageEnhance.Brightness(img_gray)
        img_gray = enhancer.enhance(1.3)
        enhancer = ImageEnhance.Contrast(img_gray)
        img_gray = enhancer.enhance(2.0)
    
    # Handle bright/washed out images
    elif quality['is_bright']:
        # Increase contrast
        enhancer = ImageEnhance.Contrast(img_gray)
        img_gray = enhancer.enhance(2.2)
    
    # Handle low contrast images
    elif quality['is_low_contrast']:
        # Strong contrast boost
        enhancer = ImageEnhance.Contrast(img_gray)
        img_gray = enhancer.enhance(2.5)
    
    # Default: moderate enhancement
    else:
        enhancer = ImageEnhance.Contrast(img_gray)
        img_gray = enhancer.enhance(1.5)
    
    # Apply sharpening
    img_sharp = img_gray.filter(ImageFilter.SHARPEN)
    
    # Binarize using Otsu's method (via PIL's autocontrast as approximation)
    # For true Otsu, would use cv2.threshold(cv2.THRESH_OTSU)
    # Simple alternative: use mean as threshold
    threshold = int(quality['mean'])
    img_binary = img_sharp.point(lambda x: 255 if x > threshold else 0, mode='1')
    
    return img_binary


def try_tesseract_psm_modes(img: Image.Image, modes: List[int] = None) -> Tuple[str, int]:
    """
    Try multiple Tesseract PSM (Page Segmentation Mode) settings.
    
    Common modes:
      3 = Fully automatic page segmentation (default)
      4 = Single column of text
      6 = Uniform block of text
     11 = Sparse text (find as much text as possible)
    
    Returns:
        Tuple of (best_text, best_mode)
    """
    if modes is None:
        modes = [6, 11, 4, 3]  # Try in order of likelihood
    
    best_text = ""
    best_mode = 6
    best_length = 0
    
    for psm in modes:
        try:
            config = f'--psm {psm}'
            text = pytesseract.image_to_string(img, lang='eng', config=config)
            
            # Keep result with most text (heuristic for best)
            if len(text.strip()) > best_length:
                best_text = text
                best_mode = psm
                best_length = len(text.strip())
        except Exception:
            continue
    
    return best_text, best_mode


def extract_text_advanced(
    pdf_path: Path,
    dpi: int = 400,
    max_pages: Optional[int] = None
) -> Tuple[str, dict]:
    """
    Extract text from PDF with advanced preprocessing.
    
    Args:
        pdf_path: Path to PDF file
        dpi: DPI for rendering (400+ recommended for low-quality scans)
        max_pages: Max pages to process (None = all)
    
    Returns:
        Tuple of (extracted_text, metadata)
    """
    if not HAS_DEPS:
        return "", {'error': 'Missing dependencies'}
    
    try:
        # Convert PDF to images
        if max_pages:
            images = convert_from_path(
                str(pdf_path),
                dpi=dpi,
                first_page=1,
                last_page=max_pages
            )
        else:
            images = convert_from_path(str(pdf_path), dpi=dpi)
        
        texts = []
        page_metadata = []
        
        for page_num, img in enumerate(images, 1):
            # Analyze image quality
            quality = analyze_image_quality(img)
            
            # Skip blank pages
            if quality['is_blank']:
                texts.append("")
                page_metadata.append({'page': page_num, 'status': 'blank'})
                continue
            
            # Apply adaptive preprocessing
            img_processed = adaptive_preprocess(img, quality)
            
            # Try multiple PSM modes
            text, best_psm = try_tesseract_psm_modes(img_processed)
            
            texts.append(text)
            page_metadata.append({
                'page': page_num,
                'status': 'extracted',
                'psm_mode': best_psm,
                'quality': quality,
                'text_length': len(text.strip())
            })
        
        # Combine texts
        full_text = "\n\n".join(texts)
        
        metadata = {
            'pages_processed': len(images),
            'total_text_length': len(full_text),
            'dpi': dpi,
            'page_details': page_metadata
        }
        
        return full_text, metadata
    
    except Exception as e:
        return "", {'error': str(e)}


def ocr_with_fallback(pdf_path: Path, max_pages: int = 5) -> str:
    """
    Try advanced OCR, fall back to basic if needed.
    
    This is a drop-in replacement for enhanced_ocr.apply_ocr_with_fallback().
    """
    if not HAS_DEPS:
        return ""
    
    # Try advanced OCR
    text, metadata = extract_text_advanced(pdf_path, dpi=400, max_pages=max_pages)
    
    # If we got reasonable text, return it
    if len(text.strip()) > 100:
        return text
    
    # Otherwise, try with even higher DPI
    text2, metadata2 = extract_text_advanced(pdf_path, dpi=600, max_pages=max_pages)
    
    if len(text2.strip()) > len(text.strip()):
        return text2
    
    return text


if __name__ == '__main__':
    # Test on a sample PDF
    import sys
    if len(sys.argv) > 1:
        pdf = Path(sys.argv[1])
        text, metadata = extract_text_advanced(pdf, dpi=400, max_pages=1)
        print(f"Extracted {len(text)} chars")
        print(f"Metadata: {metadata}")
        print(f"\nText:\n{text[:500]}")
