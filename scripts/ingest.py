#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from http.cookiejar import CookieJar
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from pypdf import PdfReader
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scripts.common import (
    RAW_DIR,
    detect_mime,
    ensure_sources,
    load_catalog,
    save_catalog,
    sha256_file,
    slugify,
    utc_now_iso,
    write_json,
)
from scripts.cookies import load_cookie_jar_from_path
from scripts.doj_hub import collect_links, discover_doj_hub_targets

CONFIG_PATH = Path("config/sources.json")
STATE_PATH = Path("data/meta/ingest_state.json")


@dataclass
class SourceConfig:
    id: str
    name: str
    base_url: str
    discovery: Dict[str, Any]
    is_official: bool
    notes: str
    constraints: str
    release_date: str
    tags: List[str] = field(default_factory=list)
    requires_cookies: bool = False
    referer: str = ""


@dataclass
class DiscoveredFile:
    url: str
    title: str
    source_page: str
    release_date: str
    tags: List[str]
    notes: Optional[str] = None


@dataclass
class DownloadResult:
    size: int
    content_type: str
    content_disposition: str
    final_url: str


@dataclass
class SkipReason:
    reason: str
    detail: str


def load_config() -> Dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def is_ci() -> bool:
    return os.getenv("CI", "").lower() in {"1", "true", "yes"}


def build_session(config: Dict[str, Any]) -> requests.Session:
    defaults = config.get("defaults", {})
    retries = int(defaults.get("retries", 3))
    backoff = float(defaults.get("backoff_factor", 0.6))
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": defaults.get("user_agent", "EppieIngest/1.1.0"),
            "Accept": "text/html,application/xhtml+xml,application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def default_cookie_path() -> Path:
    return Path(".secrets") / "justice.gov.cookies.txt"


def load_cookie_jar() -> Optional[CookieJar]:
    jar_path = os.getenv("EPPIE_COOKIE_JAR", "").strip()
    if jar_path:
        path = Path(jar_path)
    else:
        path = default_cookie_path()
        if not path.exists():
            json_path = path.with_suffix(".json")
            if json_path.exists():
                path = json_path
            else:
                return None
    try:
        jar = load_cookie_jar_from_path(path, "justice.gov")
    except Exception as exc:
        print(f"[ingest] failed to load cookie jar: {exc}")
        return None
    if jar is None:
        print(f"[ingest] cookie jar not found at {path}")
        return None
    return jar


def source_headers(source: SourceConfig) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if source.referer:
        headers["Referer"] = source.referer
    return headers


def playwright_discovery_enabled() -> bool:
    return os.getenv("EPPIE_PLAYWRIGHT_DISCOVERY", "").lower() in {"1", "true", "yes"}


def storage_state_path() -> Path:
    return Path(".secrets") / "doj.storage-state.json"


