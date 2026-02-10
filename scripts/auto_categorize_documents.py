#!/usr/bin/env python3
"""
Auto-categorize uncategorized documents using content analysis.

Strategy:
1. Read document text
2. Look for category indicators (keywords, patterns, structure)
3. Assign most likely category with confidence score
4. Update catalog
"""
import json
from pathlib import Path
import re

# Category detection patterns
CATEGORY_PATTERNS = {
    'flight-log': [
        r'\b(departure|arrival|destination|pilot|aircraft|tail number|flight date)\b',
        r'\b(N[0-9]{3,5}[A-Z]{1,2})\b',  # Aircraft tail numbers
        r'\b(passenger manifest|flight log)\b',
        r'\b(JFK|PBI|TEB|LGA|MIA|LAX)\b',  # Airport codes
    ],
    'legal-filing': [
        r'\b(plaintiff|defendant|docket|case no\.|civil action|motion|brief|memorandum of law)\b',
        r'\b(pursuant to|wherefore|respectfully submitted)\b',
        r'\b(united states district court|in the matter of)\b',
        r'\bFed\.\s*R\.\s*Civ\.\s*P\.',  # Federal Rules
    ],
    'deposition': [
        r'\b(deposition|sworn|testimony|transcript|stenographer|court reporter)\b',
        r'\b(Q\.|A\.|EXAMINATION|CROSS-EXAMINATION)\b',
        r'\b(do you swear|tell the truth)\b',
        r'\b(certified shorthand reporter)\b',
    ],
    'subpoena': [
        r'\b(subpoena|summons|duces tecum|compel|production of documents)\b',
        r'\b(you are commanded|appear and testify)\b',
        r'\b(clerk of court|subpoena ad testificandum)\b',
    ],
    'correspondence': [
        r'\b(dear|sincerely|regards|cc:|bcc:)\b',
        r'\b(re:|subject:|from:|to:)\b',
        r'\b(letter|correspondence|communication)\b',
    ],
    'email': [
        r'\b(from:|to:|sent:|subject:|cc:|bcc:)\b',
        r'@[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}',  # Email addresses
        r'\b(forwarded message|original message|reply)\b',
    ],
    'memorandum': [
        r'\b(memorandum|memo|for the record)\b',
        r'\b(to:|from:|date:|subject:)\b.*\b(memorandum|memo)\b',
        r'\b(internal memo|confidential memo)\b',
    ],
    'report': [
        r'\b(report|analysis|findings|investigation|summary)\b',
        r'\b(executive summary|conclusion|recommendation)\b',
        r'\b(prepared by|submitted to)\b',
    ],
    'evidence-list': [
        r'\b(exhibit|evidence|list of documents)\b',
        r'\b(exhibit [A-Z]|exhibit \d+)\b',
        r'\b(government exhibit|plaintiff.{1,20}exhibit)\b',
    ],
    'contact-list': [
        r'\b(contact|address book|phone number|directory)\b',
        r'\b(tel:|mobile:|email:|address:)\b',
        r'\+?\d{1,3}[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}',  # Phone patterns
    ],
}

def detect_category(text: str) -> tuple[str, float]:
    """
    Detect document category based on content.
    Returns (category, confidence_score)
    """
    text_lower = text.lower()[:5000]  # First 5k chars for speed
    
    scores = {}
    
    for category, patterns in CATEGORY_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            score += matches
        scores[category] = score
    
    # Get best category
    if not scores or max(scores.values()) == 0:
        return None, 0.0
    
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    
    # Calculate confidence (normalize by total matches)
    total_matches = sum(scores.values())
    confidence = best_score / total_matches if total_matches > 0 else 0.0
    
    # Minimum threshold
    if best_score < 2:
        return None, 0.0
    
    return best_category, confidence

def categorize_by_title(title: str) -> str | None:
    """Quick categorization based on title patterns."""
    title_lower = title.lower()
    
    if 'contact book' in title_lower or 'address book' in title_lower:
        return 'contact-list'
    if 'masseuse list' in title_lower:
        return 'contact-list'
    if 'flight log' in title_lower:
        return 'flight-log'
    if 'deposition' in title_lower:
        return 'deposition'
    if 'subpoena' in title_lower:
        return 'subpoena'
    
    return None

def main():
    catalog_path = Path("data/meta/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    uncategorized = [doc for doc in catalog if not doc.get("document_category") or doc["document_category"] == "None"]
    
    print(f"Auto-categorizing {len(uncategorized)} uncategorized documents...")
    
    categorized_count = 0
    category_stats = {}
    
    for i, doc in enumerate(uncategorized):
        doc_id = doc["id"]
        
        # Try title-based first
        category = categorize_by_title(doc["title"])
        confidence = 0.95 if category else 0.0
        
        # If no title match, analyze content
        if not category:
            text_path = Path(f"data/derived/text/{doc_id}.txt")
            if text_path.exists():
                text = text_path.read_text(errors="ignore")
                category, confidence = detect_category(text)
        
        # Update document
        if category:
            doc["document_category"] = category
            doc["category_confidence"] = round(confidence, 2)
            categorized_count += 1
            category_stats[category] = category_stats.get(category, 0) + 1
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i+1}/{len(uncategorized)}...")
    
    # Write updated catalog
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    print(f"\n✓ Categorized {categorized_count} documents")
    print(f"✓ Still uncategorized: {len(uncategorized) - categorized_count}")
    
    print("\nCategory breakdown:")
    for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")
    
    # Final stats
    all_categorized = [doc for doc in catalog if doc.get("document_category") and doc["document_category"] != "None"]
    print(f"\nOverall: {len(all_categorized)}/{len(catalog)} documents categorized ({len(all_categorized)/len(catalog)*100:.1f}%)")

if __name__ == "__main__":
    main()
