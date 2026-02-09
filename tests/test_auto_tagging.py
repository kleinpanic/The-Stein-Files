#!/usr/bin/env python3
"""
pytest tests for auto-tagging system (Phase 2).

Tests:
- Keyword-based tagging
- Person name tagging
- Location tagging
- Date-range tagging
- Document-source tagging
- Tag normalization
"""
from __future__ import annotations

import pytest

from scripts.auto_tagging import (
    extract_date_range_tags,
    extract_keyword_tags,
    extract_location_tags,
    extract_person_tags,
    extract_source_tags,
    generate_auto_tags,
    tag_summary,
)


class TestKeywordTags:
    """Test keyword-based auto-tagging."""
    
    def test_flight_keywords(self):
        text = "Flight log for aircraft N908JE, passenger manifest included."
        tags = extract_keyword_tags(text)
        assert "flight" in tags
    
    def test_victim_keywords(self):
        text = "Victim testimony regarding trafficking and abuse of minors."
        tags = extract_keyword_tags(text)
        assert "victim" in tags
    
    def test_witness_keywords(self):
        text = "Witness statement provided under oath, testified in deposition."
        tags = extract_keyword_tags(text)
        assert "witness" in tags
    
    def test_evidence_keywords(self):
        text = "Evidence photograph exhibit number EFTA00001234."
        tags = extract_keyword_tags(text)
        assert "evidence" in tags
    
    def test_financial_keywords(self):
        text = "Wire transfer payment of $10,000 to offshore account."
        tags = extract_keyword_tags(text)
        assert "financial" in tags
    
    def test_investigation_keywords(self):
        text = "FBI investigation led to search and seizure of documents."
        tags = extract_keyword_tags(text)
        assert "investigation" in tags
    
    def test_case_insensitive(self):
        text = "FLIGHT LOG for AIRCRAFT"
        tags = extract_keyword_tags(text)
        assert "flight" in tags


class TestSourceTags:
    """Test document source tagging."""
    
    def test_fbi_source(self):
        text = "FEDERAL BUREAU OF INVESTIGATION - File #91E-NYC-323571"
        tags = extract_source_tags(text)
        assert "fbi" in tags
    
    def test_court_source(self):
        text = "United States District Court - Case No. 1:15-cv-07433"
        tags = extract_source_tags(text)
        assert "court" in tags
    
    def test_deposition_source(self):
        text = "DEPOSITION OF JOHN DOE\n\nQ: State your name.\nA: John Doe."
        tags = extract_source_tags(text)
        assert "deposition" in tags
    
    def test_subpoena_source(self):
        text = "SUBPOENA - You are hereby commanded to appear and testify."
        tags = extract_source_tags(text)
        assert "subpoena" in tags
    
    def test_evidence_photo_source(self):
        text = "Evidence photo EFTA00012345 taken at scene."
        tags = extract_source_tags(text)
        assert "evidence-photo" in tags
    
    def test_flight_log_source(self):
        text = "Flight log for aircraft N908JE on July 11, 1998."
        tags = extract_source_tags(text)
        assert "flight-log" in tags
    
    def test_category_fallback(self):
        # If category is pre-classified, use it
        tags = extract_source_tags("Generic text", category="fbi-document")
        assert "fbi" in tags


