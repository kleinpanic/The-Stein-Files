import json
from pathlib import Path

from scripts.extract import extract_all


def test_extract_builds_shards(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data/meta").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/raw").mkdir(parents=True, exist_ok=True)

    raw_path = tmp_path / "data/raw/doc1.txt"
    raw_path.write_text("test content for search", encoding="utf-8")

    catalog = [
        {
            "id": "doc1",
            "title": "Test Doc",
            "source_name": "Unit Test",
            "source_url": "https://example.test/doc1",
            "source_page": "https://example.test",
            "release_date": "2026-01-01",
            "downloaded_at": "2026-01-02T00:00:00Z",
            "sha256": "a" * 64,
            "file_path": str(raw_path),
            "mime_type": "text/plain",
            "pages": None,
            "tags": ["unit"],
            "notes": "",
            "is_official": True,
            "license_or_terms": "as published by source",
            "sources": [{"source_name": "Unit Test", "source_url": "https://example.test"}],
        }
    ]
    catalog_path = tmp_path / "data/meta/catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    extract_all()

    manifest_path = tmp_path / "data/derived/index/manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["total_docs"] == 1
    shard_path = Path(manifest["shards"][0]["path"])
    assert shard_path.exists()
    shard_docs = json.loads(shard_path.read_text(encoding="utf-8"))
    assert shard_docs[0]["content"].startswith("test content")
