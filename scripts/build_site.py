#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import markdown

from scripts.common import current_git_sha, load_catalog, utc_now_iso

SITE_DIR = Path("site")
DIST_DIR = Path("dist")


def clean_dist() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def copy_assets() -> None:
    assets_dir = SITE_DIR / "assets"
    shutil.copytree(assets_dir, DIST_DIR / "assets")


def copy_data() -> None:
    mirror_mode = os.getenv("EPPIE_MIRROR_MODE", "").lower() in {"1", "true", "yes"}
    paths = [Path("data/derived"), Path("data/meta/catalog.json"), Path("data/meta/relationships.json")]
    if mirror_mode:
        paths.insert(0, Path("data/raw"))
    for path in paths:
        if path.is_dir():
            dest = DIST_DIR / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(path, dest)
        elif path.is_file():
            dest = DIST_DIR / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)


def render_template(
    content: str,
    title: str,
    build_info: str,
    asset_version: str,
    repo_slug: str,
) -> str:
    base = (SITE_DIR / "templates" / "base.html").read_text(encoding="utf-8")
    return (
        base.replace("{{title}}", title)
        .replace("{{content}}", content)
        .replace("{{build_info}}", build_info)
        .replace("{{asset_version}}", asset_version)
        .replace("{{repo_slug}}", repo_slug)
    )


def build_sources_page(build_info: str, asset_version: str, repo_slug: str) -> None:
    md = Path("docs/SOURCES.md").read_text(encoding="utf-8")
    html = markdown.markdown(md)
    content = f"<article class='prose'>{html}</article>"
    page = render_template(content, "Sources", build_info, asset_version, repo_slug)
    (DIST_DIR / "sources.html").write_text(page, encoding="utf-8")


def build_index_page(build_info: str, asset_version: str, repo_slug: str) -> None:
    content = (SITE_DIR / "templates" / "index.html").read_text(encoding="utf-8")
    page = render_template(content, "Epstein Files Library", build_info, asset_version, repo_slug)
    (DIST_DIR / "index.html").write_text(page, encoding="utf-8")


def build_viewer_page(build_info: str, asset_version: str, repo_slug: str) -> None:
    content = (SITE_DIR / "templates" / "viewer.html").read_text(encoding="utf-8")
    page = render_template(content, "Document Viewer", build_info, asset_version, repo_slug)
    (DIST_DIR / "viewer.html").write_text(page, encoding="utf-8")


def build_stats_page(build_info: str, asset_version: str, repo_slug: str) -> None:
    content = (SITE_DIR / "templates" / "stats.html").read_text(encoding="utf-8")
    page = render_template(content, "Collection Statistics", build_info, asset_version, repo_slug)
    (DIST_DIR / "stats.html").write_text(page, encoding="utf-8")


def build_emails_page(build_info: str, asset_version: str, repo_slug: str) -> None:
    content = (SITE_DIR / "templates" / "emails.html").read_text(encoding="utf-8")
    page = render_template(content, "Email Documents", build_info, asset_version, repo_slug)
    (DIST_DIR / "emails.html").write_text(page, encoding="utf-8")


def build_detail_pages(build_info: str, asset_version: str, repo_slug: str) -> None:
    catalog = load_catalog()
    detail_dir = DIST_DIR / "documents"
    detail_dir.mkdir(parents=True, exist_ok=True)

    template = (SITE_DIR / "templates" / "detail.html").read_text(encoding="utf-8")
    for entry in catalog:
        doc_html = template
        for key, value in entry.items():
            if isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    value = ", ".join(value)
                else:
                    value = json.dumps(value)
            doc_html = doc_html.replace(f"{{{{{key}}}}}", str(value))
        content = doc_html
        page = render_template(content, entry["title"], build_info, asset_version, repo_slug)
        (detail_dir / f"{entry['id']}.html").write_text(page, encoding="utf-8")


def build_people_hub_page(build_info: str, asset_version: str, repo_slug: str) -> None:
    """Build the people hub landing page."""
    content = (SITE_DIR / "templates" / "people.html").read_text(encoding="utf-8")
    page = render_template(content, "Major People", build_info, asset_version, repo_slug)
    (DIST_DIR / "people.html").write_text(page, encoding="utf-8")


def build_relationships_page(build_info: str, asset_version: str, repo_slug: str) -> None:
    """Build the relationship graph page."""
    content = (SITE_DIR / "templates" / "relationships.html").read_text(encoding="utf-8")
    page = render_template(content, "Relationship Graph", build_info, asset_version, repo_slug)
    (DIST_DIR / "relationships.html").write_text(page, encoding="utf-8")


def build_person_detail_pages(build_info: str, asset_version: str, repo_slug: str) -> None:
    """Build individual person detail pages."""
    people_data_path = Path("data/derived/people.json")
    if not people_data_path.exists():
        print("⚠️  Warning: people.json not found, skipping person pages")
        return
    
    with open(people_data_path) as f:
        people_data = json.load(f)
    
    people_dir = DIST_DIR / "people"
    people_dir.mkdir(parents=True, exist_ok=True)
    
    template = (SITE_DIR / "templates" / "person.html").read_text(encoding="utf-8")
    
    for person in people_data.get('people', []):
        content = template
        page = render_template(
            content, 
            f"{person['name']} - Person Profile", 
            build_info, 
            asset_version, 
            repo_slug
        )
        (people_dir / f"{person['slug']}.html").write_text(page, encoding="utf-8")
    
    print(f"✓ Built {len(people_data.get('people', []))} person detail pages")


def build() -> None:
    clean_dist()
    copy_assets()
    copy_data()
    build_time = utc_now_iso()
    sha = current_git_sha()
    catalog = load_catalog()
    build_info = f"Built {build_time} | Commit {sha} | Documents {len(catalog)}"
    asset_version = sha
    repo_slug = os.getenv("EPPIE_REPO_SLUG", "kleinpanic/The-Stein-Files")
    build_index_page(build_info, asset_version, repo_slug)
    build_emails_page(build_info, asset_version, repo_slug)
    build_people_hub_page(build_info, asset_version, repo_slug)
    build_relationships_page(build_info, asset_version, repo_slug)
    build_sources_page(build_info, asset_version, repo_slug)
    build_viewer_page(build_info, asset_version, repo_slug)
    build_stats_page(build_info, asset_version, repo_slug)
    build_detail_pages(build_info, asset_version, repo_slug)
    # build_person_detail_pages(build_info, asset_version, repo_slug)  # Disabled: using single expandable page instead


if __name__ == "__main__":
    build()
