from pathlib import Path


def test_search_mode_fields_defined():
    app_js = Path("site/assets/app.js").read_text(encoding="utf-8")
    assert "const SEARCH_MODE_FIELDS" in app_js
    for mode in ["full", "title", "tags", "source", "file"]:
        assert f"{mode}:" in app_js
    for field in ["title", "content", "tags", "source_name", "file_name", "id"]:
        assert field in app_js
