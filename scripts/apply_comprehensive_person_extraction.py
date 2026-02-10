#!/usr/bin/env python3
"""
Apply comprehensive person extraction to catalog.
Uses complete list of 50+ known Epstein-related people.
"""
import json
from pathlib import Path
from collections import defaultdict
import re

# Comprehensive list (44 people found + 7 not found but still searchable)
KNOWN_PEOPLE = [
    # Primary figures
    ('Jeffrey Epstein', ['Epstein', 'Jeffrey', 'Jeff Epstein']),
    ('Ghislaine Maxwell', ['Maxwell', 'Ghislaine']),
    ('Virginia Giuffre', ['Giuffre', 'Virginia Roberts', 'Roberts']),
    
    # Financiers/Business (HIGH PRIORITY - were missing!)
    ('Leon Black', ['Leon Black', 'Black']),  # 76 mentions!
    ('Thomas Pritzker', ['Pritzker', 'Thomas']),  # 29 mentions!
    ('Les Wexner', ['Wexner', 'Leslie Wexner']),
    ('Glenn Dubin', ['Dubin', 'Glenn']),
    ('Mort Zuckerman', ['Zuckerman', 'Mortimer']),
    ('Peter Listerman', ['Listerman', 'Peter']),
    
    # Politicians
    ('Bill Clinton', ['Clinton', 'William Clinton', 'President Clinton']),
    ('Donald Trump', ['Trump', 'Donald']),
    ('Prince Andrew', ['Andrew', 'Prince Andrew', 'Duke of York']),
    ('Bill Richardson', ['Richardson', 'Governor Richardson']),
    ('George Mitchell', ['Mitchell', 'George Mitchell', 'Senator Mitchell']),
    ('Ehud Barak', ['Barak', 'Ehud']),
    
    # Tech (HIGH PRIORITY - Elon was missing!)
    ('Elon Musk', ['Musk', 'Elon']),
    ('Bill Gates', ['Gates', 'Bill Gates', 'William Gates']),
    
    # Celebrities/Entertainment (HIGH PRIORITY - many missing!)
    ('Kevin Spacey', ['Spacey', 'Kevin']),  # 7 mentions!
    ('Chris Tucker', ['Tucker', 'Chris Tucker']),
    ('Naomi Campbell', ['Campbell', 'Naomi']),
    ('Heidi Klum', ['Klum', 'Heidi']),
    ('Courtney Love', ['Love', 'Courtney']),  # 13 mentions!
    ('Woody Allen', ['Allen', 'Woody']),  # 4 mentions
    
    # Scientists/Academics (HIGH PRIORITY - missing!)
    ('Stephen Hawking', ['Hawking', 'Stephen']),
    ('Marvin Minsky', ['Minsky', 'Marvin']),
    ('Lawrence Krauss', ['Krauss', 'Lawrence']),  # 4 mentions!
    ('Steven Pinker', ['Pinker', 'Steven']),
    ('Larry Summers', ['Summers', 'Larry', 'Lawrence Summers']),  # 11 mentions!
    
    # Legal/Associates (HIGH PRIORITY - missing!)
    ('Alan Dershowitz', ['Dershowitz', 'Alan']),
    ('Ken Starr', ['Starr', 'Ken', 'Kenneth Starr']),  # 8 mentions!
    ('Roy Black', ['Roy Black']),  # 3 mentions
    ('Jay Lefkowitz', ['Lefkowitz', 'Jay']),  # 8 mentions!
    
    # Staff/Associates
    ('Sarah Kellen', ['Kellen', 'Sarah']),
    ('Nadia Marcinkova', ['Marcinkova', 'Nadia']),
    ('Lesley Groff', ['Groff', 'Lesley']),
    ('Adriana Ross', ['Ross', 'Adriana']),
    ('Haley Robson', ['Robson', 'Haley']),
    ('Juan Alessi', ['Alessi', 'Juan']),  # 11 mentions
    ('Alfredo Rodriguez', ['Rodriguez', 'Alfredo']),
    ('Tony Figueroa', ['Figueroa', 'Tony']),
    ('Rinaldo Rizzo', ['Rizzo', 'Rinaldo']),
    ('Emmy Tayler', ['Tayler', 'Emmy']),
    
    # Models/Recruiters
    ('Jean-Luc Brunel', ['Brunel', 'Jean-Luc', 'Jean Luc']),  # 7 mentions!
    ('Eva Andersson-Dubin', ['Andersson', 'Andersson-Dubin', 'Eva Dubin']),
    ('Eva Dubin', ['Eva Dubin']),
    ('Shelley Lewis', ['Lewis', 'Shelley']),
    ('Shelley Harrison', ['Harrison', 'Shelley']),
    
    # Victims/Accusers (public)
    ('Maria Farmer', ['Farmer', 'Maria']),  # 8 mentions!
    ('Annie Farmer', ['Annie Farmer']),
    ('Johanna Sjoberg', ['Sjoberg', 'Johanna']),
    ('Chauntae Davies', ['Davies', 'Chauntae']),
]

def scan_for_person(text_lower, full_name, variants):
    """Check if any variant of person name appears in text."""
    for variant in variants:
        pattern = r'\b' + re.escape(variant.lower()) + r'\b'
        if re.search(pattern, text_lower):
            return True
    return False

def main():
    catalog_path = Path("data/meta/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    print(f"Applying comprehensive person extraction to {len(catalog)} documents...")
    print(f"Searching for {len(KNOWN_PEOPLE)} known people...")
    
    updated_count = 0
    
    for doc in catalog:
        doc_id = doc["id"]
        text_path = Path(f"data/derived/text/{doc_id}.txt")
        
        if not text_path.exists():
            continue
        
        text = text_path.read_text(errors="ignore")
        text_lower = text.lower()
        
        # Find all people mentioned in this document
        people_in_doc = []
        for full_name, variants in KNOWN_PEOPLE:
            if scan_for_person(text_lower, full_name, variants):
                people_in_doc.append(full_name)
        
        # Update catalog
        if people_in_doc:
            doc["person_names"] = sorted(people_in_doc)
            updated_count += 1
        else:
            doc["person_names"] = []
    
    # Write updated catalog
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    print(f"\n✓ Updated {updated_count} documents with comprehensive person extraction")
    
    # Generate stats
    name_counts = defaultdict(int)
    for doc in catalog:
        for name in doc.get("person_names", []):
            name_counts[name] += 1
    
    print(f"\nTotal unique people: {len(name_counts)}")
    print(f"People with 5+ mentions: {sum(1 for c in name_counts.values() if c >= 5)}")
    print(f"People with 3-4 mentions: {sum(1 for c in name_counts.values() if 3 <= c < 5)}")
    print(f"People with 1-2 mentions: {sum(1 for c in name_counts.values() if c < 3)}")
    
    print("\nTop 25 most mentioned:")
    for name, count in sorted(name_counts.items(), key=lambda x: x[1], reverse=True)[:25]:
        print(f"  {name}: {count} docs")

if __name__ == "__main__":
    main()
