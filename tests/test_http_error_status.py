from requests import HTTPError
from requests.models import Response

from scripts.ingest import status_code_from_http_error


def test_status_code_from_http_error_handles_falsey_response():
    resp = Response()
    resp.status_code = 404
    # Note: requests.Response is falsey when not ok (>=400).
    assert bool(resp) is False

    exc = HTTPError("not found", response=resp)
    assert status_code_from_http_error(exc) == 404
