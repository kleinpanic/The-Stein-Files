from pathlib import Path

from scripts.doj_hub import collect_links
from scripts.ingest import DojCourtRecordsAdapter, DojHubAdapter, SourceConfig


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

    files = adapter._parse_court_links(links, source.base_url)
    assert len(files) == 2
    assert files[0].title.startswith("United States v. Maxwell")
    assert files[0].release_date == "2021-01-01"
    assert files[0].url.endswith("indictment.pdf")


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

        def raise_for_status(self):
            return None

    class DummySession:
        def get(self, *args, **kwargs):
            return DummyResp()

    files = adapter.discover(DummySession())
    assert len(files) == 2
    assert files[0].url.endswith("summary.pdf")
