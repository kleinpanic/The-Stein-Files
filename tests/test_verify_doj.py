from pathlib import Path

from scripts.verify_doj import detect_blocked


def test_blocked_403_with_page_not_found_text():
    body = Path("tests/fixtures/blocked_403.html").read_text(encoding="utf-8")
    assert detect_blocked(403, body) is True


def test_not_found_404_is_not_blocked():
    body = Path("tests/fixtures/not_found_404.html").read_text(encoding="utf-8")
    assert detect_blocked(404, body) is False
