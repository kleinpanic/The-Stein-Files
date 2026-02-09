#!/usr/bin/env python3
"""
Full enhanced extraction on all 947 PDFs.
Run with enhanced OCR, metadata extraction, and Phase 1 features.
"""
import os
import sys
import time
from pathlib import Path

# Enable enhanced OCR and force re-extraction
os.environ["EPPIE_ENHANCED_OCR"] = "1"
os.environ["EPPIE_FORCE_REEXTRACT"] = "1"

sys.path.insert(0, str(Path.cwd()))

from scripts.extract import extract_all

if __name__ == "__main__":
    print("="*60)
    print("FULL ENHANCED EXTRACTION - Phase 1")
    print("="*60)
    print(f"Enhanced OCR: ENABLED")
    print(f"Total documents: 947")
    print(f"Expected time: 2-4 hours")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    
    start = time.time()
    extract_all()
    elapsed = time.time() - start
    
    print()
    print("="*60)
    print("EXTRACTION COMPLETE")
    print("="*60)
    print(f"Total time: {elapsed/60:.1f} minutes ({elapsed/3600:.1f} hours)")
    print(f"Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Next: Run 'make build' to regenerate site with enhanced metadata")
