#!/usr/bin/env python3
"""
Fuzzy categorization for OCR-garbled text.
Uses edit distance to match keywords even with OCR errors.
"""
import json
from pathlib import Path
from difflib import SequenceMatcher
import re

# Keywords for each category (will match fuzzily)
FUZZY_KEYWORDS = {
    'flight-log': [
        'departure', 'arrival', 'destination', 'pilot', 'aircraft', 'flight', 
        'passenger', 'manifest', 'airport', 'tail number'
    ],
    'deposition': [
        'deposition', 'testimony', 'sworn', 'transcript', 'stenographer',
        'examination', 'cross-examination', 'witness'
    ],
    'legal-filing': [
        'plaintiff', 'defendant', 'docket', 'motion', 'brief', 'court',
        'filing', 'memorandum of law', 'civil action'
    ],
    'correspondence': [
        'dear', 'sincerely', 'regards', 'letter', 'correspondence',
        'communication', 'attached', 'forwarded'
    ],
    'email': [
        'from:', 'to:', 'subject:', 'sent:', 'forwarded message',
        'original message', 'reply'
    ],
    'memorandum': [
        'memorandum', 'memo', 'to:', 'from:', 'subject:', 'date:',
        'for the record', 'internal'
    ],
    'maintenance': [  # NEW category for service docs
        'maintenance', 'inspection', 'service', 'repair', 'test',
        'treatment', 'tower', 'equipment', 'monthly', 'perform'
    ],
    'report': [
        'report', 'analysis', 'findings', 'investigation', 'summary',
        'executive summary', 'conclusion'
    ],
}

def fuzzy_match(word: str, target: str, threshold: float = 0.75) -> bool:
    """
    Check if word matches target with fuzzy matching.
    Returns True if similarity >= threshold.
    """
    if len(word) < 3 or len(target) < 3:
        return word.lower() == target.lower()
    
    similarity = SequenceMatcher(None, word.lower(), target.lower()).ratio()
    return similarity >= threshold

def find_fuzzy_keywords(text: str, keywords: list, threshold: float = 0.75) -> int:
    """
    Count fuzzy matches for keywords in text.
    """
    # Tokenize text (split on whitespace and punctuation)
    words = re.findall(r'\b\w+\b', text.lower())
    
    match_count = 0
    for keyword in keywords:
        keyword_words = keyword.split()
        
        if len(keyword_words) == 1:
            # Single word keyword - check each text word
            for word in words:
                if fuzzy_match(word, keyword, threshold):
                    match_count += 1
                    break  # Count each keyword once
        else:
            # Multi-word keyword - look for phrase
            keyword_lower = keyword.lower()
            if keyword_lower in text.lower():
                match_count += 1
    
    return match_count

def fuzzy_categorize(text: str, threshold: float = 0.75) -> tuple[str, float]:
    """
    Categorize text using fuzzy keyword matching.
    Returns (category, confidence_score)
    """
    # Only use first 3000 chars for speed
    text_sample = text[:3000]
    
    scores = {}
    for category, keywords in FUZZY_KEYWORDS.items():
        score = find_fuzzy_keywords(text_sample, keywords, threshold)
        scores[category] = score
    
    # Get best category
    if not scores or max(scores.values()) == 0:
        return None, 0.0
    
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    
    # Calculate confidence
    total_matches = sum(scores.values())
    confidence = best_score / total_matches if total_matches > 0 else 0.0
    
    # Minimum threshold (need at least 2 keyword matches)
    if best_score < 2:
        return None, 0.0
    
    return best_category, confidence

def main():
    catalog_path = Path("data/meta/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    # Get uncategorized docs with OCR applied
    uncategorized_ocr = [
        doc for doc in catalog
        if (not doc.get("document_category") or doc["document_category"] == "None")
        and doc.get("ocr_applied")
        and doc.get("text_quality_score", 0) > 10
    ]
    
    print(f"Fuzzy categorizing {len(uncategorized_ocr)} OCR'd uncategorized documents...")
    
    categorized_count = 0
    category_stats = {}
    
    for i, doc in enumerate(uncategorized_ocr):
        doc_id = doc["id"]
        text_path = Path(f"data/derived/text/{doc_id}.txt")
        
        if not text_path.exists():
            continue
        
        text = text_path.read_text(errors="ignore")
        category, confidence = fuzzy_categorize(text, threshold=0.70)  # Lower threshold for OCR
        
        if category:
            doc["document_category"] = category
            doc["category_confidence"] = round(confidence, 2)
            doc["category_method"] = "fuzzy"
            categorized_count += 1
            category_stats[category] = category_stats.get(category, 0) + 1
            
            if (i + 1) % 10 == 0:
                print(f"  Processed {i+1}/{len(uncategorized_ocr)}...")
    
    # Write updated catalog
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    print(f"\n✓ Fuzzy categorized {categorized_count} documents")
    
    print("\nCategory breakdown:")
    for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")
    
    # Final stats
    all_categorized = [doc for doc in catalog if doc.get("document_category") and doc["document_category"] != "None"]
    uncategorized_remaining = [doc for doc in catalog if not doc.get("document_category") or doc["document_category"] == "None"]
    
    print(f"\nOverall: {len(all_categorized)}/{len(catalog)} categorized ({len(all_categorized)/len(catalog)*100:.1f}%)")
    print(f"Uncategorized remaining: {len(uncategorized_remaining)} ({len(uncategorized_remaining)/len(catalog)*100:.1f}%)")

if __name__ == "__main__":
    main()
