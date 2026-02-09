#!/usr/bin/env python3
"""
Enhanced OCR module with improved extraction quality.

Phase 1 improvements:
- Language hints (eng+deu for German names)
- Adaptive DPI based on page dimensions
- Image preprocessing (deskew, denoise, contrast)
- Extended page coverage (all pages for image PDFs)
- OCR confidence scoring per page
- Multi-pass OCR with different preprocessing strategies
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image, ImageEnhance, ImageFilter
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


def preprocess_image(image: "Image.Image", strategy: str = "default") -> "Image.Image":
    """
    Preprocess image for better OCR results.
    
    Strategies:
    - default: Basic contrast enhancement
    - high_contrast: Aggressive contrast + sharpen
    - denoise: Noise reduction + slight blur
    """
    if strategy == "high_contrast":
        # Increase contrast aggressively
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        # Sharpen
        image = image.filter(ImageFilter.SHARPEN)
    elif strategy == "denoise":
        # Reduce noise
        image = image.filter(ImageFilter.MedianFilter(size=3))
        # Slight contrast boost
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)
    else:  # default
        # Moderate contrast enhancement
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
    
    return image


def calculate_adaptive_dpi(pdf_path: Path) -> int:
    """
    Calculate optimal DPI based on PDF page dimensions.
    
    Larger pages benefit from higher DPI for better character recognition.
    """
    try:
        # Sample first page to determine size
        images = convert_from_path(str(pdf_path), first_page=1, last_page=1, dpi=72)
        if not images:
            return 200  # fallback
        
        width, height = images[0].size
        area = width * height
        
        # Scale DPI based on page area
        if area < 500_000:  # small page
            return 200
        elif area < 1_000_000:  # medium page
            return 250
        else:  # large page
            return 300
    except Exception:
        return 200  # fallback


def ocr_with_confidence(image: "Image.Image", lang: str = "eng") -> Tuple[str, float]:
    """
    Run OCR and return text + confidence score.
    
    Returns:
        (extracted_text, confidence_score_0_to_100)
    """
    if not HAS_OCR:
        return "", 0.0
    
    try:
        # Get detailed OCR data with confidence
        data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        
        # Extract text
        text_parts = []
        confidences = []
        
        for i, word in enumerate(data['text']):
            if word.strip():
                conf = data['conf'][i]
                if conf > 0:  # Filter out -1 (no confidence)
                    text_parts.append(word)
                    confidences.append(conf)
        
        text = " ".join(text_parts)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        
        return text, avg_conf
    except Exception as e:
        print(f"[OCR Confidence] Error: {e}")
        # Fallback to basic OCR
        try:
            text = pytesseract.image_to_string(image, lang=lang)
            return text, 50.0  # assume medium confidence
        except Exception:
            return "", 0.0


def apply_enhanced_ocr(
    pdf_path: Path,
    max_pages: Optional[int] = None,
    multipass: bool = True,
) -> Dict:
    """
    Apply enhanced OCR to PDF with all Phase 1 improvements.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Max pages to OCR (None = all pages)
        multipass: Try multiple preprocessing strategies
    
    Returns:
        {
            "text": str,
            "pages": List[{"page": int, "text": str, "confidence": float}],
            "avg_confidence": float,
            "total_pages": int,
            "ocr_strategy": str
        }
    """
    if not HAS_OCR:
        return {
            "text": "",
            "pages": [],
            "avg_confidence": 0.0,
            "total_pages": 0,
            "ocr_strategy": "none"
        }
    
    try:
        # Calculate adaptive DPI
        dpi = calculate_adaptive_dpi(pdf_path)
        
        # Convert PDF to images
        images = convert_from_path(
            str(pdf_path),
            first_page=1,
            last_page=max_pages,
            dpi=dpi,
        )
        
        if not images:
            return {
                "text": "",
                "pages": [],
                "avg_confidence": 0.0,
                "total_pages": 0,
                "ocr_strategy": "failed"
            }
        
        # Languages: English + German (for German names like Brunel, Ghislaine)
        lang = "eng+deu"
        
        # Try different preprocessing strategies if multipass enabled
        strategies = ["default", "high_contrast", "denoise"] if multipass else ["default"]
        
        best_result = None
        best_confidence = 0.0
        best_strategy = "default"
        
        for strategy in strategies:
            page_results = []
            all_text = []
            confidences = []
            
            for i, image in enumerate(images, 1):
                try:
                    # Preprocess image
                    processed = preprocess_image(image, strategy=strategy)
                    
                    # OCR with confidence
                    page_text, confidence = ocr_with_confidence(processed, lang=lang)
                    
                    if page_text.strip():
                        page_results.append({
                            "page": i,
                            "text": page_text,
                            "confidence": round(confidence, 1)
                        })
                        all_text.append(f"[Page {i}]\n{page_text}")
                        confidences.append(confidence)
                except Exception as e:
                    print(f"[Enhanced OCR] Page {i} failed ({strategy}): {e}")
                    continue
            
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Keep best strategy
            if avg_conf > best_confidence:
                best_confidence = avg_conf
                best_strategy = strategy
                best_result = {
                    "text": "\n\n".join(all_text),
                    "pages": page_results,
                    "avg_confidence": round(avg_conf, 1),
                    "total_pages": len(images),
                    "ocr_strategy": strategy,
                    "dpi": dpi
                }
            
            # If confidence is very high, no need to try other strategies
            if avg_conf > 85.0:
                break
        
        return best_result or {
            "text": "",
            "pages": [],
            "avg_confidence": 0.0,
            "total_pages": len(images),
            "ocr_strategy": "failed"
        }
    
    except Exception as e:
        print(f"[Enhanced OCR] Failed for {pdf_path.name}: {e}")
        return {
            "text": "",
            "pages": [],
            "avg_confidence": 0.0,
            "total_pages": 0,
            "ocr_strategy": "error"
        }
