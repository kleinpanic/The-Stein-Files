from scripts.common import detect_mime, slugify


def test_slugify():
    assert slugify("Evidence List (Redacted)") == "evidence-list-redacted"


def test_detect_mime_pdf():
    class DummyPath:
        name = "file.pdf"
        suffix = ".pdf"

    assert detect_mime(DummyPath()) == "application/pdf"
