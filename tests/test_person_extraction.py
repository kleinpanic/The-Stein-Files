#!/usr/bin/env python3
"""Tests for person name extraction."""
from __future__ import annotations

import pytest
from scripts.enhanced_metadata import extract_person_names


class TestKnownPeopleExtraction:
    """Test extraction of known high-profile people."""
    
    def test_jeffrey_epstein(self):
        """Extract Jeffrey Epstein."""
        text = "Meeting with Jeffrey Epstein scheduled for Monday."
        names = extract_person_names(text)
        assert "Jeffrey Epstein" in names
    
    def test_ghislaine_maxwell(self):
        """Extract Ghislaine Maxwell."""
        text = "Ghislaine Maxwell was present at the event."
        names = extract_person_names(text)
        assert "Ghislaine Maxwell" in names
    
    def test_prince_andrew(self):
        """Extract Prince Andrew."""
        text = "Prince Andrew attended the meeting."
        names = extract_person_names(text)
        assert "Prince Andrew" in names
    
    def test_virginia_giuffre(self):
        """Extract Virginia Giuffre."""
        text = "Virginia Giuffre filed a lawsuit."
        names = extract_person_names(text)
        assert "Virginia Giuffre" in names
    
    def test_virginia_roberts(self):
        """Extract Virginia Roberts (maiden name)."""
        text = "Virginia Roberts testified in court."
        names = extract_person_names(text)
        assert "Virginia Roberts" in names


class TestLawyerExtraction:
    """Test extraction of lawyer names."""
    
    def test_alan_dershowitz(self):
        """Extract Alan Dershowitz."""
        text = "Attorney Alan Dershowitz represented the defendant."
        names = extract_person_names(text)
        assert "Alan Dershowitz" in names
    
    def test_roy_black(self):
        """Extract Roy Black."""
        text = "Roy Black appeared in court today."
        names = extract_person_names(text)
        assert "Roy Black" in names
    
    def test_ken_starr(self):
        """Extract Ken Starr."""
        text = "Ken Starr joined the defense team."
        names = extract_person_names(text)
        assert "Ken Starr" in names


class TestBusinessFigures:
    """Test extraction of business figures."""
    
    def test_leon_black(self):
        """Extract Leon Black."""
        text = "Leon Black met with Epstein regularly."
        names = extract_person_names(text)
        assert "Leon Black" in names
    
    def test_les_wexner(self):
        """Extract Les Wexner."""
        text = "Les Wexner was a business associate."
        names = extract_person_names(text)
        assert "Les Wexner" in names
    
    def test_thomas_pritzker(self):
        """Extract Thomas Pritzker."""
        text = "Thomas Pritzker attended the meeting."
        names = extract_person_names(text)
        assert "Thomas Pritzker" in names


class TestMultiplePeople:
    """Test extraction of multiple people from same text."""
    
    def test_meeting_with_multiple_attendees(self):
        """Extract all attendees from meeting description."""
        text = """
Meeting attendees: Jeffrey Epstein, Ghislaine Maxwell,
Leon Black, and Prince Andrew discussed various matters.
"""
        names = extract_person_names(text)
        assert len(names) >= 4
        assert "Jeffrey Epstein" in names
        assert "Ghislaine Maxwell" in names
        assert "Leon Black" in names
        assert "Prince Andrew" in names
    
    def test_legal_document_parties(self):
        """Extract parties from legal document."""
        text = """
Jane Doe, represented by Alan Dershowitz, filed suit against
Prince Andrew and Ghislaine Maxwell.
"""
        names = extract_person_names(text)
        # Should extract known names (not Jane Doe as it's generic)
        assert "Alan Dershowitz" in names
        assert "Prince Andrew" in names
        assert "Ghislaine Maxwell" in names


class TestCaseInsensitive:
    """Test case-insensitive matching."""
    
    def test_lowercase_text(self):
        """Extract names from lowercase text (OCR errors)."""
        text = "meeting with jeffrey epstein and ghislaine maxwell"
        names = extract_person_names(text)
        assert "Jeffrey Epstein" in names
        assert "Ghislaine Maxwell" in names
    
    def test_uppercase_text(self):
        """Extract names from uppercase text."""
        text = "JEFFREY EPSTEIN AND GHISLAINE MAXWELL"
        names = extract_person_names(text)
        assert "Jeffrey Epstein" in names
        assert "Ghislaine Maxwell" in names


class TestOCRGarbageRejection:
    """Test rejection of OCR garbage that looks like names."""
    
    def test_reject_short_fragments(self):
        """Reject very short text fragments."""
        text = "A B C D E F"
        names = extract_person_names(text)
        # Should not extract single letters as names
        assert len(names) == 0 or all(len(n.split()) > 1 for n in names)
    
    def test_reject_gibberish(self):
        """Reject OCR gibberish patterns."""
        text = "asdfj kl;qwer tyuiop"
        names = extract_person_names(text)
        # Should not extract gibberish as names
        assert len(names) == 0


class TestStaffAndAssociates:
    """Test extraction of staff and associates."""
    
    def test_lesley_groff(self):
        """Extract Lesley Groff."""
        text = "Assistant Lesley Groff arranged the meeting."
        names = extract_person_names(text)
        assert "Lesley Groff" in names
    
    def test_sarah_kellen(self):
        """Extract Sarah Kellen."""
        text = "Sarah Kellen was Epstein's assistant."
        names = extract_person_names(text)
        assert "Sarah Kellen" in names
    
    def test_nadia_marcinkova(self):
        """Extract Nadia Marcinkova."""
        text = "Nadia Marcinkova was present at the property."
        names = extract_person_names(text)
        assert "Nadia Marcinkova" in names


class TestEdgeCases:
    """Test edge cases."""
    
    def test_empty_text(self):
        """Handle empty text."""
        names = extract_person_names("")
        assert names == []
    
    def test_no_known_people(self):
        """Return empty list when no known people found."""
        text = "This document discusses various financial matters."
        names = extract_person_names(text)
        assert len(names) == 0
    
    def test_partial_name_no_match(self):
        """Don't extract partial name matches."""
        text = "Mr. Epstein (not Jeffrey) attended the meeting."
        names = extract_person_names(text)
        # Should not match "Epstein" alone - needs full name
        assert "Jeffrey Epstein" in names or len(names) == 0
