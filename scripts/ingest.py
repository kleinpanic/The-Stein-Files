#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import requests
from pypdf import PdfReader

from scripts.common import (
    RAW_DIR,
    load_catalog,
    save_catalog,
    sha256_file,
    slugify,
    detect_mime,
    utc_now_iso,
    ensure_sources,
    write_json,
)

CONFIG_PATH = Path("config/sources.json")


def load_sources() -> List[Dict[str, Any]]:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return data.get("documents", [])


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with dest.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def count_pdf_pages(path: Path) -> int | None:
    try:
        reader = PdfReader(str(path))
        return len(reader.pages)
    except Exception:
        return None


def ingest() -> None:
    sources = load_sources()
    catalog = load_catalog()
    updated = False

    for doc in sources:
        url = doc["source_url"]
        filename = doc.get("file_name") or Path(url).name or "document.bin"
        tmp_path = Path("/tmp/epstein-ingest") / filename
        download_file(url, tmp_path)

        sha = sha256_file(tmp_path)
        existing = next((e for e in catalog if e.get("sha256") == sha), None)

        if existing:
            ensure_sources(existing, doc["source_name"], url)
            existing["downloaded_at"] = utc_now_iso()
            if doc.get("tags"):
                existing["tags"] = sorted(set(existing.get("tags", [])) | set(doc["tags"]))
            write_json(Path("data/meta") / f"{existing['id']}.json", existing)
            tmp_path.unlink(missing_ok=True)
            updated = True
            continue

        doc_id = f"{sha[:12]}-{slugify(doc['title'])}"
        raw_dir = RAW_DIR / doc_id
        raw_dir.mkdir(parents=True, exist_ok=True)
        dest_path = raw_dir / filename
        tmp_path.replace(dest_path)

        mime_type = detect_mime(dest_path)
        pages = count_pdf_pages(dest_path) if dest_path.suffix.lower() == ".pdf" else None

        entry = {
            "id": doc_id,
            "title": doc["title"],
            "source_name": doc["source_name"],
            "source_url": url,
            "release_date": doc.get("release_date"),
            "downloaded_at": utc_now_iso(),
            "sha256": sha,
            "file_path": str(dest_path),
            "mime_type": mime_type,
            "pages": pages,
            "tags": doc.get("tags", []),
            "notes": doc.get("notes"),
            "is_official": bool(doc.get("is_official", True)),
            "license_or_terms": doc.get("license_or_terms", "as published by source"),
            "sources": [{"source_name": doc["source_name"], "source_url": url}],
        }

        write_json(Path("data/meta") / f"{doc_id}.json", entry)
        catalog.append(entry)
        updated = True

    if updated:
        catalog = sorted(catalog, key=lambda e: e.get("release_date") or "")
        save_catalog(catalog)


if __name__ == "__main__":
    ingest()
