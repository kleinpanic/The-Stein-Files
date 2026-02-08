#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
import re
import shutil
import tempfile
import time
from http.cookiejar import CookieJar
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
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
from scripts.cookies import ensure_doj_age_verified_cookie, load_cookie_jar_from_path
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
    etag: str
    last_modified: str


@dataclass
class SkipReason:
    reason: str
    detail: str


@dataclass
class RequestContext:
    timeout: int
    retry_max: int
    backoff_base: float
    limiter: RateLimiter


def load_config() -> Dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def is_ci() -> bool:
    return os.getenv("CI", "").lower() in {"1", "true", "yes"}


class RateLimiter:
    def __init__(self, requests_per_second: float) -> None:
        self.interval = 1.0 / requests_per_second if requests_per_second > 0 else 0.0
        self._last = 0.0

    def wait(self) -> None:
        if self.interval <= 0:
            return
        now = time.monotonic()
        elapsed = now - self._last
        sleep_for = self.interval - elapsed
        if sleep_for > 0:
            time.sleep(sleep_for)
        self._last = time.monotonic()


def parse_retry_after(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_backoff(base: float, attempt: int, retry_after: Optional[float]) -> float:
    backoff = base * (2 ** attempt)
    jitter = random.uniform(0, base)
    wait = backoff + jitter
    if retry_after is not None:
        wait = max(wait, retry_after)
    return wait


def request_with_retry(
    session: requests.Session,
    method: str,
    url: str,
    *,
    timeout: int,
    headers: Optional[Dict[str, str]] = None,
    retry_max: int,
    backoff_base: float,
    limiter: RateLimiter,
    stream: bool = False,
) -> requests.Response:
    retryable = {429, 500, 502, 503, 504}
    for attempt in range(retry_max + 1):
        limiter.wait()
        try:
            resp = session.request(
                method,
                url,
                timeout=timeout,
                headers=headers,
                allow_redirects=True,
                stream=stream,
            )
        except requests.RequestException as exc:
            if attempt >= retry_max:
                raise exc
            wait = compute_backoff(backoff_base, attempt, None)
            print(f"[ingest] retry exception={exc} url={url} wait={wait:.2f}s")
            time.sleep(wait)
            continue

        if resp.status_code in retryable and attempt < retry_max:
            retry_after = parse_retry_after(resp.headers.get("Retry-After", ""))
            wait = compute_backoff(backoff_base, attempt, retry_after)
            print(
                f"[ingest] retry status={resp.status_code} url={url} wait={wait:.2f}s"
            )
            resp.close()
            time.sleep(wait)
            continue

        return resp
    raise RuntimeError("request_with_retry failed unexpectedly")


def build_session(config: Dict[str, Any]) -> requests.Session:
    defaults = config.get("defaults", {})
    max_concurrency_env = os.getenv("EPPIE_MAX_CONCURRENCY")
    max_concurrency = int(max_concurrency_env) if max_concurrency_env else int(defaults.get("max_concurrency", 2))
    retry = Retry(total=0, raise_on_status=False)
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=max_concurrency,
        pool_maxsize=max_concurrency,
    )
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

    path: Optional[Path] = None
    if jar_path:
        path = Path(jar_path)
    else:
        default = default_cookie_path()
        if default.exists():
            path = default
        else:
            json_path = default.with_suffix(".json")
            if json_path.exists():
                path = json_path

    if path is None:
        # CI-friendly default: DOJ endpoints are age-gated, and we can satisfy the
        # gate with a minimal cookie. If a real cookie jar is required, callers can
        # still provide EPPIE_COOKIE_JAR.
        jar = CookieJar()
        ensure_doj_age_verified_cookie(jar)
        print("[ingest] using built-in DOJ age-verification cookie (no cookie jar file found)")
        return jar

    try:
        jar = load_cookie_jar_from_path(path, "justice.gov")
    except Exception as exc:
        print(f"[ingest] failed to load cookie jar: {exc}")
        return None
    if jar is None:
        print(f"[ingest] cookie jar not found at {path}")
        return None

    ensure_doj_age_verified_cookie(jar)
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
    session: requests.Session,
    url: str,
    timeout: int,
    headers: Optional[Dict[str, str]] = None,
    *,
    retry_max: int,
    backoff_base: float,
    limiter: RateLimiter,
) -> Optional[int]:
    try:
        resp = request_with_retry(
            session,
            "HEAD",
            url,
            timeout=timeout,
            headers=headers,
            retry_max=retry_max,
            backoff_base=backoff_base,
            limiter=limiter,
        )
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
    *,
    retry_max: int,
    backoff_base: float,
    limiter: RateLimiter,
) -> DownloadResult:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    with request_with_retry(
        session,
        "GET",
        url,
        timeout=timeout,
        headers=headers,
        retry_max=retry_max,
        backoff_base=backoff_base,
        limiter=limiter,
        stream=True,
    ) as resp:
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        content_disposition = resp.headers.get("Content-Disposition", "")
        etag = resp.headers.get("ETag", "")
        last_modified = resp.headers.get("Last-Modified", "")
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
        etag=etag,
        last_modified=last_modified,
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


