from pathlib import Path

from scripts.doj_hub import discover_doj_hub_targets


def test_discover_doj_hub_targets():
    fixture = Path("tests/fixtures/doj_hub_links.html").read_text(encoding="utf-8")
    targets = discover_doj_hub_targets(fixture, "https://www.justice.gov/epstein")
    assert targets["disclosures"].endswith("/epstein/doj-disclosures")
    assert targets["court_records"].endswith("/epstein/court-records")
    assert targets["foia"].endswith("/epstein/foia")
