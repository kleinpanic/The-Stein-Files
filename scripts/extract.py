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
    write_json,
)


MAX_CONTENT_CHARS = 20000


def extract_pdf_text(pdf_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        subprocess.run(
            [pdftotext, "-layout", str(pdf_path), str(output_path)],
            check=True,
        )
        return
    text = extract_text(str(pdf_path))
    output_path.write_text(text, encoding="utf-8")


def extract_all() -> None:
    catalog = load_catalog()
    index_docs: List[Dict[str, Any]] = []

    for entry in catalog:
        file_path = Path(entry["file_path"])
        text_path = DERIVED_TEXT_DIR / f"{entry['id']}.txt"

        if file_path.suffix.lower() == ".pdf":
            extract_pdf_text(file_path, text_path)
        else:
            text_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")

        content = text_path.read_text(encoding="utf-8", errors="ignore")
        if len(content) > MAX_CONTENT_CHARS:
            content = content[:MAX_CONTENT_CHARS]

        index_docs.append(
            {
                "id": entry["id"],
                "title": entry["title"],
                "release_date": entry.get("release_date"),
                "tags": entry.get("tags", []),
                "source_name": entry.get("source_name"),
                "content": content,
            }
        )

    DERIVED_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    write_json(DERIVED_INDEX_DIR / "search-index.json", index_docs)


if __name__ == "__main__":
    extract_all()
