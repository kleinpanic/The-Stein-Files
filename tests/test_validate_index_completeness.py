import json
from pathlib import Path

import pytest

from scripts.validate import validate_index


def test_validate_index_fails_when_catalog_entry_missing_from_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    (tmp_path / "data/meta").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/derived/index/shards/unit").mkdir(parents=True, exist_ok=True)

    # Two catalog entries...
    catalog = [
        {"id": "doc1", "file_path": "data/raw/doc1.pdf", "sha256": "a" * 64},
        {"id": "doc2", "file_path": "data/raw/doc2.pdf", "sha256": "b" * 64},
    ]
    (tmp_path / "data/meta/catalog.json").write_text(
        json.dumps(catalog), encoding="utf-8"
    )

    # ...but only one appears in the shard.
    shard_path = tmp_path / "data/derived/index/shards/unit/2026.json"
    shard_path.write_text(json.dumps([{"id": "doc1"}]), encoding="utf-8")

    manifest = {
        "generated_at": "2026-01-01T00:00:00Z",
        "total_docs": 1,
        "sources": ["Unit"],
        "years": ["2026"],
        "shards": [
            {
                "source_slug": "unit",
                "source_name": "Unit",
                "year": "2026",
                "count": 1,
                "path": str(Path("data/derived/index/shards/unit/2026.json")),
            }
        ],
    }
    (tmp_path / "data/derived/index/manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    with pytest.raises(ValueError, match=r"Index missing 1 catalog entries"):
        validate_index()
