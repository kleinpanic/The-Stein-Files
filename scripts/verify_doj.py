#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse, urlunparse

import requests

from scripts.cookies import load_cookie_jar_from_path

CONFIG_PATH = Path("config/sources.json")
SOURCE_IDS = {
    "doj-epstein-hub",
    "doj-epstein-doj-disclosures",
    "doj-epstein-court-records",
    "doj-epstein-foia",
}


def normalize_doj_url(url: str) -> str:
    if not url:
        return url
    parsed = urlparse(url)
    if parsed.netloc == "justice.gov":
        parsed = parsed._replace(netloc="www.justice.gov")
    return urlunparse(parsed)


def load_config() -> Dict[str, object]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_urls(config: Dict[str, object]) -> List[str]:
    urls = []
    for source in config.get("sources", []):
        if source.get("id") in SOURCE_IDS:
            urls.append(normalize_doj_url(source.get("base_url", "")))
    return [url for url in urls if url]


def load_cookie_jar() -> requests.cookies.RequestsCookieJar | None:
    jar_path = os.getenv("EPPIE_COOKIE_JAR", "").strip()
    if not jar_path:
        default = Path(".secrets") / "justice.gov.cookies.txt"
        if default.exists():
            jar_path = str(default)
    if not jar_path:
        return None
    path = Path(jar_path)
    jar = load_cookie_jar_from_path(path, "justice.gov")
    if jar is None:
        return None
    return jar


def main() -> int:
    config = load_config()
    defaults = config.get("defaults", {})
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": defaults.get("user_agent", "EppieVerify/1.0"),
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.justice.gov/epstein",
        }
    )
    jar = load_cookie_jar()
    if jar:
        session.cookies = jar

    urls = load_urls(config)
    for url in urls:
        try:
            resp = session.get(url, timeout=30, allow_redirects=True)
            print(f"[verify-doj] {url} status={resp.status_code}")
        except requests.RequestException as exc:
            print(f"[verify-doj] {url} status=0 error={exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
