#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
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

CONFIG_PATH = Path("config/sources.json")


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


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[Dict[str, str]] = []
        self._current_link: Optional[Dict[str, str]] = None
        self._heading_text: List[str] = []
        self._active_heading = ""
        self._heading_tag: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5"}:
            self._heading_tag = tag
            self._heading_text = []
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href")
            if href:
                self._current_link = {"href": href, "text": "", "heading": self._active_heading}

    def handle_data(self, data: str) -> None:
        if self._heading_tag:
            self._heading_text.append(data.strip())
        if self._current_link is not None:
            self._current_link["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == self._heading_tag:
            heading = " ".join(part for part in self._heading_text if part)
            if heading:
                self._active_heading = heading
            self._heading_tag = None
            self._heading_text = []
        if tag == "a" and self._current_link is not None:
            text = self._current_link["text"].strip()
            self.links.append(
                {
                    "href": self._current_link["href"],
                    "text": text,
                    "heading": self._current_link["heading"],
                }
            )
            self._current_link = None


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
    session.headers.update({"User-Agent": defaults.get("user_agent", "EppieIngest/1.1.0")})
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def collect_links(html: str) -> List[Dict[str, str]]:
    parser = LinkCollector()
    parser.feed(html)
    return parser.links


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


def estimate_size(session: requests.Session, url: str, timeout: int) -> Optional[int]:
    try:
        resp = session.head(url, timeout=timeout, allow_redirects=True)
        if resp.ok and resp.headers.get("Content-Length"):
            return int(resp.headers["Content-Length"])
    except Exception:
        return None
    return None


def download_file(session: requests.Session, url: str, dest: Path, timeout: int) -> DownloadResult:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    with session.get(url, stream=True, timeout=timeout) as resp:
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


class DojDisclosuresAdapter(SourceAdapter):
    def discover(self, session: requests.Session) -> List[DiscoveredFile]:
        timeout = int(self.config.get("defaults", {}).get("timeout_seconds", 120))
        resp = session.get(self.source.base_url, timeout=timeout)
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
                resp = session.get(next_url, timeout=timeout)
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
        resp = session.get(self.source.base_url, timeout=timeout)
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
            sub_resp = session.get(page, timeout=timeout)
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
        resp = session.get(self.source.base_url, timeout=timeout)
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
        resp = session.get(self.source.base_url, timeout=timeout)
        resp.raise_for_status()
        links = collect_links(resp.text)
        files: List[DiscoveredFile] = []
        for link in links:
            url = normalize_url(self.source.base_url, link["href"])
            if not self._allowed(url) and "dl?inline=" not in url:
                continue
            if "media" not in url:
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


def adapter_for(source: SourceConfig, config: Dict[str, Any]) -> SourceAdapter:
    kind = source.discovery.get("type")
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
            )
        )
    return sources


def select_limits(config: Dict[str, Any]) -> Dict[str, int]:
    limits = config.get("limits", {})
    env_key = "ci" if is_ci() else "local"
    env_limits = limits.get(env_key, {})
    return {
        "max_docs": int(env_limits.get("max_docs_per_source", 0)),
        "max_bytes": int(env_limits.get("max_bytes_per_source", 0)),
    }


def ingest() -> None:
    config = load_config()
    limits = select_limits(config)
    timeout = int(config.get("defaults", {}).get("timeout_seconds", 120))
    session = build_session(config)
    sources = build_sources(config)

    catalog = load_catalog()
    by_sha = {entry["sha256"]: entry for entry in catalog}
    updated = False

    for source in sources:
        adapter = adapter_for(source, config)
        try:
            discovered = adapter.discover(session)
        except requests.RequestException as exc:
            print(f"[ingest] {source.id}: discovery failed ({exc})")
            continue
        discovered = sorted({d.url: d for d in discovered}.values(), key=lambda d: d.url)
        max_docs = limits.get("max_docs", 0)
        max_bytes = limits.get("max_bytes", 0)
        total_bytes = 0
        downloaded = 0
        new_docs = 0
        print(f"[ingest] {source.id}: discovered {len(discovered)} files")

        for item in discovered:
            if max_docs and downloaded >= max_docs:
                break
            if max_bytes and total_bytes >= max_bytes:
                break

            est_size = estimate_size(session, item.url, timeout)
            if max_bytes and est_size and total_bytes + est_size > max_bytes:
                print(f"[ingest] skip (size cap) {item.url}")
                continue

            filename = Path(urlparse(item.url).path).name or f"document-{downloaded}.bin"
            with tempfile.TemporaryDirectory(prefix="epstein-ingest-") as tmpdir:
                tmp_path = Path(tmpdir) / filename
                result = download_file(session, item.url, tmp_path, timeout)
                if is_html_file(tmp_path, result.content_type):
                    print(f"[ingest] skip non-file response: {item.url}")
                    continue

                sha = sha256_file(tmp_path)
                existing = by_sha.get(sha)
                if existing:
                    ensure_sources(existing, source.name, item.source_page or source.base_url)
                    existing["downloaded_at"] = utc_now_iso()
                    existing["source_url"] = result.final_url or item.url
                    if item.tags:
                        existing["tags"] = sorted(set(existing.get("tags", [])) | set(item.tags))
                    write_json(Path("data/meta") / f"{existing['id']}.json", existing)
                    updated = True
                    total_bytes += result.size
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
                downloaded += 1

        print(
            f"[ingest] {source.id}: downloaded {downloaded} files, new {new_docs}, bytes {total_bytes}"
        )

    if updated:
        catalog = sorted(catalog, key=lambda e: e.get("release_date") or "")
        save_catalog(catalog)


if __name__ == "__main__":
    ingest()
