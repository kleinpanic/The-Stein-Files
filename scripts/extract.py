#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from pdfminer.high_level import extract_text

from scripts.common import (
    DATA_META_DIR,
    DERIVED_INDEX_DIR,
    DERIVED_TEXT_DIR,
    load_catalog,
    slugify,
    utc_now_iso,
    write_json,
)
from scripts.pdf_analyzer import analyze_pdf
from scripts.auto_tagging import generate_auto_tags
from scripts.email_metadata import extract_email_metadata, is_epstein_email


MAX_CONTENT_CHARS = 20000
TEXT_EXTENSIONS = {".txt", ".rtf", ".csv"}


def extract_pdf_text(pdf_path: Path, output_path: Path) -> Optional[str]:
    """
    Extract text from PDF and return it.
    
    Returns:
        Extracted text or None on failure
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdftotext = shutil.which("pdftotext")
    try:
        if pdftotext:
            subprocess.run(
                [pdftotext, "-layout", str(pdf_path), str(output_path)],
                check=True,
            )
            return output_path.read_text(encoding="utf-8", errors="ignore")
        text = extract_text(str(pdf_path))
        output_path.write_text(text, encoding="utf-8")
        return text
    except Exception as exc:
        print(f"[extract] failed to read {pdf_path.name}: {exc}")
        output_path.write_text("", encoding="utf-8")
        return ""


def extract_all() -> None:
    catalog = load_catalog()
    index_docs: List[Dict[str, Any]] = []
    shards: Dict[tuple[str, str], List[Dict[str, Any]]] = {}
    
    # Check if OCR is enabled
    enable_ocr = os.getenv("EPPIE_OCR_ENABLED", "0") == "1"
    # Force re-extraction (ignore existing derived text)
    force_reextract = os.getenv("EPPIE_FORCE_REEXTRACT", "0") == "1"

    catalog_updated = False

    for entry in catalog:
        file_path = Path(entry["file_path"])
        text_path = DERIVED_TEXT_DIR / f"{entry['id']}.txt"
        mime_type = entry.get("mime_type", "")
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            # Prefer existing derived text (preserves OCR output and avoids expensive re-extract)
            extracted_text: Optional[str] = None
            if not force_reextract and text_path.exists():
                extracted_text = text_path.read_text(encoding="utf-8", errors="ignore")

            if extracted_text is None:
                extracted_text = extract_pdf_text(file_path, text_path)

            # Analyze PDF for metadata enrichment only when needed
            has_analysis_fields = all(
                key in entry
                for key in [
                    "pdf_type",
                    "has_extractable_text",
                    "ocr_applied",
                    "text_quality_score",
                    "file_size_bytes",
                    "extracted_file_numbers",
                    "extracted_dates",
                    "document_category",
                    # Phase 1 fields - require re-analysis if missing
                    "person_names",
                    "locations",
                    "case_numbers",
                ]
            )

            should_ocr = enable_ocr and (not entry.get("ocr_applied", False))
            needs_analysis = force_reextract or (not has_analysis_fields) or should_ocr

            if extracted_text is not None and needs_analysis:
                analysis = analyze_pdf(file_path, extracted_text, enable_ocr=should_ocr)

                # Update catalog entry with analysis results
                if analysis:
                    entry["pdf_type"] = analysis["pdf_type"]
                    entry["has_extractable_text"] = analysis["has_extractable_text"]
                    entry["ocr_applied"] = analysis["ocr_applied"] or entry.get("ocr_applied", False)
                    entry["text_quality_score"] = analysis["text_quality_score"]
                    entry["file_size_bytes"] = analysis["file_size_bytes"]
                    entry["extracted_file_numbers"] = analysis["extracted_file_numbers"]
                    entry["extracted_dates"] = analysis["extracted_dates"]
                    entry["document_category"] = analysis["document_category"]
                    # Phase 1 fields
                    entry["person_names"] = analysis.get("person_names", [])
                    entry["locations"] = analysis.get("locations", [])
                    entry["case_numbers"] = analysis.get("case_numbers", [])
                    if "ocr_confidence" in analysis:
                        entry["ocr_confidence"] = analysis["ocr_confidence"]
                    catalog_updated = True

                    # If OCR was applied and produced better text, save it
                    if analysis.get("enhanced_text"):
                        text_path.write_text(analysis["enhanced_text"], encoding="utf-8")
                        print(f"[extract] Applied OCR to {file_path.name}")
                    
                    # Phase 2: Generate auto-tags
                    if extracted_text:
                        auto_tags = generate_auto_tags(
                            text=extracted_text,
                            category=analysis.get("document_category"),
                            person_names=analysis.get("person_names", []),
                            locations=analysis.get("locations", []),
                            release_date=entry.get("release_date"),
                        )
                        if auto_tags:
                            entry["auto_tags"] = auto_tags
                            print(f"[extract] Generated {len(auto_tags)} auto-tags for {file_path.name}")
            
            # Extract email metadata for email/correspondence documents
            if extracted_text and entry.get("document_category") in ["email", "correspondence"]:
                email_meta = extract_email_metadata(extracted_text)
                if email_meta.get("from_addr") or email_meta.get("to_addr") or email_meta.get("subject"):
                    entry["email_from"] = email_meta.get("from_addr")
                    entry["email_to"] = email_meta.get("to_addr")
                    entry["email_subject"] = email_meta.get("subject")
                    entry["email_date"] = email_meta.get("date")
                    entry["is_epstein_email"] = is_epstein_email(email_meta, extracted_text)
                    catalog_updated = True
                    print(f"[extract] Extracted email metadata from {file_path.name}")
        elif suffix in TEXT_EXTENSIONS or mime_type.startswith("text/"):
            text_path.parent.mkdir(parents=True, exist_ok=True)
            text_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            text_path.parent.mkdir(parents=True, exist_ok=True)
            text_path.write_text("", encoding="utf-8")

        content = text_path.read_text(encoding="utf-8", errors="ignore")
        if len(content) > MAX_CONTENT_CHARS:
            content = content[:MAX_CONTENT_CHARS]

        doc = {
            "id": entry["id"],
            "title": entry["title"],
            "release_date": entry.get("release_date", ""),
            "tags": entry.get("tags", []),
            "source_name": entry.get("source_name"),
            "file_name": Path(entry.get("file_path", "")).name,
            "content": content,
            # Add enriched metadata to search index
            "pdf_type": entry.get("pdf_type"),
            "text_quality_score": entry.get("text_quality_score"),
            "document_category": entry.get("document_category"),
            "extracted_file_numbers": entry.get("extracted_file_numbers", []),
            # Phase 2: Auto-tags for advanced search
            "auto_tags": entry.get("auto_tags", []),
            "person_names": entry.get("person_names", []),
            "locations": entry.get("locations", []),
            # Email metadata
            "email_from": entry.get("email_from"),
            "email_to": entry.get("email_to"),
            "email_subject": entry.get("email_subject"),
            "email_date": entry.get("email_date"),
            "is_epstein_email": entry.get("is_epstein_email", False),
        }
        index_docs.append(doc)

        source_name = entry.get("source_name", "Unknown")
        source_slug = slugify(source_name)
        release_date = entry.get("release_date", "")
        year = release_date[:4] if release_date[:4].isdigit() else "unknown"
        shards.setdefault((source_slug, year), []).append(doc)
    
    # Save updated catalog if metadata was enriched
    if catalog_updated:
        catalog_path = DATA_META_DIR / "catalog.json"
        write_json(catalog_path, catalog)
        print(f"[extract] Updated catalog with PDF analysis metadata")

    DERIVED_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    shards_dir = DERIVED_INDEX_DIR / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_at": utc_now_iso(),
        "total_docs": len(index_docs),
        "sources": sorted({doc["source_name"] for doc in index_docs}),
        "years": sorted({doc["release_date"][:4] for doc in index_docs if doc["release_date"][:4].isdigit()}),
        "shards": [],
    }

    for (source_slug, year), docs in sorted(shards.items()):
        shard_path = shards_dir / source_slug / f"{year}.json"
        shard_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(shard_path, docs)
        manifest["shards"].append(
            {
                "source_slug": source_slug,
                "source_name": docs[0]["source_name"] if docs else "Unknown",
                "year": year,
                "count": len(docs),
                "path": str(Path("data/derived/index/shards") / source_slug / f"{year}.json"),
            }
        )

    write_json(DERIVED_INDEX_DIR / "manifest.json", manifest)


if __name__ == "__main__":
    extract_all()
