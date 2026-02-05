import json
from pathlib import Path

import scripts.ingest as ingest


def test_ingest_resumes_without_redownload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data/meta").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/raw").mkdir(parents=True, exist_ok=True)

    config = {
        "defaults": {
            "timeout_seconds": 5,
            "requests_per_second": 0,
            "retry_max": 1,
            "backoff_base_seconds": 0.1,
        },
        "limits": {"local": {"max_docs_per_source": 0, "max_bytes_per_source": 0, "max_attempts_per_source": 0}},
        "sources": [
            {
                "id": "dummy",
                "name": "Dummy",
                "base_url": "https://example.test",
                "discovery": {"type": "dummy"},
                "is_official": True,
                "notes": "",
                "constraints": "",
                "release_date": "2026-01-01",
            }
        ],
    }

    class FakeAdapter:
        def __init__(self, source, config):
            self.source = source
            self.config = config

        def discover(self, session):
            return [
                ingest.DiscoveredFile(
                    url="https://example.test/a.pdf",
                    title="Doc A",
                    source_page=self.source.base_url,
                    release_date=self.source.release_date,
                    tags=[],
                ),
                ingest.DiscoveredFile(
                    url="https://example.test/b.pdf",
                    title="Doc B",
                    source_page=self.source.base_url,
                    release_date=self.source.release_date,
                    tags=[],
                ),
            ]

    downloads = {"count": 0}

    def fake_download(session, url, dest, timeout, headers=None, retry_max=0, backoff_base=0, limiter=None):
        downloads["count"] += 1
        dest.write_bytes(url.encode("utf-8"))
        return ingest.DownloadResult(
            size=len(url),
            content_type="application/pdf",
            content_disposition="",
            final_url=url,
            etag="",
            last_modified="",
        )

    monkeypatch.setattr(ingest, "load_config", lambda: config)
    monkeypatch.setattr(ingest, "adapter_for", lambda source, cfg, requester=None: FakeAdapter(source, cfg))
    monkeypatch.setattr(ingest, "download_file", fake_download)
    monkeypatch.setattr(ingest, "estimate_size", lambda *args, **kwargs: None)
    monkeypatch.setattr(ingest, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(ingest, "STATE_PATH", tmp_path / "data/meta/ingest_state.json")
    monkeypatch.setattr(ingest, "RAW_DIR", tmp_path / "data/raw")

    ingest.ingest()
    assert downloads["count"] == 2
    state = json.loads((tmp_path / "data/meta/ingest_state.json").read_text(encoding="utf-8"))
    assert len(state["dummy"]["seen_urls"]) == 2

    ingest.ingest()
    assert downloads["count"] == 2
