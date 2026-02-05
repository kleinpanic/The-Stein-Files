#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from pdfminer.high_level import extract_text

from scripts.common import (
    DERIVED_INDEX_DIR,
    DERIVED_TEXT_DIR,
    load_catalog,
    slugify,
    utc_now_iso,
    write_json,
)


MAX_CONTENT_CHARS = 20000
TEXT_EXTENSIONS = {".txt", ".rtf", ".csv"}


def extract_pdf_text(pdf_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdftotext = shutil.which("pdftotext")
    try:
        if pdftotext:
            subprocess.run(
                [pdftotext, "-layout", str(pdf_path), str(output_path)],
                check=True,
            )
            return
        text = extract_text(str(pdf_path))
        output_path.write_text(text, encoding="utf-8")
    except Exception as exc:
        print(f"[extract] failed to read {pdf_path.name}: {exc}")
        output_path.write_text("", encoding="utf-8")


def extract_all() -> None:
    catalog = load_catalog()
    index_docs: List[Dict[str, Any]] = []
    shards: Dict[tuple[str, str], List[Dict[str, Any]]] = {}

    for entry in catalog:
        file_path = Path(entry["file_path"])
        text_path = DERIVED_TEXT_DIR / f"{entry['id']}.txt"
        mime_type = entry.get("mime_type", "")
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            extract_pdf_text(file_path, text_path)
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
        }
        index_docs.append(doc)

        source_name = entry.get("source_name", "Unknown")
        source_slug = slugify(source_name)
        release_date = entry.get("release_date", "")
        year = release_date[:4] if release_date[:4].isdigit() else "unknown"
        shards.setdefault((source_slug, year), []).append(doc)

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
