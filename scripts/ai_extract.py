#!/usr/bin/env python3
"""
AI-powered document metadata extraction using Gemini Pro Vision.

Usage:
    python ai_extract.py <pdf_path>
    python ai_extract.py data/raw/doc.pdf --pages 3
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional
import argparse

# Conversion from PDF to images
try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False


EXTRACTION_PROMPT = """You are analyzing a legal document from the Epstein case files.

Read this document image and extract the following information in JSON format:

{
  "document_type": "email | correspondence | legal-filing | deposition | flight-log | evidence-list | memorandum | report | maintenance | contact-list | other",
  "confidence": 0.0-1.0,
  "from": "sender name/email or null",
  "to": "recipient name/email or null",
  "subject": "subject line or null",
  "date": "YYYY-MM-DD or null",
  "people_mentioned": ["Full Name 1", "Full Name 2"],
  "locations_mentioned": ["Location 1", "Location 2"],
  "organizations": ["Org 1", "Org 2"],
  "key_topics": ["topic1", "topic2"],
  "summary": "2-3 sentence summary",
  "is_redacted": true/false,
  "quality_issues": "description of OCR/scan issues or null"
}

Rules:
- Only extract information that is clearly visible
- If a field is not visible/readable, set to null (do NOT guess)
- For people_mentioned: use full names only (first + last), max 10
- For dates: use ISO format (YYYY-MM-DD)
- For document_type: pick the most specific category
- Set is_redacted: true if you see black boxes or [REDACTED] markers
- Respond ONLY with valid JSON, no other text

RESPOND WITH JSON ONLY."""


def pdf_to_images(pdf_path: Path, max_pages: int = 3) -> list[Path]:
    """Convert PDF to images for vision model."""
    if not HAS_PDF2IMAGE:
        raise ImportError("pdf2image required: pip install pdf2image")
    
    # Convert PDF pages to images
    images = convert_from_path(pdf_path, first_page=1, last_page=max_pages, dpi=150)
    
    # Save to temp files
    temp_files = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, image in enumerate(images):
            img_path = Path(tmpdir) / f"page_{i+1}.png"
            image.save(img_path, "PNG")
            temp_files.append(img_path)
    
    return temp_files


def extract_with_gemini(image_paths: list[Path], prompt: str) -> dict:
    """Use Gemini CLI to extract metadata from document images."""
    # Use first image only for now (can extend to multi-image later)
    image_path = image_paths[0]
    
    # Call gemini CLI
    cmd = [
        "gemini",
        prompt,
        "--image", str(image_path),
        "--json"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"Gemini error: {result.stderr}", file=sys.stderr)
            return None
        
        # Parse JSON response
        response_text = result.stdout.strip()
        
        # Try to extract JSON from response (might have extra text)
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
            return json.loads(json_text)
        else:
            print(f"No JSON found in response: {response_text[:200]}", file=sys.stderr)
            return None
            
    except subprocess.TimeoutExpired:
        print("Gemini timeout", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        print(f"Response: {result.stdout[:500]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Gemini extraction failed: {e}", file=sys.stderr)
        return None


def extract_metadata_ai(pdf_path: Path, max_pages: int = 3) -> Optional[dict]:
    """
    Extract metadata from PDF using AI vision model.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Number of pages to analyze (default 3)
    
    Returns:
        Dictionary with extracted metadata, or None if failed
    """
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return None
    
    print(f"Converting PDF to images: {pdf_path.name}")
    
    try:
        # Convert to images
        images = pdf_to_images(pdf_path, max_pages)
        
        print(f"Extracting metadata with Gemini ({len(images)} pages)...")
        
        # Extract with Gemini
        metadata = extract_with_gemini(images, EXTRACTION_PROMPT)
        
        if metadata:
            print(f"✓ Extraction complete (confidence: {metadata.get('confidence', 0):.2f})")
            return metadata
        else:
            print("✗ Extraction failed", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="AI-powered PDF metadata extraction")
    parser.add_argument("pdf_path", type=Path, help="Path to PDF file")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages to analyze")
    parser.add_argument("--output", type=Path, help="Output JSON file (default: stdout)")
    
    args = parser.parse_args()
    
    # Extract
    metadata = extract_metadata_ai(args.pdf_path, args.pages)
    
    if metadata:
        # Output
        if args.output:
            args.output.write_text(json.dumps(metadata, indent=2))
            print(f"Saved to {args.output}")
        else:
            print(json.dumps(metadata, indent=2))
        
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
