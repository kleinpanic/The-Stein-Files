#!/usr/bin/env python3
"""
Analyze person mentions from catalog.json to identify major figures.
Threshold: 5+ document mentions
"""

import json
from collections import defaultdict
from pathlib import Path

def main():
    catalog_path = Path(__file__).parent.parent / "data/meta/catalog.json"
    
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    # Count person mentions across documents
    person_to_docs = defaultdict(set)
    person_to_doc_details = defaultdict(list)
    
    for doc in catalog:
        doc_id = doc.get('id', 'unknown')
        doc_title = doc.get('title', 'Untitled')
        doc_category = doc.get('document_category', 'uncategorized')
        
        for person in doc.get('person_names', []):
            person_to_docs[person].add(doc_id)
            person_to_doc_details[person].append({
                'id': doc_id,
                'title': doc_title,
                'category': doc_category
            })
    
    # Convert to counts and sort
    person_counts = {
        person: len(doc_ids) 
        for person, doc_ids in person_to_docs.items()
    }
    
    sorted_people = sorted(person_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Filter for major people (5+ mentions)
    major_people = [(name, count) for name, count in sorted_people if count >= 5]
    
    print("=" * 80)
    print(f"PERSON MENTION ANALYSIS")
    print("=" * 80)
    print(f"Total unique people extracted: {len(person_counts)}")
    print(f"Major people (5+ mentions): {len(major_people)}")
    print(f"Total documents in catalog: {len(catalog)}")
    print()
    
    print("=" * 80)
    print("TOP 50 MAJOR PEOPLE (sorted by mention count)")
    print("=" * 80)
    for i, (name, count) in enumerate(major_people[:50], 1):
        print(f"{i:3d}. {name:40s} {count:4d} mentions")
    
    if len(major_people) > 50:
        print(f"\n... and {len(major_people) - 50} more major people")
    
    # Save full analysis
    output = {
        'total_unique_people': len(person_counts),
        'major_people_count': len(major_people),
        'total_documents': len(catalog),
        'major_people': [
            {
                'name': name,
                'mention_count': count,
                'documents': list(person_to_docs[name]),
                'sample_docs': person_to_doc_details[name][:5]  # First 5 docs
            }
            for name, count in major_people
        ],
        'all_people': [
            {'name': name, 'mention_count': count}
            for name, count in sorted_people
        ]
    }
    
    output_path = Path(__file__).parent.parent / "data/derived/person_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Full analysis saved to: {output_path}")
    
    # Document type breakdown for top 10
    print("\n" + "=" * 80)
    print("DOCUMENT TYPE BREAKDOWN (Top 10 People)")
    print("=" * 80)
    
    for name, count in major_people[:10]:
        categories = defaultdict(int)
        for doc_detail in person_to_doc_details[name]:
            categories[doc_detail['category']] += 1
        
        print(f"\n{name} ({count} mentions):")
        for category, cat_count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {category}: {cat_count}")

if __name__ == "__main__":
    main()