def status_code_from_http_error(exc: requests.HTTPError) -> int:
    resp = exc.response
    if resp is None:
        return 0
    return resp.status_code


def response_is_not_found(resp: requests.Response) -> bool:
    if resp.status_code == 404:
        return True
    content_type = resp.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type:
        return False
    text = resp.text.lower()
    return "page not found" in text or "404" in text[:2000]


def conditional_head(
    session: requests.Session,
    url: str,
    timeout: int,
    headers: Dict[str, str],
    *,
    etag: str = "",
    last_modified: str = "",
    retry_max: int,
    backoff_base: float,
    limiter: RateLimiter,
) -> Optional[requests.Response]:
    conditional_headers = dict(headers)
    if etag:
        conditional_headers["If-None-Match"] = etag
    if last_modified:
        conditional_headers["If-Modified-Since"] = last_modified
    if not etag and not last_modified:
        return None
    try:
        return request_with_retry(
            session,
            "HEAD",
            url,
            timeout=timeout,
            headers=conditional_headers,
            retry_max=retry_max,
            backoff_base=backoff_base,
            limiter=limiter,
        )
    except requests.RequestException:
        return None


def resolve_hub_targets(
    session: requests.Session,
    hub_url: str,
    timeout: int,
    headers: Optional[Dict[str, str]] = None,
    requester: Optional[RequestContext] = None,
) -> Dict[str, str]:
    if requester:
        resp = request_with_retry(
            session,
            "GET",
            hub_url,
            timeout=requester.timeout,
            headers=headers,
            retry_max=requester.retry_max,
            backoff_base=requester.backoff_base,
            limiter=requester.limiter,
        )
    else:
        resp = session.get(hub_url, timeout=timeout, headers=headers)
    resp.raise_for_status()
    return discover_doj_hub_targets(resp.text, hub_url)


