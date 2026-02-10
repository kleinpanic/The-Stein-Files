#!/usr/bin/env python3
"""
Normalize dates to ISO8601 format for timeline queries.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional


def parse_date_string(date_str: str) -> Optional[str]:
    """
    Parse a date string in various formats and return ISO8601 (YYYY-MM-DD).
    
    Returns None if the date cannot be parsed.
    """
    date_str = date_str.strip()
    
    # Already ISO8601
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # MM/DD/YYYY or M/D/YYYY
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
    if match:
        month, day, year = match.groups()
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return None
    
    # Month DD, YYYY (e.g., "July 2, 2019", "Feb 16, 2017")
    match = re.match(
        r'^(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
        r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        r'\s+(\d{1,2}),?\s+(\d{4})$',
        date_str,
        re.IGNORECASE
    )
    if match:
        month_str, day, year = match.groups()
        month_map = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12,
        }
        month = month_map.get(month_str.lower())
        if month:
            try:
                dt = datetime(int(year), month, int(day))
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                return None
    
    # DD Month YYYY (e.g., "2 July 2019")
    match = re.match(
        r'^(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
        r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        r'\s+(\d{4})$',
        date_str,
        re.IGNORECASE
    )
    if match:
        day, month_str, year = match.groups()
        month_map = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12,
        }
        month = month_map.get(month_str.lower())
        if month:
            try:
                dt = datetime(int(year), month, int(day))
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                return None
    
    return None


def normalize_dates(dates: List[str]) -> List[str]:
    """
    Normalize a list of date strings to ISO8601 format.
    
    Returns a sorted list of unique ISO8601 dates.
    Skips dates that cannot be parsed.
    """
    normalized = set()
    for date_str in dates:
        iso_date = parse_date_string(date_str)
        if iso_date:
            normalized.add(iso_date)
    
    return sorted(normalized)


if __name__ == '__main__':
    # Test date normalization
    test_dates = [
        '07/02/2020',
        '8/13/2019',
        'Feb 16, 2017',
        'July 2, 2019',
        '2019-07-02',
        'January 7, 2020',
    ]
    
    print('Date Normalization Test:')
    for date in test_dates:
        normalized = parse_date_string(date)
        print(f'  {date:20s} → {normalized}')
    
    print('\nBatch normalization:')
    normalized_list = normalize_dates(test_dates)
    print(f'  Input: {len(test_dates)} dates')
    print(f'  Output: {len(normalized_list)} unique ISO8601 dates')
    print(f'  Result: {normalized_list}')
