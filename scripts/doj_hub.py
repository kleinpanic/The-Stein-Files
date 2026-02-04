from __future__ import annotations

from html.parser import HTMLParser
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse


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


def collect_links(html: str) -> List[Dict[str, str]]:
    parser = LinkCollector()
    parser.feed(html)
    return parser.links


def normalize_url(base_url: str, href: str) -> str:
    full = urljoin(base_url, href)
    parsed = urlparse(full)
    return parsed._replace(fragment="").geturl()


def _score_link(text: str, href: str, target: str) -> int:
    text_l = text.lower()
    href_l = href.lower()
    target_l = target.lower()
    score = 0
    if target_l in text_l:
        score += 3
    if target_l.replace(" ", "-") in href_l:
        score += 4
    if target_l.replace(" ", "") in href_l:
        score += 2
    return score


def discover_doj_hub_targets(html: str, base_url: str) -> Dict[str, str]:
    targets = {
        "disclosures": ["doj disclosures", "disclosures"],
        "court_records": ["court records", "court record"],
        "foia": ["foia", "freedom of information"],
    }
    best: Dict[str, Dict[str, str | int]] = {}
    links = collect_links(html)
    for link in links:
        href = normalize_url(base_url, link["href"])
        text = link["text"].strip()
        heading = link.get("heading", "")
        combined_text = " ".join(part for part in [text, heading] if part)
        for key, phrases in targets.items():
            score = 0
            for phrase in phrases:
                score = max(score, _score_link(combined_text, href, phrase))
            if score <= 0:
                continue
            current = best.get(key)
            if not current or score > int(current["score"]):
                best[key] = {"url": href, "score": score, "text": combined_text}
    return {key: str(info["url"]) for key, info in best.items()}
