#!/usr/bin/env python3
"""Tests for email metadata extraction."""
from __future__ import annotations

import pytest
from scripts.email_metadata import (
    extract_email_metadata,
    extract_email_address,
    extract_name_from_line,
    is_epstein_email,
)


class TestEmailAddressExtraction:
    """Test email address extraction patterns."""
    
    def test_standard_email(self):
        """Extract standard email address."""
        text = "From: john.doe@example.com"
        assert extract_email_address(text) == "john.doe@example.com"
    
    def test_email_with_plus(self):
        """Extract email with plus addressing."""
        text = "To: user+tag@example.com"
        assert extract_email_address(text) == "user+tag@example.com"
    
    def test_email_in_brackets(self):
        """Extract email from mailto brackets."""
        text = "[mailto:support@example.com]"
        assert extract_email_address(text) == "support@example.com"
    
    def test_no_email(self):
        """Return None when no email found."""
        text = "Some text without email"
        assert extract_email_address(text) is None


class TestNameExtraction:
    """Test name extraction from email headers."""
    
    def test_simple_name(self):
        """Extract simple name."""
        line = "From: John Doe"
        name = extract_name_from_line(line)
        # Function returns cleaned line, not just name part
        assert name is not None
        assert "john" in name.lower() or "doe" in name.lower()
    
    def test_name_with_email(self):
        """Extract name when email present."""
        line = "From: John Doe <john@example.com>"
        name = extract_name_from_line(line)
        assert name is not None
        assert "john" in name.lower()
    
    def test_skip_empty_lines(self):
        """Skip empty or whitespace-only lines."""
        assert extract_name_from_line("") is None
        assert extract_name_from_line("   ") is None
    
    def test_skip_dates(self):
        """Skip lines that are just dates."""
        assert extract_name_from_line("01/15/2024") is None
        assert extract_name_from_line("2024-01-15") is None


class TestEmailMetadataExtraction:
    """Test full email metadata extraction."""
    
    def test_complete_email_headers(self):
        """Extract all fields from complete email."""
        email_text = """
From: alice@example.com
To: bob@example.com
Subject: Test Email
Date: Mon, 15 Jan 2024 10:30:00 -0500

Body text here.
"""
        metadata = extract_email_metadata(email_text)
        assert metadata["from_addr"] == "alice@example.com"
        assert metadata["to_addr"] == "bob@example.com"
        assert metadata["subject"] == "Test Email"
        assert "Jan" in metadata["date"] or "2024" in metadata["date"]
    
    def test_partial_headers(self):
        """Extract available fields from partial headers."""
        email_text = """
From: sender@example.com
Subject: Important Message

No To: field in this email.
"""
        metadata = extract_email_metadata(email_text)
        assert metadata["from_addr"] == "sender@example.com"
        assert metadata["subject"] == "Important Message"
        # to_addr may be None, empty, or placeholder
        assert metadata.get("to_addr") in [None, "", "[Not visible in document]"]
    
    def test_ocr_garbled_email(self):
        """Handle OCR-garbled email text gracefully."""
        email_text = """
From:
[Not visible in document]
To: recipient@example.com
Subject: Test
"""
        metadata = extract_email_metadata(email_text)
        # Should extract what's available
        assert metadata["to_addr"] == "recipient@example.com"
        assert metadata["subject"] == "Test"
    
    def test_no_email_headers(self):
        """Return empty metadata for non-email text."""
        text = "This is just a regular document with no email headers."
        metadata = extract_email_metadata(text)
        # All fields should be None, empty, or placeholder
        from_addr = metadata.get("from_addr")
        to_addr = metadata.get("to_addr")
        subject = metadata.get("subject")
        
        # Accept None, empty string, or "[Not visible in document]" placeholder
        assert from_addr in [None, "", "[Not visible in document]"] or not from_addr
        assert to_addr in [None, "", "[Not visible in document]"] or not to_addr
        assert subject in [None, "", "[Not visible in document]"] or not subject


class TestEpsteinEmailDetection:
    """Test detection of Epstein-related emails."""
    
    def test_epstein_sender(self):
        """Detect email from Epstein."""
        metadata = {"from_addr": "jeffrey@epstein.com"}
        text = "Email content"
        assert is_epstein_email(metadata, text) is True
    
    def test_epstein_recipient(self):
        """Detect email to Epstein."""
        metadata = {"to_addr": "jepstein@example.com"}
        text = "Email content"
        assert is_epstein_email(metadata, text) is True
    
    def test_epstein_in_body(self):
        """Detect Epstein mentioned in email body."""
        metadata = {"from_addr": "other@example.com"}
        text = "Meeting with Jeffrey Epstein scheduled for tomorrow."
        assert is_epstein_email(metadata, text) is True
    
    def test_not_epstein_email(self):
        """Regular email not related to Epstein."""
        metadata = {"from_addr": "alice@example.com", "to_addr": "bob@example.com"}
        text = "Regular business correspondence."
        assert is_epstein_email(metadata, text) is False


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_text(self):
        """Handle empty text gracefully."""
        metadata = extract_email_metadata("")
        assert all(v is None for v in metadata.values())
    
    def test_very_long_text(self):
        """Handle very long email text."""
        email_text = "From: test@example.com\n" + "A" * 100000
        metadata = extract_email_metadata(email_text)
        assert metadata["from_addr"] == "test@example.com"
    
    def test_unicode_in_email(self):
        """Handle unicode characters in email."""
        email_text = "From: josé@example.com\nSubject: Tëst émàil"
        metadata = extract_email_metadata(email_text)
        assert "jos" in metadata["from_addr"].lower()
        assert metadata["subject"] is not None
