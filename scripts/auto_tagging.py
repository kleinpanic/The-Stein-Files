#!/usr/bin/env python3
"""
Auto-tagging system for Eppie documents.

Phase 2: Multi-dimensional tagging:
- Keyword-based tags (scan content for specific terms)
- Person-name tags (from enhanced_metadata)
- Location tags (from enhanced_metadata)
- Date-range tags (1990s, 2000s, 2010s, extracted from dates)
- Document-source tags (FBI, court, deposition, etc.)
- Content-type tags (flight-log, testimony, photo, correspondence)

All tags are case-insensitive and normalized.
"""
from __future__ import annotations

import re
from typing import List, Set
from datetime import datetime


# Keyword categories for auto-tagging
KEYWORD_TAGS = {
    "flight": ["flight", "plane", "aircraft", "pilot", "passenger", "trip", "travel log", "manifest"],
    "victim": ["victim", "minor", "underage", "trafficking", "abuse", "assault", "exploitation"],
    "witness": ["witness", "testimony", "deposition", "statement", "testified", "sworn"],
    "evidence": ["evidence", "exhibit", "photograph", "photo", "image", "documentation"],
    "location": ["island", "residence", "property", "address", "estate", "mansion"],
    "financial": ["payment", "wire transfer", "account", "transaction", "money", "compensation"],
    "legal": ["subpoena", "court order", "warrant", "affidavit", "filing", "motion", "brief"],
    "communication": ["email", "letter", "message", "phone call", "correspondence", "memo"],
    "investigation": ["FBI", "investigation", "agent", "detective", "search", "seizure", "raid"],
}


# Document source patterns
SOURCE_PATTERNS = {
    "fbi": [
        r'\bFBI\b',
        r'\bFederal Bureau of Investigation\b',
        r'\b\d{1,3}[A-Z]{1,3}-[A-Z]{2,5}-\d{5,7}\b',  # FBI file format
    ],
    "court": [
        r'\bUnited States District Court\b',
        r'\bU\.S\. District Court\b',
        r'\bCase No\.',
        r'\bDocket No\.',
        r'\b\d{1,2}:\d{2}-(?:cv|cr)-\d{4,5}\b',  # federal case format
    ],
    "deposition": [
        r'\bDEPOSITION\b',
        r'\bQ:\s+',  # Question format
        r'\bA:\s+',  # Answer format
        r'\btestimony of\b',
    ],
    "subpoena": [
        r'\bSUBPOENA\b',
        r'\bsubpoena duces tecum\b',
        r'\bYou are hereby commanded\b',
    ],
    "evidence-photo": [
        r'\bEFTA\d{8,}\b',
        r'\bevidence photo\b',
        r'\bphoto exhibit\b',
    ],
    "flight-log": [
        r'\bflight log\b',
        r'\bpassenger manifest\b',
        r'\baircraft\b.*\blog\b',
        r'\bN\d{3}[A-Z]{1,2}\b',  # aircraft registration (e.g., N908JE)
    ],
}


def extract_keyword_tags(text: str) -> Set[str]:
    """
    Extract keyword-based tags by scanning content.
    
    Returns:
        Set of tag strings (normalized, lowercase)
    """
    tags = set()
    text_lower = text.lower()
    
    for tag_name, keywords in KEYWORD_TAGS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                tags.add(tag_name)
                break  # one match per category is enough
    
    return tags


def extract_source_tags(text: str, category: str = None) -> Set[str]:
    """
    Extract document source tags (FBI, court, deposition, etc.)
    
    Args:
        text: Document content
        category: Optional pre-classified category from Phase 1
    
    Returns:
        Set of source tag strings
    """
    tags = set()
    
    # If we already have a category from Phase 1, use it
    if category:
        category_lower = category.lower()
        if "fbi" in category_lower:
            tags.add("fbi")
        if "court" in category_lower:
            tags.add("court")
        if "deposition" in category_lower:
            tags.add("deposition")
        if "evidence" in category_lower or "photo" in category_lower:
            tags.add("evidence-photo")
        if "flight" in category_lower:
            tags.add("flight-log")
    
    # Pattern matching for source detection
    for source, patterns in SOURCE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                tags.add(source)
                break
    
    return tags


