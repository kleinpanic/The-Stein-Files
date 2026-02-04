from scripts.ingest import SkipReason, SourceConfig, skip_reason_for_source


def test_skip_reason_without_cookie():
    source = SourceConfig(
        id="doj-epstein-hub",
        name="DOJ Epstein Library — Hub",
        base_url="https://www.justice.gov/epstein",
        discovery={"type": "doj_hub"},
        is_official=True,
        notes="",
        constraints="",
        release_date="",
        tags=[],
        requires_cookies=True,
        referer="https://www.justice.gov/epstein",
    )
    reason = skip_reason_for_source(source, None)
    assert isinstance(reason, SkipReason)
    assert reason.reason == "cookie_required"


def test_skip_reason_with_cookie():
    source = SourceConfig(
        id="doj-epstein-hub",
        name="DOJ Epstein Library — Hub",
        base_url="https://www.justice.gov/epstein",
        discovery={"type": "doj_hub"},
        is_official=True,
        notes="",
        constraints="",
        release_date="",
        tags=[],
        requires_cookies=True,
        referer="https://www.justice.gov/epstein",
    )
    reason = skip_reason_for_source(source, object())
    assert reason is None
