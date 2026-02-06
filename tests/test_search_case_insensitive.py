import re
from pathlib import Path


def test_search_terms_are_lowercased_for_case_insensitive_queries():
    app_js = Path("site/assets/app.js").read_text(encoding="utf-8")

    # We specifically want the lunr query terms to be normalized, not just snippet building.
    match = re.search(r"const terms = query[\s\S]*?\.map\(\(term\) => term\.toLowerCase\(\)\)", app_js)
    assert match, "Expected performSearch() to lowercase query terms before lunr query()"
