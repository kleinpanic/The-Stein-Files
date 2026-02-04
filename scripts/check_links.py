#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests

from scripts.doj_hub import discover_doj_hub_targets

CONFIG_PATH = Path("config/sources.json")


def load_config(path: Path = CONFIG_PATH) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_session(config: Dict[str, Any]) -> requests.Session:
    defaults = config.get("defaults", {})
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": defaults.get("user_agent", "EppieLinkCheck/1.0"),
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def is_page_not_found(resp: requests.Response) -> bool:
    if resp.status_code == 404:
        return True
    content_type = resp.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type:
        return False
    text = resp.text.lower()
    return "page not found" in text or "404" in text[:2000]


def fetch_with_fallback(
    session: requests.Session, url: str, timeout: int
) -> requests.Response:
    try:
        resp = session.head(url, allow_redirects=True, timeout=timeout)
        if resp.status_code in {405, 501}:
            raise requests.RequestException("HEAD not allowed")
        return resp
    except requests.RequestException:
        return session.get(url, allow_redirects=True, timeout=timeout)


def discover_hub_links(
    session: requests.Session, hub_url: str, timeout: int
) -> Set[str]:
    resp = session.get(hub_url, allow_redirects=True, timeout=timeout)
    resp.raise_for_status()
    targets = discover_doj_hub_targets(resp.text, hub_url)
    return set(targets.values())


def check_links(
    config: Dict[str, Any],
    session: Optional[requests.Session] = None,
    hub_links: Optional[Set[str]] = None,
) -> List[str]:
    errors: List[str] = []
    session = session or build_session(config)
    timeout = int(config.get("defaults", {}).get("timeout_seconds", 20))
    if hub_links is None:
        try:
            hub_links = discover_hub_links(session, "https://www.justice.gov/epstein", timeout)
        except requests.RequestException as exc:
            hub_links = set()
            errors.append(f"hub fetch failed: {exc}")

    for source in config.get("sources", []):
        url = source.get("base_url", "")
        if not url:
            continue
        allow_403 = bool(source.get("link_check", {}).get("allow_403"))
        try:
            resp = fetch_with_fallback(session, url, timeout)
        except requests.RequestException as exc:
            errors.append(f"{source.get('id','unknown')}: request failed {url} ({exc})")
            continue

        if is_page_not_found(resp):
            errors.append(f"{source.get('id','unknown')}: 404 not found {url}")
            continue

        if resp.status_code == 403 and allow_403:
            if url in hub_links:
                continue
            errors.append(f"{source.get('id','unknown')}: 403 but not present on hub {url}")
            continue

        if resp.status_code >= 400:
            errors.append(
                f"{source.get('id','unknown')}: status {resp.status_code} {url}"
            )

    return errors


def main() -> int:
    config = load_config()
    session = build_session(config)
    errors = check_links(config, session=session)
    if errors:
        for err in errors:
            print(f"[check-links] {err}")
        return 1
    print("[check-links] all source links OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
