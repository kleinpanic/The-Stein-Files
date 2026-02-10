#!/usr/bin/env python3
"""
Fast comprehensive person extraction using precompiled patterns.
"""
import json
from pathlib import Path
from collections import defaultdict
import re

# Complete list with SINGLE primary search term (most distinctive)
KNOWN_PEOPLE = {
    'Jeffrey Epstein': 'epstein',
    'Ghislaine Maxwell': 'maxwell',
    'Virginia Giuffre': 'giuffre',
    'Leon Black': 'leon black',
    'Thomas Pritzker': 'pritzker',
    'Les Wexner': 'wexner',
    'Glenn Dubin': 'glenn dubin',
    'Bill Clinton': 'clinton',
    'Donald Trump': 'trump',
    'Prince Andrew': 'prince andrew',
    'Bill Richardson': 'bill richardson',
    'George Mitchell': 'george mitchell',
    'Ehud Barak': 'ehud barak',
    'Elon Musk': 'elon',
    'Bill Gates': 'bill gates',
    'Kevin Spacey': 'spacey',
    'Chris Tucker': 'chris tucker',
    'Naomi Campbell': 'naomi campbell',
    'Courtney Love': 'courtney love',
    'Woody Allen': 'woody allen',
    'Stephen Hawking': 'hawking',
    'Marvin Minsky': 'minsky',
    'Lawrence Krauss': 'krauss',
    'Steven Pinker': 'pinker',
    'Larry Summers': 'larry summers',
    'Alan Dershowitz': 'dershowitz',
    'Ken Starr': 'ken starr',
    'Roy Black': 'roy black',
    'Jay Lefkowitz': 'lefkowitz',
    'Sarah Kellen': 'kellen',
    'Nadia Marcinkova': 'marcinkova',
    'Lesley Groff': 'groff',
    'Adriana Ross': 'adriana ross',
    'Juan Alessi': 'alessi',
    'Alfredo Rodriguez': 'alfredo rodriguez',
    'Tony Figueroa': 'figueroa',
    'Emmy Tayler': 'emmy tayler',
    'Jean-Luc Brunel': 'brunel',
    'Eva Andersson-Dubin': 'andersson',
    'Shelley Lewis': 'shelley lewis',
    'Maria Farmer': 'maria farmer',
    'Annie Farmer': 'annie farmer',
    'Peter Listerman': 'listerman',
    'Mort Zuckerman': 'zuckerman',
}

# Precompile patterns
PATTERNS = {
    name: re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
    for name, term in KNOWN_PEOPLE.items()
}

def main():
    catalog_path = Path("data/meta/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    print(f"Fast comprehensive extraction: {len(catalog)} docs, {len(KNOWN_PEOPLE)} people...")
    
    updated_count = 0
    processed = 0
    
    for doc in catalog:
        doc_id = doc["id"]
        text_path = Path(f"data/derived/text/{doc_id}.txt")
        
        if not text_path.exists():
            continue
        
        text = text_path.read_text(errors="ignore").lower()
        
        # Find all people in this document
        people_in_doc = []
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                people_in_doc.append(name)
        
        # Update catalog
        doc["person_names"] = sorted(people_in_doc)
        if people_in_doc:
            updated_count += 1
        
        processed += 1
        if processed % 100 == 0:
            print(f"  Processed {processed}/{len(catalog)}...")
    
    # Write updated catalog
    print("Writing catalog...")
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    print(f"\n✓ Updated {updated_count} documents")
    
    # Stats
    name_counts = defaultdict(int)
    for doc in catalog:
        for name in doc.get("person_names", []):
            name_counts[name] += 1
    
    print(f"\nPeople with 3+ mentions: {sum(1 for c in name_counts.values() if c >= 3)}")
    print("\nTop 30 most mentioned:")
    for name, count in sorted(name_counts.items(), key=lambda x: x[1], reverse=True)[:30]:
        print(f"  {name}: {count} docs")

if __name__ == "__main__":
    main()
