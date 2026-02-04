from scripts.check_links import check_links


class FakeResponse:
    def __init__(self, status_code: int, body: str = "", content_type: str = "text/html"):
        self.status_code = status_code
        self.text = body
        self.headers = {"Content-Type": content_type}


class FakeSession:
    def __init__(self, responses: dict[str, FakeResponse]):
        self._responses = responses

    def head(self, url, **kwargs):
        return self._responses[url]

    def get(self, url, **kwargs):
        return self._responses[url]


def test_check_links_allows_403_when_on_hub():
    config = {
        "defaults": {"timeout_seconds": 5},
        "sources": [
            {
                "id": "doj-court",
                "base_url": "https://www.justice.gov/epstein/court-records",
                "link_check": {"allow_403": True},
            }
        ],
    }
    session = FakeSession(
        {
            "https://www.justice.gov/epstein/court-records": FakeResponse(403),
        }
    )
    errors = check_links(config, session=session, hub_links={"https://www.justice.gov/epstein/court-records"})
    assert errors == []


def test_check_links_403_without_hub_fails():
    config = {
        "defaults": {"timeout_seconds": 5},
        "sources": [
            {
                "id": "doj-foia",
                "base_url": "https://www.justice.gov/epstein/foia",
                "link_check": {"allow_403": True},
            }
        ],
    }
    session = FakeSession(
        {
            "https://www.justice.gov/epstein/foia": FakeResponse(403),
        }
    )
    errors = check_links(config, session=session, hub_links=set())
    assert errors and "403" in errors[0]


def test_check_links_404_fails():
    config = {
        "defaults": {"timeout_seconds": 5},
        "sources": [
            {
                "id": "bad-link",
                "base_url": "https://example.test/missing",
            }
        ],
    }
    session = FakeSession(
        {
            "https://example.test/missing": FakeResponse(404, "Page not found"),
        }
    )
    errors = check_links(config, session=session, hub_links=set())
    assert errors and "404" in errors[0]
