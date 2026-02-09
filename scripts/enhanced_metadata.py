#!/usr/bin/env python3
"""
Enhanced metadata extraction for Eppie documents.

Phase 1 improvements:
- FBI file number formats
- Court case number formats
- Person name extraction (NER-style patterns)
- Location extraction (cities, addresses)
- Enhanced case number patterns for evidence photos
- Batch/exhibit number extraction
"""
from __future__ import annotations

import re
from typing import List, Set


# Enhanced file number patterns
FILE_NUMBER_PATTERNS = [
    # Existing EFTA numbers
    r'\bEFTA\d{8,}\b',
    
    # FBI file numbers
    r'\b\d{1,3}[A-Z]{1,3}-[A-Z]{2,5}-\d{5,7}\b',  # e.g., 91E-NYC-323571
    r'\bFBI\s*#?\s*\d{2,3}-\d{4,6}\b',  # e.g., FBI #12-34567
    r'\bFile\s*#?\s*\d{2,3}[A-Z]{1,2}-\d{4,7}\b',  # e.g., File #12A-45678
    
    # Court case numbers
    r'\b\d{1,2}:\d{2}-cv-\d{4,5}\b',  # e.g., 1:15-cv-07433 (federal civil)
    r'\b\d{1,2}:\d{2}-cr-\d{4,5}\b',  # e.g., 1:19-cr-00490 (federal criminal)
    r'\bCase\s*No\.?\s*\d{2,4}-\d{3,6}\b',  # e.g., Case No. 19-123456
    r'\bDocket\s*No\.?\s*\d{2,4}-\d{3,6}\b',  # e.g., Docket No. 08-12345
    
    # Evidence/Exhibit numbers
    r'\bExhibit\s*[A-Z]?-?\d{1,4}\b',  # e.g., Exhibit A-123
    r'\bEvidence\s*#?\s*\d{2,6}\b',  # e.g., Evidence #12345
    r'\bBatch\s*#?\s*\d{2,6}\b',  # e.g., Batch #5678
]


# Person name patterns (simplified NER-style)
# Common titles that precede names
PERSON_TITLES = [
    r'\b(?:Mr|Ms|Mrs|Miss|Dr|Prof|President|Judge|Attorney|Agent|Detective|Officer)\.\s+',
    r'\b(?:Jeffrey|Ghislaine|Virginia|Prince|Duke|Sir|Lord|Lady)\s+',
]

# Common suffixes that follow names
PERSON_SUFFIXES = [
    r'\s+(?:Jr|Sr|III|IV|MD|PhD|Esq)\.?',
]

def extract_person_names(text: str) -> List[str]:
    """
    Extract person names from text using pattern matching.
    
    Note: This is a simplified approach. For production, consider spaCy NER.
    """
    names = set()
    
    # Pattern: Title + Capitalized Words (2-3 words)
    for title_pattern in PERSON_TITLES:
        pattern = title_pattern + r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})'
        matches = re.findall(pattern, text)
        names.update(matches)
    
    # Pattern: Capitalized Name + Suffix
    for suffix_pattern in PERSON_SUFFIXES:
        pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})' + suffix_pattern
        matches = re.findall(pattern, text)
        names.update(matches)
    
    # Common high-profile names (case-specific)
    known_names = [
        'Jeffrey Epstein', 'Ghislaine Maxwell', 'Virginia Giuffre', 'Virginia Roberts',
        'Prince Andrew', 'Bill Clinton', 'Donald Trump', 'Alan Dershowitz',
        'Les Wexner', 'Jean-Luc Brunel', 'Sarah Kellen', 'Nadia Marcinkova',
        'Haley Robson', 'Adriana Ross', 'Lesley Groff'
    ]
    
    for name in known_names:
        if name.lower() in text.lower():
            names.add(name)
    
    return sorted(names)


# Location patterns
LOCATION_PATTERNS = [
    # Cities with state abbreviations
    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})\b',  # e.g., "New York, NY"
    
    # Famous locations (case-specific)
    r'\bLittle\s+St\.?\s+James(?:\s+Island)?\b',
    r'\bGreat\s+St\.?\s+James(?:\s+Island)?\b',
    r'\bPalm\s+Beach\b',
    r'\bManhattan\b',
    r'\bParis,?\s*France\b',
    r'\bLondon,?\s*(?:England|UK)\b',
    r'\bNew\s+Mexico\b',
    r'\bNew\s+York\b',
    
    # Street addresses
    r'\b\d{1,5}\s+(?:East|West|North|South|E\.?|W\.?|N\.?|S\.?)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b',
]

def extract_locations(text: str) -> List[str]:
    """
    Extract location mentions from text.
    """
    locations = set()
    
    for pattern in LOCATION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Handle tuples (city, state) vs strings
            for match in matches:
                if isinstance(match, tuple):
                    locations.add(", ".join(match))
                else:
                    locations.add(match)
    
    return sorted(locations)


def extract_enhanced_file_numbers(text: str) -> List[str]:
    """
    Extract file numbers using enhanced patterns.
    """
    numbers = set()
    
    for pattern in FILE_NUMBER_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        numbers.update(matches)
    
    return sorted(numbers)


def extract_case_metadata(text: str) -> dict:
    """
    Extract comprehensive case-related metadata from text.
    
    Returns:
        {
            "file_numbers": List[str],
            "person_names": List[str],
            "locations": List[str],
            "case_numbers": List[str],  # court case numbers
            "exhibit_numbers": List[str]  # evidence/exhibit IDs
        }
    """
    all_numbers = extract_enhanced_file_numbers(text)
    
    # Separate different types of numbers
    case_numbers = [n for n in all_numbers if re.search(r'(cv|cr|Case|Docket)', n, re.IGNORECASE)]
    exhibit_numbers = [n for n in all_numbers if re.search(r'(Exhibit|Evidence|Batch)', n, re.IGNORECASE)]
    file_numbers = [n for n in all_numbers if n not in case_numbers and n not in exhibit_numbers]
    
    return {
        "file_numbers": file_numbers[:10],  # limit to top 10
        "person_names": extract_person_names(text)[:20],  # limit to top 20
        "locations": extract_locations(text)[:10],  # limit to top 10
        "case_numbers": case_numbers[:5],
        "exhibit_numbers": exhibit_numbers[:10]
    }
