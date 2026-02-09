#!/usr/bin/env python3
"""
Test auto-tagging system on sample documents.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.auto_tagging import generate_auto_tags, tag_summary


# Sample texts for testing
SAMPLE_TEXTS = {
    "flight_log": """
    FLIGHT LOG - Aircraft N908JE
    Date: July 11, 1998
    Passengers: Jeffrey Epstein, Ghislaine Maxwell, Virginia Roberts
    Departure: Palm Beach, FL
    Arrival: Little St. James Island
    """,
    
    "fbi_report": """
    FEDERAL BUREAU OF INVESTIGATION
    File #91E-NYC-323571
    Case No. 19-cr-00490
    
    Investigation into Jeffrey Epstein trafficking allegations.
    Witness statements from Virginia Giuffre regarding abuse at Manhattan residence.
    Evidence photos EFTA00001234, EFTA00001235.
    """,
    
    "court_deposition": """
    UNITED STATES DISTRICT COURT
    SOUTHERN DISTRICT OF NEW YORK
    
    Case No. 1:15-cv-07433
    
    DEPOSITION OF VIRGINIA GIUFFRE
    
    Q: Can you state your name for the record?
    A: Virginia Giuffre, formerly Virginia Roberts.
    
    Q: When did you first meet Jeffrey Epstein?
    A: In 2000, at Mar-a-Lago in Palm Beach.
    """,
    
    "email": """
    From: ghislaine.maxwell@example.com
    To: jeffrey.epstein@example.com
    Date: March 15, 2005
    Subject: Travel arrangements
    
    Jeffrey,
    
    Confirmed flight arrangements for next week's trip to Paris.
    Will coordinate with Jean-Luc Brunel for the event.
    
    Ghislaine
    """,
}


def test_autotagging():
    """Run auto-tagging on sample texts and display results."""
    print("=" * 60)
    print("AUTO-TAGGING SYSTEM TEST")
    print("=" * 60)
    print()
    
    for doc_type, text in SAMPLE_TEXTS.items():
        print(f"Document Type: {doc_type.upper()}")
        print("-" * 60)
        print("Text Sample:")
        print(text[:200] + "..." if len(text) > 200 else text)
        print()
        
        # Generate tags
        tags = generate_auto_tags(
            text=text,
            category=None,  # Let auto-detection work
            person_names=None,  # Will be extracted from text
            locations=None,  # Will be extracted from text
            release_date="2019-08-12",  # Example release date
        )
        
        print(f"Generated Tags ({len(tags)}):")
        print(json.dumps(tags, indent=2))
        print()
        
        # Show organized summary
        summary = tag_summary(tags)
        print("Tag Summary:")
        for category, items in summary.items():
            if items:
                print(f"  {category.capitalize()}: {', '.join(items)}")
        print()
        print("=" * 60)
        print()


def test_edge_cases():
    """Test edge cases and error handling."""
    print("EDGE CASE TESTS")
    print("=" * 60)
    print()
    
    # Empty text
    tags = generate_auto_tags(text="", category=None, release_date="2019-08-12")
    print(f"Empty text: {len(tags)} tags -> {tags}")
    assert len(tags) >= 1  # Should at least have decade tag from release_date
    print("✓ Empty text handled")
    print()
    
    # Very long text
    long_text = "Jeffrey Epstein " * 10000
    tags = generate_auto_tags(text=long_text, category=None)
    print(f"Long text (150k chars): {len(tags)} tags")
    print("✓ Long text handled")
    print()
    
    # Unicode and special characters
    unicode_text = "Jeffrey Épstein, Ghíslaine Mâxwell, Parîs, Frànce"
    tags = generate_auto_tags(text=unicode_text, category=None)
    print(f"Unicode text: {len(tags)} tags -> {tags}")
    print("✓ Unicode handled")
    print()
    
    # No dates
    no_date_text = "Generic document with no dates or years"
    tags = generate_auto_tags(text=no_date_text, category=None, release_date=None)
    print(f"No dates: {len(tags)} tags -> {tags}")
    print("✓ Missing dates handled")
    print()


if __name__ == "__main__":
    test_autotagging()
    test_edge_cases()
    print("\n✅ All auto-tagging tests passed!")
