from pathlib import Path

from scripts.doj_hub import collect_links
from scripts.ingest import DojCourtRecordsAdapter, DojFoiaAdapter, DojHubAdapter, SourceConfig


def test_court_records_adapter_parses_links():
    fixture = Path("tests/fixtures/doj_court_records.html").read_text(encoding="utf-8")
    links = collect_links(fixture)
    source = SourceConfig(
        id="doj-epstein-court-records",
        name="DOJ Epstein Library — Court Records",
        base_url="https://www.justice.gov/epstein/court-records",
        discovery={"type": "doj_court_records"},
        is_official=True,
        notes="",
        constraints="",
        release_date="",
        tags=["court-records"],
    )
    config = {"defaults": {"allowed_extensions": [".pdf"], "ignore_extensions": []}}
    adapter = DojCourtRecordsAdapter(source, config)

    class DummySession:
        def head(self, url, **kwargs):
            class HeadResp:
                status_code = 200
                headers = {"Content-Type": "application/pdf"}

            return HeadResp()

    files = adapter._parse_court_links(DummySession(), links, source.base_url)
    assert len(files) == 2
    assert files[0].title.startswith("United States v. Maxwell")
    assert files[0].release_date == "2021-01-01"
    assert "/multimedia/" in files[0].url


def test_hub_adapter_parses_links():
    fixture = Path("tests/fixtures/doj_hub.html").read_text(encoding="utf-8")
    source = SourceConfig(
        id="doj-epstein-hub",
        name="DOJ Epstein Library — Hub",
        base_url="https://www.justice.gov/epstein",
        discovery={"type": "doj_hub"},
        is_official=True,
        notes="",
        constraints="",
        release_date="",
        tags=["doj"],
    )
    config = {"defaults": {"allowed_extensions": [".pdf", ".csv"], "ignore_extensions": []}}
    adapter = DojHubAdapter(source, config)

    class DummyResp:
        text = fixture
        status_code = 200

        def raise_for_status(self):
            return None

    class DummySession:
        def get(self, *args, **kwargs):
            return DummyResp()

    files = adapter.discover(DummySession())
    assert len(files) == 2
    assert files[0].url.endswith("summary.pdf")


def test_foia_adapter_parses_multimedia_links():
    fixture = Path("tests/fixtures/doj_foia.html").read_text(encoding="utf-8")
    source = SourceConfig(
        id="doj-epstein-foia",
        name="DOJ Epstein Library — FOIA",
        base_url="https://www.justice.gov/epstein/foia",
        discovery={"type": "doj_foia"},
        is_official=True,
        notes="",
        constraints="",
        release_date="2026-01-30",
        tags=["foia"],
    )
    config = {
        "defaults": {"allowed_extensions": [".pdf", ".wav"], "ignore_extensions": []}
    }
    adapter = DojFoiaAdapter(source, config)

    class DummyResp:
        text = fixture
        status_code = 200

        def raise_for_status(self):
            return None

    class HeadResp:
        status_code = 200
        headers = {"Content-Type": "application/pdf"}

    class DummySession:
        def get(self, *args, **kwargs):
            return DummyResp()

        def head(self, url, **kwargs):
            return HeadResp()

    files = adapter.discover(DummySession())
    assert len(files) == 3
    urls = {file.url for file in files}
    assert any(url.endswith("/multimedia/foia/release-1") for url in urls)
    assert any(url.endswith("/multimedia/foia/audio-1") for url in urls)
    assert any(url.endswith("/multimedia/foia/opaque") for url in urls)
