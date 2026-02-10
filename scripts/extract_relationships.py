#!/usr/bin/env python3
"""
Extract relationships between people from emails and documents.

Builds a relationship graph showing connections based on:
- Email From → To patterns
- Meeting attendees in documents
- Co-mentions in same documents
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_email_relationships(catalog: List[Dict]) -> List[Tuple[str, str, str]]:
    """
    Extract From → To relationships from emails.
    
    Returns:
        List of (from_person, to_person, relationship_type) tuples
    """
    relationships = []
    
    for doc in catalog:
        if doc.get('document_category') not in ['email', 'correspondence']:
            continue
        
        from_addr = doc.get('email_from')
        to_addr = doc.get('email_to')
        
        if from_addr and to_addr:
            # Skip placeholder values
            if '[Not visible' not in from_addr and '[Not visible' not in to_addr:
                relationships.append((from_addr, to_addr, 'email'))
    
    return relationships


def extract_co_mentions(catalog: List[Dict]) -> List[Tuple[str, str, str]]:
    """
    Extract co-mention relationships (people mentioned in same document).
    
    Returns:
        List of (person1, person2, relationship_type) tuples
    """
    relationships = []
    
    for doc in catalog:
        people = doc.get('person_names', [])
        if len(people) < 2:
            continue
        
        # Create relationships for all pairs
        for i, person1 in enumerate(people):
            for person2 in people[i+1:]:
                relationships.append((person1, person2, 'co-mentioned'))
    
    return relationships


def build_relationship_graph(catalog: List[Dict]) -> Dict:
    """
    Build a complete relationship graph from catalog.
    
    Returns:
        Dict with nodes (people) and edges (relationships)
    """
    # Extract relationships
    email_rels = extract_email_relationships(catalog)
    co_mention_rels = extract_co_mentions(catalog)
    
    # Build graph
    nodes = set()
    edges = defaultdict(lambda: defaultdict(int))
    
    # Add email relationships
    for from_person, to_person, rel_type in email_rels:
        nodes.add(from_person)
        nodes.add(to_person)
        edges[from_person][to_person] += 1
    
    # Add co-mention relationships
    for person1, person2, rel_type in co_mention_rels:
        nodes.add(person1)
        nodes.add(person2)
        # Bidirectional for co-mentions
        edges[person1][person2] += 1
        edges[person2][person1] += 1
    
    # Convert to serializable format
    graph = {
        'nodes': [{'id': person, 'name': person} for person in sorted(nodes)],
        'edges': [
            {
                'source': from_person,
                'target': to_person,
                'weight': weight
            }
            for from_person, targets in edges.items()
            for to_person, weight in targets.items()
        ]
    }
    
    return graph


if __name__ == '__main__':
    # Load catalog
    catalog_path = Path('data/meta/catalog.json')
    catalog = json.load(catalog_path.open())
    
    print('Extracting relationships...')
    graph = build_relationship_graph(catalog)
    
    print(f'\nRelationship Graph:')
    print(f'  Nodes (people): {len(graph["nodes"])}')
    print(f'  Edges (connections): {len(graph["edges"])}')
    
    # Save graph
    output_path = Path('data/meta/relationships.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w') as f:
        json.dump(graph, f, indent=2)
    
    print(f'\nSaved to: {output_path}')
    
    # Show top connections
    edges_sorted = sorted(graph['edges'], key=lambda e: e['weight'], reverse=True)
    print(f'\nTop 10 connections:')
    for i, edge in enumerate(edges_sorted[:10], 1):
        print(f'  {i}. {edge["source"][:30]} → {edge["target"][:30]} ({edge["weight"]}x)')