def extract_date_range_tags(text: str, release_date: str = None) -> Set[str]:
    """
    Extract decade tags based on dates mentioned in content or release date.
    
    Args:
        text: Document content
        release_date: Document release date (ISO format YYYY-MM-DD)
    
    Returns:
        Set of decade tags (e.g., "1990s", "2000s")
    """
    tags = set()
    
    # Extract years from text (4-digit numbers that look like years)
    year_pattern = r'\b(19\d{2}|20\d{2})\b'
    years = [int(y) for y in re.findall(year_pattern, text)]
    
    # Add release date year if available
    if release_date:
        try:
            release_year = int(release_date[:4])
            years.append(release_year)
        except (ValueError, IndexError):
            pass
    
    # Convert years to decade tags
    for year in years:
        if 1990 <= year < 2000:
            tags.add("1990s")
        elif 2000 <= year < 2010:
            tags.add("2000s")
        elif 2010 <= year < 2020:
            tags.add("2010s")
        elif 2020 <= year < 2030:
            tags.add("2020s")
    
    return tags


def extract_person_tags(person_names: List[str]) -> Set[str]:
    """
    Convert person names to normalized tags.
    
    Args:
        person_names: List of person names from enhanced_metadata
    
    Returns:
        Set of person tags (normalized: lowercase, hyphens)
    """
    tags = set()
    
    for name in person_names:
        # Normalize: lowercase, replace spaces with hyphens
        tag = name.lower().replace(" ", "-")
        # Remove special characters
        tag = re.sub(r'[^a-z0-9-]', '', tag)
        if tag:
            tags.add(f"person:{tag}")
    
    return tags


def extract_location_tags(locations: List[str]) -> Set[str]:
    """
    Convert locations to normalized tags.
    
    Args:
        locations: List of locations from enhanced_metadata
    
    Returns:
        Set of location tags (normalized: lowercase, hyphens)
    """
    tags = set()
    
    for location in locations:
        # Normalize: lowercase, replace spaces/commas with hyphens
        tag = location.lower().replace(" ", "-").replace(",", "")
        # Remove special characters
        tag = re.sub(r'[^a-z0-9-]', '', tag)
        if tag:
            tags.add(f"location:{tag}")
    
    return tags


def generate_auto_tags(
    text: str,
    category: str = None,
    person_names: List[str] = None,
    locations: List[str] = None,
    release_date: str = None,
) -> List[str]:
    """
    Generate comprehensive auto-tags for a document.
    
    Args:
        text: Full document text content
        category: Pre-classified category from Phase 1
        person_names: Person names from enhanced_metadata
        locations: Locations from enhanced_metadata
        release_date: Release date (YYYY-MM-DD format)
    
    Returns:
        Sorted list of unique tags
    """
    all_tags = set()
    
    # Keyword tags
    all_tags.update(extract_keyword_tags(text))
    
    # Source tags
    all_tags.update(extract_source_tags(text, category))
    
    # Date range tags
    all_tags.update(extract_date_range_tags(text, release_date))
    
    # Person tags
    if person_names:
        all_tags.update(extract_person_tags(person_names))
    
    # Location tags
    if locations:
        all_tags.update(extract_location_tags(locations))
    
    return sorted(all_tags)


def tag_summary(tags: List[str]) -> dict:
    """
    Organize tags into categories for display.
    
    Returns:
        {
            "keywords": [...],
            "sources": [...],
            "people": [...],
            "locations": [...],
            "decades": [...],
        }
    """
    summary = {
        "keywords": [],
        "sources": [],
        "people": [],
        "locations": [],
        "decades": [],
    }
    
    for tag in tags:
        if tag.startswith("person:"):
            summary["people"].append(tag[7:])  # strip "person:" prefix
        elif tag.startswith("location:"):
            summary["locations"].append(tag[9:])  # strip "location:" prefix
        elif tag.endswith("s") and tag[:-1].isdigit():  # decade tags like "1990s"
            summary["decades"].append(tag)
        elif tag in ["fbi", "court", "deposition", "subpoena", "evidence-photo", "flight-log"]:
            summary["sources"].append(tag)
        else:
            summary["keywords"].append(tag)
    
    return summary