def discover_with_playwright(
    urls: List[str],
    allowed_exts: List[str],
) -> List[str]:
    if not playwright_discovery_enabled():
        return []
    state_path = storage_state_path()
    if not state_path.exists():
        print("[ingest] skip playwright discovery (missing storage state)")
        return []
    node = shutil.which("node")
    if not node:
        print("[ingest] skip playwright discovery (node missing)")
        return []
    script = Path("scripts/playwright_discover.mjs")
    if not script.exists():
        print("[ingest] skip playwright discovery (script missing)")
        return []
    try:
        result = subprocess.run(
            [
                node,
                str(script),
                "--urls",
                ",".join(urls),
                "--storage",
                str(state_path),
                "--allow",
                ",".join(allowed_exts),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout.strip() or "[]")
    except Exception as exc:
        print(f"[ingest] playwright discovery failed: {exc}")
        return []


def normalize_url(base_url: str, href: str) -> str:
    full = urljoin(base_url, href)
    parsed = urlparse(full)
    return parsed._replace(fragment="").geturl()


def allowed_extension(url: str, allowed: Iterable[str], ignored: Iterable[str]) -> bool:
    path = urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext in ignored:
        return False
    if not allowed:
        return True
    return ext in allowed


def estimate_size(
    session: requests.Session, url: str, timeout: int, headers: Optional[Dict[str, str]] = None
) -> Optional[int]:
    try:
        resp = session.head(url, timeout=timeout, allow_redirects=True, headers=headers)
        if resp.ok and resp.headers.get("Content-Length"):
            return int(resp.headers["Content-Length"])
    except Exception:
        return None
    return None


def download_file(
    session: requests.Session,
    url: str,
    dest: Path,
    timeout: int,
    headers: Optional[Dict[str, str]] = None,
) -> DownloadResult:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    with session.get(url, stream=True, timeout=timeout, headers=headers) as resp:
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        content_disposition = resp.headers.get("Content-Disposition", "")
        with dest.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    size += len(chunk)
                    f.write(chunk)
    return DownloadResult(
        size=size,
        content_type=content_type,
        content_disposition=content_disposition,
        final_url=resp.url,
    )


def count_pdf_pages(path: Path) -> int | None:
    try:
        reader = PdfReader(str(path))
        return len(reader.pages)
    except Exception:
        return None


def extract_year(text: str) -> str:
    match = re.search(r"(19|20)\d{2}", text)
    if match:
        return match.group(0)
    return ""


def filename_from_disposition(disposition: str) -> str:
    if not disposition:
        return ""
    match = re.search(r'filename="?([^";]+)"?', disposition)
    if match:
        return match.group(1)
    return ""


def extension_from_content_type(content_type: str) -> str:
    content_type = content_type.lower()
    if "pdf" in content_type:
        return ".pdf"
    if "rtf" in content_type:
        return ".rtf"
    if "text/plain" in content_type:
        return ".txt"
    if "csv" in content_type:
        return ".csv"
    if "audio/wav" in content_type or "audio/x-wav" in content_type:
        return ".wav"
    if "video/mp4" in content_type:
        return ".mp4"
    return ""


def is_html_file(path: Path, content_type: str) -> bool:
    if "text/html" in (content_type or "").lower():
        return True
    try:
        head = path.read_bytes()[:200].lstrip()
    except Exception:
        return False
    return head.startswith(b"<!DOCTYPE html") or head.startswith(b"<html")


def is_blocked_response(result: DownloadResult, path: Path) -> Optional[SkipReason]:
    content_type = (result.content_type or "").lower()
    if "text/html" in content_type:
        return SkipReason(reason="html_response", detail=content_type)
    if result.size < 4096 and is_html_file(path, content_type):
        return SkipReason(reason="html_body", detail="small_html_body")
    return None


def response_is_not_found(resp: requests.Response) -> bool:
    if resp.status_code == 404:
        return True
    content_type = resp.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type:
        return False
    text = resp.text.lower()
    return "page not found" in text or "404" in text[:2000]


def resolve_hub_targets(
    session: requests.Session,
    hub_url: str,
    timeout: int,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    resp = session.get(hub_url, timeout=timeout, headers=headers)
    resp.raise_for_status()
    return discover_doj_hub_targets(resp.text, hub_url)


def resolve_source_base_url(
    session: requests.Session,
    source: SourceConfig,
    timeout: int,
    hub_cache: Dict[str, Dict[str, str]],
) -> str:
    hub_target = source.discovery.get("hub_target")
    hub_url = source.discovery.get("hub_url")
    if not hub_target or not hub_url:
        return source.base_url
    targets = hub_cache.get(hub_url)
    if targets is None:
        try:
            targets = resolve_hub_targets(
                session, hub_url, timeout, headers=source_headers(source)
            )
        except requests.RequestException as exc:
            print(f"[ingest] hub discovery failed: {hub_url} ({exc})")
            targets = {}
        hub_cache[hub_url] = targets
    discovered = targets.get(hub_target)
    if not discovered:
        return source.base_url
    if discovered == source.base_url:
        return source.base_url
    try:
        resp = session.get(
            source.base_url,
            timeout=min(timeout, 20),
            headers=source_headers(source),
            allow_redirects=True,
        )
        if response_is_not_found(resp):
            print(
                f"[ingest] {source.id}: configured URL not found; using hub {discovered}"
            )
        else:
            print(f"[ingest] {source.id}: using hub-discovered URL {discovered}")
    except requests.RequestException:
        print(f"[ingest] {source.id}: using hub-discovered URL {discovered}")
    return discovered


def skip_reason_for_source(source: SourceConfig, cookie_jar: Optional[CookieJar]) -> Optional[SkipReason]:
    if source.requires_cookies and not cookie_jar:
        return SkipReason(reason="cookie_required", detail="cookie jar missing")
    return None


class SourceAdapter:
    def __init__(self, source: SourceConfig, config: Dict[str, Any]) -> None:
        self.source = source
        self.config = config

    def discover(self, session: requests.Session) -> List[DiscoveredFile]:
        raise NotImplementedError

    def _allowed(self, url: str) -> bool:
        defaults = self.config.get("defaults", {})
        allowed = defaults.get("allowed_extensions", [])
        ignored = defaults.get("ignore_extensions", [])
        return allowed_extension(url, allowed, ignored)


class DojHubAdapter(SourceAdapter):
    def discover(self, session: requests.Session) -> List[DiscoveredFile]:
        timeout = int(self.config.get("defaults", {}).get("timeout_seconds", 120))
        resp = session.get(
            self.source.base_url, timeout=timeout, headers=source_headers(self.source)
        )
        resp.raise_for_status()
        links = collect_links(resp.text)
        files: List[DiscoveredFile] = []
        for link in links:
            url = normalize_url(self.source.base_url, link["href"])
            if not self._allowed(url):
                continue
            title_text = link["text"].strip() or Path(urlparse(url).path).name
            files.append(
                DiscoveredFile(
                    url=url,
                    title=title_text,
                    source_page=self.source.base_url,
                    release_date=self.source.release_date,
                    tags=self.source.tags,
                )
            )
        return files


class DojDisclosuresAdapter(SourceAdapter):
    def discover(self, session: requests.Session) -> List[DiscoveredFile]:
        timeout = int(self.config.get("defaults", {}).get("timeout_seconds", 120))
        resp = session.get(
            self.source.base_url, timeout=timeout, headers=source_headers(self.source)
        )
        resp.raise_for_status()
        links = collect_links(resp.text)
        dataset_pages = [
            normalize_url(self.source.base_url, link["href"])
            for link in links
            if "/epstein/doj-disclosures/data-set-" in link["href"]
        ]
        dataset_pages = sorted(set(dataset_pages))

        files: List[DiscoveredFile] = []
        for link in links:
            url = normalize_url(self.source.base_url, link["href"])
            if self._allowed(url):
                title = link["text"].strip() or Path(urlparse(url).path).name
                files.append(
                    DiscoveredFile(
                        url=url,
                        title=title,
                        source_page=self.source.base_url,
                        release_date=self.source.release_date,
                        tags=self.source.tags,
                    )
                )

        for page_url in dataset_pages:
            files.extend(self._discover_dataset_pages(session, page_url, timeout))

        return files

    def _discover_dataset_pages(
        self, session: requests.Session, page_url: str, timeout: int
    ) -> List[DiscoveredFile]:
        discovered: List[DiscoveredFile] = []
        visited = set()
        next_url = page_url
        while next_url and next_url not in visited:
            visited.add(next_url)
            try:
                resp = session.get(
                    next_url, timeout=timeout, headers=source_headers(self.source)
                )
                resp.raise_for_status()
            except requests.RequestException as exc:
                print(f"[ingest] dataset page fetch failed: {next_url} ({exc})")
                break
            links = collect_links(resp.text)
            page_title = next(
                (link["heading"] for link in links if link["heading"]), ""
            )
            for link in links:
                url = normalize_url(next_url, link["href"])
                if not self._allowed(url):
                    continue
                title_text = link["text"].strip() or Path(urlparse(url).path).name
                if page_title:
                    title = f"{page_title} — {title_text}"
                else:
                    title = title_text
                discovered.append(
                    DiscoveredFile(
                        url=url,
                        title=title,
                        source_page=page_url,
                        release_date=self.source.release_date,
                        tags=self.source.tags,
                    )
                )
            next_url = self._find_next_page(links, next_url)
        return discovered

    def _find_next_page(self, links: List[Dict[str, str]], base_url: str) -> str:
        for link in links:
            text = link["text"].strip().lower()
            href = link["href"]
            if text in {"next", "›", ">"}:
                return normalize_url(base_url, href)
            if "page=" in href and "/data-set-" in href:
                return normalize_url(base_url, href)
        return ""


class DojCourtRecordsAdapter(SourceAdapter):
    def discover(self, session: requests.Session) -> List[DiscoveredFile]:
        timeout = int(self.config.get("defaults", {}).get("timeout_seconds", 120))
        headers = source_headers(self.source)
        resp = session.get(self.source.base_url, timeout=timeout, headers=headers)
        if resp.status_code == 403 and playwright_discovery_enabled():
            urls = discover_with_playwright(
                [self.source.base_url],
                self.config.get("defaults", {}).get("allowed_extensions", []),
            )
            return [
                DiscoveredFile(
                    url=url,
                    title=Path(urlparse(url).path).name,
                    source_page=self.source.base_url,
                    release_date=self.source.release_date,
                    tags=self.source.tags,
                )
                for url in urls
            ]
        resp.raise_for_status()
        links = collect_links(resp.text)

        subpages = [
            normalize_url(self.source.base_url, link["href"])
            for link in links
            if "See files at" in link["text"] or "/epstein/court-records/" in link["href"]
        ]
        subpages = sorted(set(subpages))

        files = self._parse_court_links(links, self.source.base_url)
        for page in subpages:
            if page == self.source.base_url:
                continue
            sub_resp = session.get(
                page, timeout=timeout, headers=source_headers(self.source)
            )
            sub_resp.raise_for_status()
            sub_links = collect_links(sub_resp.text)
            files.extend(self._parse_court_links(sub_links, page))

        return files

    def _parse_court_links(
        self, links: List[Dict[str, str]], page_url: str
    ) -> List[DiscoveredFile]:
        discovered: List[DiscoveredFile] = []
        for link in links:
            url = normalize_url(page_url, link["href"])
            if not self._allowed(url):
                continue
            heading = link["heading"] or "Court Records"
            title_text = link["text"].strip() or Path(urlparse(url).path).name
            title = f"{heading} — {title_text}" if heading else title_text
            year = extract_year(heading)
            release_date = f"{year}-01-01" if year else self.source.release_date
            discovered.append(
                DiscoveredFile(
                    url=url,
                    title=title,
                    source_page=page_url,
                    release_date=release_date,
                    tags=self.source.tags,
                )
            )
        return discovered


class DojFoiaAdapter(SourceAdapter):
    def discover(self, session: requests.Session) -> List[DiscoveredFile]:
        timeout = int(self.config.get("defaults", {}).get("timeout_seconds", 120))
        headers = source_headers(self.source)
        resp = session.get(self.source.base_url, timeout=timeout, headers=headers)
        if resp.status_code == 403 and playwright_discovery_enabled():
            urls = discover_with_playwright(
                [self.source.base_url],
                self.config.get("defaults", {}).get("allowed_extensions", []),
            )
            return [
                DiscoveredFile(
                    url=url,
                    title=Path(urlparse(url).path).name,
                    source_page=self.source.base_url,
                    release_date=self.source.release_date,
                    tags=self.source.tags,
                )
                for url in urls
            ]
        resp.raise_for_status()
        links = collect_links(resp.text)
        files: List[DiscoveredFile] = []
        for link in links:
            url = normalize_url(self.source.base_url, link["href"])
            if not self._allowed(url):
                continue
            heading = link["heading"] or "FOIA"
            title_text = link["text"].strip() or Path(urlparse(url).path).name
            title = f"{heading} — {title_text}"
            files.append(
                DiscoveredFile(
                    url=url,
                    title=title,
                    source_page=self.source.base_url,
                    release_date=self.source.release_date,
                    tags=self.source.tags,
                )
            )
        return files


class OpaPressReleaseAdapter(SourceAdapter):
    def discover(self, session: requests.Session) -> List[DiscoveredFile]:
        timeout = int(self.config.get("defaults", {}).get("timeout_seconds", 120))
        resp = session.get(
            self.source.base_url, timeout=timeout, headers=source_headers(self.source)
        )
        resp.raise_for_status()
        links = collect_links(resp.text)
        files: List[DiscoveredFile] = []
        for link in links:
            url = normalize_url(self.source.base_url, link["href"])
            if not self._allowed(url) and "dl?inline" not in url:
                continue
            if "/ag/media/" not in url:
                continue
            title_text = link["text"].strip() or Path(urlparse(url).path).name
            if title_text.lower() == "here":
                title_text = "Attorney General Letter (Feb 27, 2025)"
            files.append(
                DiscoveredFile(
                    url=url,
                    title=title_text,
                    source_page=self.source.base_url,
                    release_date=self.source.release_date,
                    tags=self.source.tags,
                )
            )
        return files


def adapter_for(source: SourceConfig, config: Dict[str, Any]) -> SourceAdapter:
    kind = source.discovery.get("type")
    if kind == "doj_hub":
        return DojHubAdapter(source, config)
    if kind == "doj_disclosures":
        return DojDisclosuresAdapter(source, config)
    if kind == "doj_court_records":
        return DojCourtRecordsAdapter(source, config)
    if kind == "doj_foia":
        return DojFoiaAdapter(source, config)
    if kind == "opa_press_release":
        return OpaPressReleaseAdapter(source, config)
    raise ValueError(f"Unknown discovery type: {kind}")


def build_sources(config: Dict[str, Any]) -> List[SourceConfig]:
    sources = []
    for item in config.get("sources", []):
        sources.append(
            SourceConfig(
                id=item["id"],
                name=item["name"],
                base_url=item["base_url"],
                discovery=item.get("discovery", {}),
                is_official=bool(item.get("is_official", True)),
                notes=item.get("notes", ""),
                constraints=item.get("constraints", ""),
                release_date=item.get("release_date", ""),
                tags=item.get("tags", []),
                requires_cookies=bool(item.get("requires_cookies", False)),
                referer=item.get("referer", ""),
            )
        )
    return sources


def load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: Dict[str, Any]) -> None:
    write_json(STATE_PATH, state)


def select_limits(config: Dict[str, Any]) -> Dict[str, int]:
    limits = config.get("limits", {})
    env_key = "ci" if is_ci() else "local"
    env_limits = limits.get(env_key, {})
    env_max_docs = os.getenv("EPPIE_MAX_DOWNLOADS_PER_SOURCE")
    env_max_bytes = os.getenv("EPPIE_MAX_BYTES_PER_RUN")
    return {
        "max_docs": int(env_max_docs) if env_max_docs else int(env_limits.get("max_docs_per_source", 0)),
        "max_bytes": int(env_limits.get("max_bytes_per_source", 0)),
        "max_bytes_run": int(env_max_bytes) if env_max_bytes else 0,
        "max_attempts": int(env_limits.get("max_attempts_per_source", 0)),
    }


def ingest() -> None:
    config = load_config()
    limits = select_limits(config)
    timeout = int(config.get("defaults", {}).get("timeout_seconds", 120))
    session = build_session(config)
    cookie_jar = load_cookie_jar()
    if cookie_jar:
        session.cookies = cookie_jar
    sources = build_sources(config)
    state = load_state()
    state_changed = False
    run_bytes_limit = limits.get("max_bytes_run", 0)
    run_bytes_used = 0
    hub_cache: Dict[str, Dict[str, str]] = {}

    catalog = load_catalog()
    by_sha = {entry["sha256"]: entry for entry in catalog}
    updated = False

    for source in sources:
        if run_bytes_limit and run_bytes_used >= run_bytes_limit:
            break
        skip_reason = skip_reason_for_source(source, cookie_jar)
        if skip_reason:
            print(
                "[ingest] skip gated source "
                f"reason={skip_reason.reason} url={source.base_url}"
            )
            continue
        resolved_url = resolve_source_base_url(session, source, timeout, hub_cache)
        if resolved_url != source.base_url:
            source.base_url = resolved_url
        adapter = adapter_for(source, config)
        try:
            discovered = adapter.discover(session)
        except requests.RequestException as exc:
            print(f"[ingest] {source.id}: discovery failed ({exc})")
            continue
        discovered = sorted({d.url: d for d in discovered}.values(), key=lambda d: d.url)
        max_docs = limits.get("max_docs", 0)
        max_bytes = limits.get("max_bytes", 0)
        max_attempts = limits.get("max_attempts", 0)
        total_bytes = 0
        downloaded = 0
        new_docs = 0
        attempted = 0
        skipped_nonfile = 0
        cursor = int(state.get(source.id, {}).get("cursor", 0))
        if cursor >= len(discovered):
            cursor = 0
        print(f"[ingest] {source.id}: discovered {len(discovered)} files")

        for idx, item in enumerate(discovered[cursor:], start=cursor):
            if max_attempts and attempted >= max_attempts:
                break
            if max_docs and downloaded >= max_docs:
                break
            if max_bytes and total_bytes >= max_bytes:
                break
            if run_bytes_limit and run_bytes_used >= run_bytes_limit:
                break
            attempted += 1
            state[source.id] = {"cursor": idx + 1}
            state_changed = True

            headers = source_headers(source)
            est_size = estimate_size(session, item.url, timeout, headers=headers)
            if max_bytes and est_size and total_bytes + est_size > max_bytes:
                print(f"[ingest] skip (size cap) {item.url}")
                continue
            if run_bytes_limit and est_size and run_bytes_used + est_size > run_bytes_limit:
                print(f"[ingest] skip (run size cap) {item.url}")
                continue

            filename = Path(urlparse(item.url).path).name or f"document-{downloaded}.bin"
            with tempfile.TemporaryDirectory(prefix="epstein-ingest-") as tmpdir:
                tmp_path = Path(tmpdir) / filename
                result = download_file(session, item.url, tmp_path, timeout, headers=headers)
                blocked = is_blocked_response(result, tmp_path)
                if blocked:
                    skipped_nonfile += 1
                    if skipped_nonfile <= 5:
                        print(
                            "[ingest] skip gated response "
                            f"url={item.url} reason={blocked.reason} detail={blocked.detail}"
                        )
                    continue

                sha = sha256_file(tmp_path)
                existing = by_sha.get(sha)
                if existing:
                    changed = False
                    sources_before = len(existing.get("sources", []))
                    ensure_sources(existing, source.name, item.source_page or source.base_url)
                    if len(existing.get("sources", [])) != sources_before:
                        changed = True

                    new_source_url = result.final_url or item.url
                    if existing.get("source_url") != new_source_url:
                        existing["source_url"] = new_source_url
                        changed = True

                    if existing.get("title", "").lower() in {"here", ""} and item.title:
                        existing["title"] = item.title
                        changed = True

                    if not existing.get("release_date") and item.release_date:
                        existing["release_date"] = item.release_date
                        changed = True

                    if item.tags:
                        new_tags = sorted(set(existing.get("tags", [])) | set(item.tags))
                        if new_tags != existing.get("tags", []):
                            existing["tags"] = new_tags
                            changed = True

                    if changed:
                        existing["downloaded_at"] = utc_now_iso()
                        write_json(Path("data/meta") / f"{existing['id']}.json", existing)
                        updated = True

                    total_bytes += result.size
                    run_bytes_used += result.size
                    downloaded += 1
                    continue

                doc_id = f"{sha[:12]}-{slugify(item.title)}"
                raw_dir = RAW_DIR / doc_id
                raw_dir.mkdir(parents=True, exist_ok=True)
                header_name = filename_from_disposition(result.content_disposition)
                final_name = header_name or filename
                if final_name in {"dl", "download"} or "." not in final_name:
                    ext = extension_from_content_type(result.content_type)
                    final_name = f"{slugify(item.title)}{ext}" if ext else final_name
                dest_path = raw_dir / final_name
                shutil.move(str(tmp_path), dest_path)

                mime_type = detect_mime(dest_path)
                pages = count_pdf_pages(dest_path) if dest_path.suffix.lower() == ".pdf" else None

                entry = {
                    "id": doc_id,
                    "title": item.title,
                    "source_name": source.name,
                    "source_url": result.final_url or item.url,
                    "release_date": item.release_date or "",
                    "downloaded_at": utc_now_iso(),
                    "sha256": sha,
                    "file_path": str(dest_path),
                    "mime_type": mime_type,
                    "pages": pages,
                    "tags": item.tags,
                    "notes": item.notes or source.notes,
                    "is_official": bool(source.is_official),
                    "license_or_terms": "as published by source",
                    "sources": [
                        {
                            "source_name": source.name,
                            "source_url": item.source_page or source.base_url,
                        }
                    ],
                }

                write_json(Path("data/meta") / f"{doc_id}.json", entry)
                catalog.append(entry)
                by_sha[sha] = entry
                updated = True
                new_docs += 1
                total_bytes += result.size
                run_bytes_used += result.size
                downloaded += 1

        print(
            f"[ingest] {source.id}: downloaded {downloaded} files, new {new_docs}, "
            f"bytes {total_bytes}, attempts {attempted}, non-file {skipped_nonfile}"
        )

    if updated:
        catalog = sorted(catalog, key=lambda e: e.get("release_date") or "")
        save_catalog(catalog)
    if state_changed:
        save_state(state)


if __name__ == "__main__":
    ingest()
