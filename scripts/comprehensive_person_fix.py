#!/usr/bin/env python3
"""
Comprehensive person extraction fix - hybrid approach.

Strategy:
1. Extract full names where present
2. Search for last-name mentions of known high-profile people
3. Attribute last-name mentions to canonical full names
4. Update catalog with complete person coverage
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set, Dict
import json


# High-profile people known to be involved in Epstein case
# Format: (FullName, [lastnames to search])
HIGH_PROFILE_PEOPLE = [
    ('Jeffrey Epstein', ['Epstein']),
    ('Ghislaine Maxwell', ['Maxwell']),
    ('Virginia Giuffre', ['Giuffre', 'Roberts']),  # Also known as Virginia Roberts
    ('Prince Andrew', ['Andrew']),  # Note: "Andrew" alone can be ambiguous
    ('Bill Clinton', ['Clinton']),
    ('Donald Trump', ['Trump']),
    ('Alan Dershowitz', ['Dershowitz']),
    ('Les Wexner', ['Wexner']),
    ('Jean-Luc Brunel', ['Brunel']),
    ('Sarah Kellen', ['Kellen']),
    ('Nadia Marcinkova', ['Marcinkova']),
    ('Haley Robson', ['Robson']),
    ('Adriana Ross', ['Ross']),  # Note: "Ross" is common, may need context
    ('Lesley Groff', ['Groff']),
    ('Juan Alessi', ['Alessi']),
    ('Alfredo Rodriguez', ['Rodriguez', 'Alfredo Rodriguez']),
    ('Tony Figueroa', ['Figueroa']),
    ('Rinaldo Rizzo', ['Rizzo']),
    ('Emmy Tayler', ['Tayler', 'Emmy Tayler']),
    ('Eva Andersson-Dubin', ['Andersson-Dubin', 'Andersson', 'Dubin']),
    ('Glenn Dubin', ['Glenn Dubin']),
    ('Marvin Minsky', ['Minsky']),
    ('Stephen Hawking', ['Hawking']),
    ('Kevin Spacey', ['Spacey']),
    ('Chris Tucker', ['Tucker']),
    ('Naomi Campbell', ['Campbell']),  # Note: "Campbell" is common
    ('Heidi Klum', ['Klum']),
    ('Courtney Love', ['Courtney Love']),
    ('George Mitchell', ['George Mitchell']),
    ('Ron Burkle', ['Burkle']),
    ('Bill Richardson', ['Richardson']),  # Note: "Richardson" is common
    ('Ehud Barak', ['Barak']),
]

# Blacklist: Common words that look like names but aren't
BLACKLIST_TERMS = {
    'hello', 'hi', 'dear', 'sent', 'from', 'to', 'subject', 'cc', 'bcc',
    'morning', 'afternoon', 'evening', 'ok', 'okay', 'thanks', 'thank',
    'date', 'time', 'page', 'total', 'document', 'file', 'case',
    'court', 'judge', 'attorney', 'agent', 'officer', 'president',
    'new', 'york', 'city', 'street', 'service', 'register',
    'device', 'title', 'nope', 'sure', 'cool', 'great', 'good',
}


def extract_full_names(text: str) -> Set[str]:
    """Extract full names using title patterns."""
    names = set()
    
    # Pattern: Title + Capitalized Name (2-3 words)
    title_pattern = r'\b(?:Mr|Ms|Mrs|Miss|Dr|Prof|President|Judge|Attorney|Agent|Detective|Officer|Senator|Representative|Governor)\.\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
    for match in re.finditer(title_pattern, text):
        candidate = match.group(1).strip()
        # Basic validation
        if len(candidate) > 5 and not any(bad in candidate.lower() for bad in BLACKLIST_TERMS):
            names.add(candidate)
    
    return names


def search_high_profile_names(text: str) -> Dict[str, int]:
    """
    Search for high-profile people by full name AND last name.
    
    Returns: {canonical_full_name: mention_count}
    """
    text_lower = text.lower()
    mentions = {}
    
    for full_name, lastnames in HIGH_PROFILE_PEOPLE:
        count = 0
        
        # Search for full name (case-insensitive)
        count += len(re.findall(re.escape(full_name.lower()), text_lower))
        
        # Search for each lastname variant
        for lastname in lastnames:
            # Word boundary matching to avoid substring matches
            pattern = r'\b' + re.escape(lastname.lower()) + r'\b'
            lastname_matches = len(re.findall(pattern, text_lower))
            
            # Context filtering for ambiguous names
            if lastname.lower() in ['andrew', 'ross', 'campbell', 'richardson']:
                # These are common names - only count if preceded by context
                # e.g., "Prince Andrew", "Mr. Ross", etc.
                context_pattern = r'(?:prince|mr|ms|mrs|duke)\s+' + pattern
                context_matches = len(re.findall(context_pattern, text_lower))
                count += context_matches
            else:
                count += lastname_matches
        
        if count > 0:
            mentions[full_name] = count
    
    return mentions


def extract_person_names_hybrid(text: str) -> List[str]:
    """
    Hybrid extraction: full names + high-profile name search.
    """
    names = set()
    
    # Method 1: Extract full names with title patterns
    full_names = extract_full_names(text)
    names.update(full_names)
    
    # Method 2: Search for high-profile people
    high_profile = search_high_profile_names(text)
    names.update(high_profile.keys())
    
    return sorted(names)


def main():
    """Re-extract person names using hybrid approach."""
    catalog_path = Path("data/meta/catalog.json")
    
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    print(f"Running comprehensive person extraction on {len(catalog)} documents...")
    print("Using hybrid approach: full names + high-profile last-name matching")
    
    updated_count = 0
    for doc in catalog:
        doc_id = doc["id"]
        text_path = Path(f"data/derived/text/{doc_id}.txt")
        
        if not text_path.exists():
            continue
        
        text = text_path.read_text(errors="ignore")
        
        # Extract person names (hybrid)
        person_names = extract_person_names_hybrid(text)
        
        # Update doc
        doc["person_names"] = person_names
        if person_names:
            updated_count += 1
    
    # Write updated catalog
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    print(f"\n✓ Updated {updated_count} documents with hybrid person extraction")
    
    # Generate stats
    name_counts = {}
    for doc in catalog:
        for name in doc.get("person_names", []):
            name_counts[name] = name_counts.get(name, 0) + 1
    
    print(f"\nTotal unique person names: {len(name_counts)}")
    print(f"People with 5+ mentions: {sum(1 for c in name_counts.values() if c >= 5)}")
    print(f"People with 3-4 mentions: {sum(1 for c in name_counts.values() if 3 <= c < 5)}")
    
    print("\nTop 20 most mentioned:")
    for name, count in sorted(name_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {name}: {count} docs")
    
    return name_counts


if __name__ == "__main__":
    main()
