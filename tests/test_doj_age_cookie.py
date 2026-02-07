import json
from http.cookiejar import CookieJar

from scripts.cookies import ensure_doj_age_verified_cookie
from scripts.ingest import load_cookie_jar as ingest_load_cookie_jar


def test_ensure_doj_age_verified_cookie_adds_cookie():
    jar = CookieJar()
    ensure_doj_age_verified_cookie(jar)
    assert any(
        cookie.name == "justiceGovAgeVerified"
        and cookie.value == "true"
        and cookie.domain == ".justice.gov"
        for cookie in jar
    )


def test_ingest_load_cookie_jar_injects_age_cookie(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".secrets").mkdir(parents=True, exist_ok=True)

    # Minimal cookie jar (ingest falls back to .json when .txt is missing).
    (tmp_path / ".secrets/justice.gov.cookies.json").write_text(
        json.dumps([]), encoding="utf-8"
    )

    jar = ingest_load_cookie_jar()
    assert jar is not None
    assert any(cookie.name == "justiceGovAgeVerified" for cookie in jar)


def test_ingest_load_cookie_jar_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jar = ingest_load_cookie_jar()
    assert jar is not None
    assert any(cookie.name == "justiceGovAgeVerified" for cookie in jar)