def resolve_source_base_url(
    session: requests.Session,
    source: SourceConfig,
    timeout: int,
    hub_cache: Dict[str, Dict[str, str]],
    requester: Optional[RequestContext] = None,
) -> str:
    hub_target = source.discovery.get("hub_target")
    hub_url = source.discovery.get("hub_url")
    if not hub_target or not hub_url:
        return source.base_url
    targets = hub_cache.get(hub_url)
    if targets is None:
        try:
            targets = resolve_hub_targets(
                session,
                hub_url,
                timeout,
                headers=source_headers(source),
                requester=requester,
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
        if requester:
            resp = request_with_retry(
                session,
                "GET",
                source.base_url,
                timeout=min(timeout, 20),
                headers=source_headers(source),
                retry_max=requester.retry_max,
                backoff_base=requester.backoff_base,
                limiter=requester.limiter,
            )
        else:
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
    def __init__(
        self,
        source: SourceConfig,
        config: Dict[str, Any],
        requester: Optional[RequestContext] = None,
    ) -> None:
        self.source = source
        self.config = config
        self.requester = requester

    def discover(self, session: requests.Session) -> List[DiscoveredFile]:
        raise NotImplementedError

    def _allowed(self, url: str) -> bool:
        defaults = self.config.get("defaults", {})
        allowed = defaults.get("allowed_extensions", [])
        ignored = defaults.get("ignore_extensions", [])
        return allowed_extension(url, allowed, ignored)

    def _is_relevant_file_link(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        return "/multimedia/" in path or "/epstein/" in path

    def _anchor_has_allowed_extension(self, text: str) -> bool:
        defaults = self.config.get("defaults", {})
        allowed = defaults.get("allowed_extensions", [])
        text_lower = text.strip().lower()
        return any(text_lower.endswith(ext) for ext in allowed)

    def _content_type_allowed(self, content_type: str) -> bool:
        content_type = (content_type or "").lower()
        allowed_types = {
            "application/pdf",
            "application/rtf",
            "text/plain",
            "text/csv",
            "audio/wav",
            "audio/x-wav",
            "video/mp4",
        }
        return any(token in content_type for token in allowed_types)

    def _multimedia_allowed_by_head(
        self,
        session: requests.Session,
        url: str,
        headers: Optional[Dict[str, str]],
    ) -> bool:
        try:
            if self.requester:
                resp = request_with_retry(
                    session,
                    "HEAD",
                    url,
                    timeout=self.requester.timeout,
                    headers=headers,
                    retry_max=self.requester.retry_max,
                    backoff_base=self.requester.backoff_base,
                    limiter=self.requester.limiter,
                )
            else:
                resp = session.head(url, timeout=120, headers=headers, allow_redirects=True)
        except requests.RequestException:
            return False
        return self._content_type_allowed(resp.headers.get("Content-Type", ""))

    def _should_include_link(
        self,
        session: requests.Session,
        url: str,
        link_text: str,
        headers: Optional[Dict[str, str]],
    ) -> bool:
        if not self._is_relevant_file_link(url):
            return False
        if self._allowed(url):
            return True
        if "/multimedia/" in urlparse(url).path.lower():
            if self._anchor_has_allowed_extension(link_text):
                return True
            return self._multimedia_allowed_by_head(session, url, headers)
        return False

    def fetch(
        self,
        session: requests.Session,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        if not self.requester:
            return session.get(url, timeout=120, headers=headers)
        return request_with_retry(
            session,
            "GET",
            url,
            timeout=self.requester.timeout,
            headers=headers,
            retry_max=self.requester.retry_max,
            backoff_base=self.requester.backoff_base,
            limiter=self.requester.limiter,
        )


class DojHubAdapter(SourceAdapter):
    def discover(self, session: requests.Session) -> List[DiscoveredFile]:
        resp = self.fetch(session, self.source.base_url, headers=source_headers(self.source))
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
        resp = self.fetch(session, self.source.base_url, headers=source_headers(self.source))
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
                resp = self.fetch(session, next_url, headers=source_headers(self.source))
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
        resp = self.fetch(session, self.source.base_url, headers=headers)
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

        files = self._parse_court_links(session, links, self.source.base_url)
        for page in subpages:
            if page == self.source.base_url:
                continue
            sub_resp = self.fetch(session, page, headers=source_headers(self.source))
            sub_resp.raise_for_status()
            sub_links = collect_links(sub_resp.text)
            files.extend(self._parse_court_links(session, sub_links, page))

        return files

    def _parse_court_links(
        self, session: requests.Session, links: List[Dict[str, str]], page_url: str
    ) -> List[DiscoveredFile]:
        discovered: List[DiscoveredFile] = []
        headers = source_headers(self.source)
        for link in links:
            url = normalize_url(page_url, link["href"])
            link_text = link.get("text", "")
            if not self._should_include_link(session, url, link_text, headers):
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
        resp = self.fetch(session, self.source.base_url, headers=headers)
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
            link_text = link.get("text", "")
            if not self._should_include_link(session, url, link_text, headers):
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
        resp = self.fetch(session, self.source.base_url, headers=source_headers(self.source))
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


class DirectListAdapter(SourceAdapter):
    """Adapter for sources with a pre-defined list of file URLs."""
    def discover(self, session: requests.Session) -> List[DiscoveredFile]:
        files_config = self.source.discovery.get("files", [])
        files: List[DiscoveredFile] = []
        for file_info in files_config:
            url = file_info.get("url")
            if not url:
                continue
            files.append(
                DiscoveredFile(
                    url=url,
                    title=file_info.get("title", file_info.get("filename", Path(urlparse(url).path).name)),
                    source_page=self.source.base_url,
                    release_date=self.source.release_date,
                    tags=self.source.tags,
                )
            )
        return files


def adapter_for(
    source: SourceConfig,
    config: Dict[str, Any],
    requester: Optional[RequestContext] = None,
) -> SourceAdapter:
    kind = source.discovery.get("type")
    if kind == "doj_hub":
        return DojHubAdapter(source, config, requester)
    if kind == "doj_disclosures":
        return DojDisclosuresAdapter(source, config, requester)
    if kind == "doj_court_records":
        return DojCourtRecordsAdapter(source, config, requester)
    if kind == "doj_foia":
        return DojFoiaAdapter(source, config, requester)
    if kind == "opa_press_release":
        return OpaPressReleaseAdapter(source, config, requester)
    if kind == "direct_list":
        return DirectListAdapter(source, config, requester)
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


def select_throttle(config: Dict[str, Any]) -> Dict[str, float]:
    defaults = config.get("defaults", {})
    rps_env = os.getenv("EPPIE_REQUESTS_PER_SECOND")
    retry_env = os.getenv("EPPIE_RETRY_MAX")
    backoff_env = os.getenv("EPPIE_BACKOFF_BASE_SECONDS")
    time_budget_env = os.getenv("EPPIE_TIME_BUDGET_SECONDS")
    return {
        "requests_per_second": float(rps_env) if rps_env else float(defaults.get("requests_per_second", 1.5)),
        "retry_max": int(retry_env) if retry_env else int(defaults.get("retry_max", 5)),
        "backoff_base": float(backoff_env) if backoff_env else float(defaults.get("backoff_base_seconds", 1.0)),
        "time_budget": float(time_budget_env) if time_budget_env else 0.0,
    }


def ingest() -> None:
    config = load_config()
    limits = select_limits(config)
    throttle = select_throttle(config)
    timeout = int(config.get("defaults", {}).get("timeout_seconds", 120))
    session = build_session(config)
    limiter = RateLimiter(throttle["requests_per_second"])
    retry_max = int(throttle["retry_max"])
    backoff_base = float(throttle["backoff_base"])
    time_budget = float(throttle["time_budget"])
    started_at = time.monotonic()
    request_context = RequestContext(
        timeout=timeout,
        retry_max=retry_max,
        backoff_base=backoff_base,
        limiter=limiter,
    )
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
    by_url: Dict[str, Dict[str, Any]] = {}
    for entry in catalog:
        if entry.get("source_url"):
            by_url[entry["source_url"]] = entry
        for source in entry.get("sources", []):
            url = source.get("source_url")
            if url:
                by_url[url] = entry
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
        if time_budget and (time.monotonic() - started_at) >= time_budget:
            print("[ingest] time budget reached; stopping run")
            break
        resolved_url = resolve_source_base_url(
            session, source, timeout, hub_cache, requester=request_context
        )
        if resolved_url != source.base_url:
            source.base_url = resolved_url
        adapter = adapter_for(source, config, requester=request_context)
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
        source_state = state.get(source.id, {})
        cursor = int(source_state.get("cursor", 0))
        seen_urls = set(source_state.get("seen_urls", []))
        failed_urls = dict(source_state.get("failed_urls", {}))
        if cursor >= len(discovered):
            cursor = 0
        print(f"[ingest] {source.id}: discovered {len(discovered)} files")

        for idx, item in enumerate(discovered[cursor:], start=cursor):
            if time_budget and (time.monotonic() - started_at) >= time_budget:
                print("[ingest] time budget reached; stopping run")
                break
            if max_attempts and attempted >= max_attempts:
                break
            if max_docs and downloaded >= max_docs:
                break
            if max_bytes and total_bytes >= max_bytes:
                break
            if run_bytes_limit and run_bytes_used >= run_bytes_limit:
                break
            if item.url in seen_urls:
                continue
            attempted += 1
            state[source.id] = {"cursor": idx + 1}
            state_changed = True

            headers = source_headers(source)
            existing_by_url = by_url.get(item.url)
            if existing_by_url:
                conditional = conditional_head(
                    session,
                    item.url,
                    timeout,
                    headers,
                    etag=existing_by_url.get("etag", ""),
                    last_modified=existing_by_url.get("last_modified", ""),
                    retry_max=retry_max,
                    backoff_base=backoff_base,
                    limiter=limiter,
                )
                if conditional is not None and conditional.status_code == 304:
                    seen_urls.add(item.url)
                    state[source.id] = {
                        "cursor": idx + 1,
                        "seen_urls": sorted(seen_urls),
                        "failed_urls": failed_urls,
                        "last_run": utc_now_iso(),
                    }
                    state_changed = True
                    continue

            est_size = estimate_size(
                session,
                item.url,
                timeout,
                headers=headers,
                retry_max=retry_max,
                backoff_base=backoff_base,
                limiter=limiter,
            )
            if max_bytes and est_size and total_bytes + est_size > max_bytes:
                print(f"[ingest] skip (size cap) {item.url}")
                continue
            if run_bytes_limit and est_size and run_bytes_used + est_size > run_bytes_limit:
                print(f"[ingest] skip (run size cap) {item.url}")
                continue

            filename = Path(urlparse(item.url).path).name or f"document-{downloaded}.bin"
            with tempfile.TemporaryDirectory(prefix="epstein-ingest-") as tmpdir:
                tmp_path = Path(tmpdir) / filename
                try:
                    result = download_file(
                        session,
                        item.url,
                        tmp_path,
                        timeout,
                        headers=headers,
                        retry_max=retry_max,
                        backoff_base=backoff_base,
                        limiter=limiter,
                    )
                except requests.HTTPError as exc:
                    status = status_code_from_http_error(exc)
                    if status in {403, 404}:
                        print(f"[ingest] skip status={status} url={item.url}")
                        failed_urls[item.url] = {"status": status, "at": utc_now_iso()}
                        state[source.id] = {
                            "cursor": idx + 1,
                            "seen_urls": sorted(seen_urls),
                            "failed_urls": failed_urls,
                            "last_run": utc_now_iso(),
                        }
                        state_changed = True
                        continue
                    raise
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
                    source_page = item.source_page or source.base_url
                    if source_page and existing.get("source_page") != source_page:
                        existing["source_page"] = source_page
                        changed = True

                    if result.content_type and not existing.get("mime_type"):
                        existing["mime_type"] = result.content_type
                        changed = True
                    if result.final_url and existing.get("source_url") != result.final_url:
                        existing["source_url"] = result.final_url
                        changed = True
                    if result.content_disposition:
                        existing["content_disposition"] = result.content_disposition
                        changed = True
                    if result.etag:
                        existing["etag"] = result.etag
                        changed = True
                    if result.last_modified:
                        existing["last_modified"] = result.last_modified
                        changed = True
                    if result.final_url:
                        by_url[result.final_url] = existing

                    if changed:
                        existing["downloaded_at"] = utc_now_iso()
                        write_json(Path("data/meta") / f"{existing['id']}.json", existing)
                        updated = True

                    total_bytes += result.size
                    run_bytes_used += result.size
                    downloaded += 1
                    seen_urls.add(item.url)
                    state[source.id] = {
                        "cursor": idx + 1,
                        "seen_urls": sorted(seen_urls),
                        "failed_urls": failed_urls,
                        "last_run": utc_now_iso(),
                    }
                    state_changed = True
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
                    "source_page": item.source_page or source.base_url,
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
                    "etag": result.etag,
                    "last_modified": result.last_modified,
                    "content_disposition": result.content_disposition,
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
                by_url[entry["source_url"]] = entry
                updated = True
                new_docs += 1
                total_bytes += result.size
                run_bytes_used += result.size
                downloaded += 1
                seen_urls.add(item.url)
                state[source.id] = {
                    "cursor": idx + 1,
                    "seen_urls": sorted(seen_urls),
                    "failed_urls": failed_urls,
                    "last_run": utc_now_iso(),
                }
                state_changed = True

        print(
            f"[ingest] {source.id}: downloaded {downloaded} files, new {new_docs}, "
            f"bytes {total_bytes}, attempts {attempted}, non-file {skipped_nonfile}"
        )
        current_cursor = state.get(source.id, {}).get("cursor", cursor)
        state[source.id] = {
            "cursor": current_cursor,
            "seen_urls": sorted(seen_urls),
            "failed_urls": failed_urls,
            "last_run": utc_now_iso(),
        }
        state_changed = True

    if updated:
        catalog = sorted(catalog, key=lambda e: e.get("release_date") or "")
        save_catalog(catalog)
    if state_changed:
        save_state(state)


if __name__ == "__main__":
    ingest()

