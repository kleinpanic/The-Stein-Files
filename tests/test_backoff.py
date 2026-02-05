from scripts.ingest import RateLimiter, request_with_retry


class FakeResponse:
    def __init__(self, status_code, headers=None):
        self.status_code = status_code
        self.headers = headers or {}

    def close(self):
        return None


class FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def request(self, method, url, **kwargs):
        self.calls += 1
        return self._responses.pop(0)


def test_retry_respects_retry_after(monkeypatch):
    sleeps = []

    def fake_sleep(value):
        sleeps.append(value)

    monkeypatch.setattr("time.sleep", fake_sleep)

    session = FakeSession(
        [
            FakeResponse(503, headers={"Retry-After": "2"}),
            FakeResponse(200),
        ]
    )
    limiter = RateLimiter(0)
    resp = request_with_retry(
        session,
        "GET",
        "https://example.test/file",
        timeout=5,
        headers=None,
        retry_max=2,
        backoff_base=1.0,
        limiter=limiter,
    )
    assert resp.status_code == 200
    assert session.calls == 2
    assert sleeps and sleeps[0] >= 2
