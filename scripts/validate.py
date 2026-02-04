#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

from scripts.common import DERIVED_INDEX_DIR, DERIVED_TEXT_DIR, load_catalog, sha256_file


def load_schema() -> dict:
    return json.loads(Path("data/meta/schema.json").read_text(encoding="utf-8"))


def validate_catalog() -> None:
    schema = load_schema()
    catalog = load_catalog()
    for entry in catalog:
        validate(instance=entry, schema=schema)


def validate_files() -> None:
    catalog = load_catalog()
    for entry in catalog:
        path = Path(entry["file_path"])
        if not path.exists():
            raise FileNotFoundError(f"Missing raw file: {path}")
        if sha256_file(path) != entry["sha256"]:
            raise ValueError(f"SHA mismatch for {path}")
        text_path = DERIVED_TEXT_DIR / f"{entry['id']}.txt"
        if not text_path.exists():
            raise FileNotFoundError(f"Missing text file: {text_path}")


def validate_index() -> None:
    index_path = DERIVED_INDEX_DIR / "search-index.json"
    if not index_path.exists():
        raise FileNotFoundError("Missing search-index.json")
    index_docs = json.loads(index_path.read_text(encoding="utf-8"))
    catalog = {entry["id"] for entry in load_catalog()}
    for doc in index_docs:
        if doc["id"] not in catalog:
            raise ValueError(f"Index id not found in catalog: {doc['id']}")


def main() -> None:
    validate_catalog()
    validate_files()
    validate_index()


if __name__ == "__main__":
    main()
