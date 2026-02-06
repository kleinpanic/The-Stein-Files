import json
from pathlib import Path

from scripts.verify_doj import detect_blocked, load_cookie_jar


def test_blocked_403_with_page_not_found_text():
    body = Path("tests/fixtures/blocked_403.html").read_text(encoding="utf-8")
    assert detect_blocked(403, body) is True


def test_not_found_404_is_not_blocked():
    body = Path("tests/fixtures/not_found_404.html").read_text(encoding="utf-8")
    assert detect_blocked(404, body) is False


def test_load_cookie_jar_falls_back_to_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".secrets").mkdir(parents=True, exist_ok=True)

    cookies = [
        {
            "domain": ".justice.gov",
            "name": "test",
            "value": "1",
            "path": "/",
            "secure": True,
            "expires": 1893456000,
        }
    ]
    (tmp_path / ".secrets/justice.gov.cookies.json").write_text(
        json.dumps(cookies), encoding="utf-8"
    )

    jar = load_cookie_jar()
    assert jar is not None