class TestDateRangeTags:
    """Test date range (decade) tagging."""
    
    def test_1990s_extraction(self):
        text = "Event occurred in 1995 and continued through 1998."
        tags = extract_date_range_tags(text)
        assert "1990s" in tags
    
    def test_2000s_extraction(self):
        text = "Between 2000 and 2005, multiple incidents occurred."
        tags = extract_date_range_tags(text)
        assert "2000s" in tags
    
    def test_2010s_extraction(self):
        text = "Investigation began in 2015 and concluded in 2019."
        tags = extract_date_range_tags(text)
        assert "2010s" in tags
    
    def test_2020s_extraction(self):
        text = "Document released in 2024."
        tags = extract_date_range_tags(text)
        assert "2020s" in tags
    
    def test_multiple_decades(self):
        text = "Events from 1998, 2005, and 2015."
        tags = extract_date_range_tags(text)
        assert "1990s" in tags
        assert "2000s" in tags
        assert "2010s" in tags
    
    def test_release_date_fallback(self):
        text = "No dates in text."
        tags = extract_date_range_tags(text, release_date="2019-08-12")
        assert "2010s" in tags
    
    def test_no_dates(self):
        text = "No dates or years mentioned."
        tags = extract_date_range_tags(text)
        assert len(tags) == 0


class TestPersonTags:
    """Test person name tagging."""
    
    def test_single_person(self):
        tags = extract_person_tags(["Jeffrey Epstein"])
        assert "person:jeffrey-epstein" in tags
    
    def test_multiple_people(self):
        tags = extract_person_tags(["Jeffrey Epstein", "Ghislaine Maxwell"])
        assert "person:jeffrey-epstein" in tags
        assert "person:ghislaine-maxwell" in tags
    
    def test_normalization(self):
        # Test lowercase and hyphenation
        tags = extract_person_tags(["Virginia Roberts Giuffre"])
        assert "person:virginia-roberts-giuffre" in tags
    
    def test_special_characters_removed(self):
        tags = extract_person_tags(["Jean-Luc Brunel"])
        assert "person:jean-luc-brunel" in tags
    
    def test_empty_list(self):
        tags = extract_person_tags([])
        assert len(tags) == 0


class TestLocationTags:
    """Test location tagging."""
    
    def test_single_location(self):
        tags = extract_location_tags(["Little St. James Island"])
        assert "location:little-st-james-island" in tags
    
    def test_multiple_locations(self):
        tags = extract_location_tags(["New York", "Palm Beach"])
        assert "location:new-york" in tags
        assert "location:palm-beach" in tags
    
    def test_normalization(self):
        tags = extract_location_tags(["New York, NY"])
        assert "location:new-york-ny" in tags
    
    def test_special_characters_removed(self):
        tags = extract_location_tags(["Saint-Tropez"])
        assert "location:saint-tropez" in tags
    
    def test_empty_list(self):
        tags = extract_location_tags([])
        assert len(tags) == 0


class TestGenerateAutoTags:
    """Test comprehensive auto-tag generation."""
    
    def test_flight_log_document(self):
        text = """
        FLIGHT LOG - Aircraft N908JE
        Date: July 11, 1998
        Passengers: Jeffrey Epstein, Ghislaine Maxwell
        Departure: Palm Beach, FL
        Arrival: Little St. James Island
        """
        tags = generate_auto_tags(
            text=text,
            person_names=["Jeffrey Epstein", "Ghislaine Maxwell"],
            locations=["Palm Beach", "Little St. James Island"],
            release_date="2019-08-12"
        )
        
        # Should have keywords, sources, dates, people, locations
        assert "flight" in tags
        assert "flight-log" in tags
        assert "1990s" in tags
        assert "2010s" in tags  # From release date
        assert "person:jeffrey-epstein" in tags
        assert "person:ghislaine-maxwell" in tags
        assert "location:palm-beach" in tags
        assert "location:little-st-james-island" in tags
    
    def test_fbi_report_document(self):
        text = """
        FEDERAL BUREAU OF INVESTIGATION
        File #91E-NYC-323571
        
        Investigation into trafficking allegations.
        Witness statements and evidence photographs.
        """
        tags = generate_auto_tags(
            text=text,
            category="fbi-report",
            release_date="2019-08-12"
        )
        
        assert "fbi" in tags
        assert "investigation" in tags
        assert "witness" in tags
        assert "evidence" in tags
        assert "2010s" in tags
    
    def test_court_deposition(self):
        text = """
        UNITED STATES DISTRICT COURT
        DEPOSITION OF VIRGINIA GIUFFRE
        
        Q: State your name.
        A: Virginia Giuffre.
        
        Q: When did you meet Jeffrey Epstein?
        A: In 2000.
        """
        tags = generate_auto_tags(
            text=text,
            person_names=["Virginia Giuffre"],
            release_date="2019-08-12"
        )
        
        assert "court" in tags
        assert "deposition" in tags
        assert "witness" in tags
        assert "2000s" in tags
        assert "person:virginia-giuffre" in tags
    
    def test_empty_text(self):
        tags = generate_auto_tags(text="", release_date="2019-08-12")
        # Should at least have decade from release date
        assert "2010s" in tags
    
    def test_sorted_output(self):
        tags = generate_auto_tags(
            text="Flight witness victim",
            release_date="2019-08-12"
        )
        # Verify output is sorted
        assert tags == sorted(tags)


