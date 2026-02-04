from scripts.ingest import SourceConfig, build_session, source_headers


def test_source_headers_include_referer():
    source = SourceConfig(
        id="doj-epstein-court-records",
        name="DOJ Epstein Library — Court Records",
        base_url="https://www.justice.gov/epstein/court-records",
        discovery={"type": "doj_court_records"},
        is_official=True,
        notes="",
        constraints="",
        release_date="",
        tags=[],
        requires_cookies=True,
        referer="https://www.justice.gov/epstein",
    )
    headers = source_headers(source)
    assert headers["Referer"] == "https://www.justice.gov/epstein"


def test_session_has_browser_headers():
    session = build_session({"defaults": {"user_agent": "TestAgent/1.0"}})
    assert "Accept" in session.headers
    assert "Accept-Language" in session.headers
