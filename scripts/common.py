from __future__ import annotations

import hashlib
import json
import mimetypes
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

CATALOG_PATH = Path("data/meta/catalog.json")
SCHEMA_PATH = Path("data/meta/schema.json")
DATA_META_DIR = Path("data/meta")
RAW_DIR = Path("data/raw")
DERIVED_TEXT_DIR = Path("data/derived/text")
DERIVED_INDEX_DIR = Path("data/derived/index")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(text: str) -> str:
    cleaned = []
    for ch in text.lower():
        if ch.isalnum():
            cleaned.append(ch)
        elif ch in {" ", "-", "_"}:
            cleaned.append("-")
    slug = "".join(cleaned)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "document"


def detect_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    if mime:
        return mime
    if path.suffix.lower() == ".pdf":
        return "application/pdf"
    return "application/octet-stream"


def load_catalog() -> List[Dict[str, Any]]:
    return load_json(CATALOG_PATH, [])


def save_catalog(entries: List[Dict[str, Any]]) -> None:
    write_json(CATALOG_PATH, entries)


def find_by_sha(entries: List[Dict[str, Any]], sha: str) -> Optional[Dict[str, Any]]:
    for entry in entries:
        if entry.get("sha256") == sha:
            return entry
    return None


def ensure_sources(entry: Dict[str, Any], source_name: str, source_url: str) -> None:
    sources = entry.setdefault("sources", [])
    for item in sources:
        if item.get("source_url") == source_url:
            return
    sources.append({"source_name": source_name, "source_url": source_url})


def current_git_sha() -> str:
    try:
        import subprocess

        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True)
            .strip()
        )
    except Exception:
        return "unknown"
