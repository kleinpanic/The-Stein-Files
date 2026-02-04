from scripts.ingest import SourceConfig, resolve_source_base_url


class DummyResponse:
    def __init__(self, status_code: int, body: str = "", content_type: str = "text/html"):
        self.status_code = status_code
        self.text = body
        self.headers = {"Content-Type": content_type}


class DummySession:
    def __init__(self, response):
        self._response = response

    def get(self, *args, **kwargs):
        return self._response


def test_resolve_source_base_url_falls_back_on_404():
    source = SourceConfig(
        id="doj-foia",
        name="DOJ Epstein Library — FOIA",
        base_url="https://www.justice.gov/epstein/foia",
        discovery={
            "type": "doj_foia",
            "hub_url": "https://www.justice.gov/epstein",
            "hub_target": "foia",
        },
        is_official=True,
        notes="",
        constraints="",
        release_date="",
        tags=[],
    )
    hub_cache = {
        "https://www.justice.gov/epstein": {"foia": "https://www.justice.gov/epstein/foia-records"}
    }
    session = DummySession(DummyResponse(404, "Page not found"))
    resolved = resolve_source_base_url(session, source, timeout=10, hub_cache=hub_cache)
    assert resolved == "https://www.justice.gov/epstein/foia-records"