class TestTagSummary:
    """Test tag organization and summary."""
    
    def test_organize_by_category(self):
        tags = [
            "flight", "victim",  # keywords
            "fbi", "court",  # sources
            "person:jeffrey-epstein", "person:ghislaine-maxwell",  # people
            "location:new-york", "location:palm-beach",  # locations
            "1990s", "2000s",  # decades
        ]
        
        summary = tag_summary(tags)
        
        assert "flight" in summary["keywords"]
        assert "victim" in summary["keywords"]
        assert "fbi" in summary["sources"]
        assert "court" in summary["sources"]
        assert "jeffrey-epstein" in summary["people"]
        assert "ghislaine-maxwell" in summary["people"]
        assert "new-york" in summary["locations"]
        assert "palm-beach" in summary["locations"]
        assert "1990s" in summary["decades"]
        assert "2000s" in summary["decades"]
    
    def test_person_prefix_stripped(self):
        tags = ["person:john-doe"]
        summary = tag_summary(tags)
        assert "john-doe" in summary["people"]
        assert "person:john-doe" not in summary["people"]
    
    def test_location_prefix_stripped(self):
        tags = ["location:new-york"]
        summary = tag_summary(tags)
        assert "new-york" in summary["locations"]
        assert "location:new-york" not in summary["locations"]
    
    def test_empty_tags(self):
        summary = tag_summary([])
        assert summary["keywords"] == []
        assert summary["sources"] == []
        assert summary["people"] == []
        assert summary["locations"] == []
        assert summary["decades"] == []


class TestIntegration:
    """Integration tests for real-world scenarios."""
    
    def test_comprehensive_document(self):
        """Test a document with all tag types."""
        text = """
        FEDERAL BUREAU OF INVESTIGATION
        Case #91E-NYC-323571
        
        DEPOSITION - Flight Log Analysis
        Date: August 12, 2019
        
        Investigation into trafficking allegations involving minor victims.
        Evidence photographs from Little St. James Island, Virgin Islands.
        Witness testimony from Virginia Giuffre regarding events in 1998, 2001, and 2015.
        
        Financial records show wire transfers from offshore accounts.
        Court subpoena issued for additional documents.
        """
        
        tags = generate_auto_tags(
            text=text,
            person_names=["Virginia Giuffre"],
            locations=["Little St. James Island", "Virgin Islands"],
            release_date="2019-08-12"
        )
        
        # Verify we have tags from all categories
        summary = tag_summary(tags)
        assert len(summary["keywords"]) > 0
        assert len(summary["sources"]) > 0
        assert len(summary["people"]) > 0
        assert len(summary["locations"]) > 0
        assert len(summary["decades"]) > 0
        
        # Verify specific important tags
        assert any("fbi" in tag for tag in tags)
        assert any("witness" in tag for tag in tags)
        assert any("victim" in tag for tag in tags)
        assert any("1990s" in tag for tag in tags)
        assert any("2010s" in tag for tag in tags)
