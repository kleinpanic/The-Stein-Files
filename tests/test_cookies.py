from pathlib import Path

from scripts.cookies import write_netscape_cookiejar


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
