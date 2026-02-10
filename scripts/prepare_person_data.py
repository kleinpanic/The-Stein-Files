#!/usr/bin/env python3
"""
Prepare clean person data for person profile pages.
Filters out extraction errors, normalizes names, generates per-person JSON.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from datetime import datetime

def is_valid_person_name(name: str) -> bool:
    """Filter out obvious extraction errors."""
    if not name or len(name) < 2:
        return False
    
    # Reject if contains newlines, tabs, or excessive whitespace
    if '\n' in name or '\t' in name or '  ' in name:
        return False
    
    # Reject obvious non-person patterns
    bad_patterns = [
        r'^\d+$',  # Just numbers
        r'^Page\s+\d+',  # Page numbers
        r'^Total',
        r'Date$',
        r'Trial$',
        r'Title$',
        r'^\s*Ok\s*$',
        r'^\s*Sure\s*$',
        r'^\s*Tuesday\s*$',
        r'PROCEDURES',
        r'SAP\s+',
    ]
    
    for pattern in bad_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return False
    
    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', name):
        return False
    
    return True

def normalize_name(name: str) -> str:
    """Basic name normalization."""
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def extract_date_from_doc(doc: dict) -> str:
    """Extract best available date from document."""
    # Try extracted dates first
    if doc.get('extracted_dates'):
        dates = doc['extracted_dates']
        if dates:
            return dates[0]  # Return first extracted date
    
    # Fall back to release date
    if doc.get('release_date'):
        return doc['release_date']
    
    return 'Unknown'

def parse_date_for_sorting(date_str: str) -> tuple:
    """Parse date string for sorting. Returns (year, month, day) or (9999, 99, 99) for unknown."""
    if date_str == 'Unknown' or not date_str:
        return (9999, 99, 99)
    
    # Try common formats
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%b %d, %Y',
        '%B %d, %Y',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return (dt.year, dt.month, dt.day)
        except:
            continue
    
    # Try to extract just year
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        return (int(year_match.group()), 0, 0)
    
    return (9999, 99, 99)

def main():
    catalog_path = Path("data/meta/catalog.json")
    
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    # Collect person data
    person_to_docs = defaultdict(list)
    person_to_categories = defaultdict(lambda: defaultdict(int))
    
    for doc in catalog:
        doc_id = doc.get('id', 'unknown')
        
        for person in doc.get('person_names', []):
            # Validate and normalize
            if not is_valid_person_name(person):
                continue
            
            person = normalize_name(person)
            
            # Store document reference
            person_to_docs[person].append({
                'id': doc_id,
                'title': doc.get('title', 'Untitled'),
                'category': doc.get('document_category', 'uncategorized'),
                'date': extract_date_from_doc(doc),
                'source_name': doc.get('source_name', 'Unknown'),
                'pages': doc.get('pages', 0),
                'file_size_bytes': doc.get('file_size_bytes', 0),
                'tags': doc.get('tags', []),
            })
            
            # Count categories
            category = doc.get('document_category', 'uncategorized')
            person_to_categories[person][category] += 1
    
    # Filter for major people (1+ mentions - show all)
    major_people = {
        person: docs 
        for person, docs in person_to_docs.items() 
        if len(docs) >= 1
    }
    
    # Sort people by mention count
    sorted_people = sorted(
        major_people.items(), 
        key=lambda x: len(x[1]), 
        reverse=True
    )
    
    # Generate output data
    people_data = []
    
    for person, docs in sorted_people:
        # Sort documents by date
        docs_sorted = sorted(docs, key=lambda d: parse_date_for_sorting(d['date']))
        
        # Get category breakdown
        categories = dict(person_to_categories[person])
        category_list = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        # Group by year for timeline
        timeline = defaultdict(list)
        for doc in docs_sorted:
            year = parse_date_for_sorting(doc['date'])[0]
            if year == 9999:
                year = 'Unknown'
            timeline[year].append(doc)
        
        person_data = {
            'name': person,
            'slug': re.sub(r'[^a-z0-9]+', '-', person.lower()).strip('-'),
            'mention_count': len(docs),
            'documents': docs_sorted,
            'categories': category_list,
            'timeline': dict(timeline),
        }
        
        people_data.append(person_data)
    
    # Save master people data
    output_dir = Path("data/derived")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    master_output = {
        'generated_at': datetime.now().isoformat(),
        'total_people': len(people_data),
        'threshold_mentions': 1,
        'people': people_data,
    }
    
    with open(output_dir / "people.json", 'w') as f:
        json.dump(master_output, f, indent=2)
    
    # Save individual person files
    people_dir = output_dir / "people"
    people_dir.mkdir(exist_ok=True)
    
    for person_data in people_data:
        slug = person_data['slug']
        with open(people_dir / f"{slug}.json", 'w') as f:
            json.dump(person_data, f, indent=2)
    
    print("=" * 80)
    print("PERSON DATA PREPARATION")
    print("=" * 80)
    print(f"Total people (1+ mentions): {len(people_data)}")
    print(f"Master file: {output_dir / 'people.json'}")
    print(f"Individual files: {people_dir}/")
    print()
    
    print("Major People:")
    for person_data in people_data:
        print(f"  - {person_data['name']:40s} {person_data['mention_count']:3d} mentions")
        print(f"    Top categories: {', '.join(f'{cat}({count})' for cat, count in person_data['categories'][:3])}")
    
    print()
    print("✓ Person data prepared successfully")

if __name__ == "__main__":
    main()
