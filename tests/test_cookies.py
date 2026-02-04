from pathlib import Path

import json

from scripts.cookies import load_cookie_jar_from_path, write_netscape_cookiejar


def test_cookiejar_writer_filters_and_formats(tmp_path: Path) -> None:
    cookies = [
        {
            "domain": ".justice.gov",
            "path": "/",
            "secure": True,
            "expires": 2000000000,
            "name": "session",
            "value": "abc123",
        },
        {
            "domain": ".example.com",
            "path": "/",
            "secure": False,
            "expires": 2000000000,
            "name": "other",
            "value": "nope",
        },
    ]
    output = tmp_path / "cookies.txt"
    count = write_netscape_cookiejar(cookies, output, "justice.gov")
    content = output.read_text(encoding="utf-8")

    assert count == 1
    assert content.startswith("# Netscape HTTP Cookie File")
    assert "justice.gov" in content
    assert "example.com" not in content


def test_cookiejar_writer_creates_parent_dir(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "cookies.txt"
    count = write_netscape_cookiejar(
        [
            {
                "domain": ".justice.gov",
                "path": "/",
                "secure": False,
                "expires": 2000000000,
                "name": "session",
                "value": "abc123",
            }
        ],
        output,
        "justice.gov",
    )
    assert count == 1
    assert output.exists()


def test_load_cookie_jar_from_json(tmp_path: Path) -> None:
    cookies = [
        {
            "domain": ".justice.gov",
            "path": "/",
            "secure": True,
            "expires": 2000000000,
            "name": "session",
            "value": "abc123",
        }
    ]
    path = tmp_path / "cookies.json"
    path.write_text(json.dumps(cookies), encoding="utf-8")
    jar = load_cookie_jar_from_path(path, "justice.gov")
    assert jar is not None
    assert any(cookie.domain.endswith("justice.gov") for cookie in jar)


def test_load_cookie_jar_from_netscape(tmp_path: Path) -> None:
    output = tmp_path / "cookies.txt"
    write_netscape_cookiejar(
        [
            {
                "domain": ".justice.gov",
                "path": "/",
                "secure": False,
                "expires": 2000000000,
                "name": "session",
                "value": "abc123",
            }
        ],
        output,
        "justice.gov",
    )
    jar = load_cookie_jar_from_path(output, "justice.gov")
    assert jar is not None
    assert any(cookie.domain.endswith("justice.gov") for cookie in jar)
