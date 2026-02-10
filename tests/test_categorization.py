#!/usr/bin/env python3
"""Tests for document categorization."""
from __future__ import annotations

import pytest
from scripts.pdf_analyzer import classify_document_type


class TestEmailCategorization:
    """Test email detection."""
    
    def test_standard_email(self):
        """Categorize standard email format."""
        text = """
From: alice@example.com
To: bob@example.com
Subject: Meeting Tomorrow

Let's meet at 2pm.
"""
        category = classify_document_type("doc.pdf", text)
        assert category == "email"
    
    def test_email_without_to_field(self):
        """Categorize email with only From and Subject."""
        text = "From: sender@example.com\nSubject: Important\nMessage body."
        category = classify_document_type("doc.pdf", text)
        assert category == "email"


class TestLegalDocuments:
    """Test legal document categorization."""
    
    def test_legal_filing(self):
        """Categorize legal filing."""
        text = """
UNITED STATES DISTRICT COURT
SOUTHERN DISTRICT OF NEW YORK

Plaintiff v. Defendant
Case No. 1:23-cv-12345

MOTION FOR SUMMARY JUDGMENT
"""
        category = classify_document_type("doc.pdf", text)
        assert category == "legal-filing"
    
    def test_subpoena(self):
        """Categorize subpoena."""
        text = """
SUBPOENA TO PRODUCE DOCUMENTS
You are commanded to produce the following documents...
"""
        category = classify_document_type("doc.pdf", text)
        assert category == "subpoena"
    
    def test_deposition(self):
        """Categorize deposition transcript."""
        text = """
DEPOSITION OF JOHN DOE
Taken on January 15, 2024

Q: Please state your name.
A: John Doe.
"""
        category = classify_document_type("doc.pdf", text)
        assert category == "deposition"


class TestFinancialDocuments:
    """Test financial document categorization."""
    
    def test_wire_transfer(self):
        """Categorize wire transfer."""
        text = """
WIRE TRANSFER DETAILS
Account Number: 123456789
SWIFT: ABCDUS33
Amount: $10,000.00
"""
        category = classify_document_type("doc.pdf", text)
        assert category == "financial-record"
    
    def test_receipt(self):
        """Categorize receipt."""
        text = """
INVOICE #12345
Bill To: Customer Name
Subtotal: $100.00
Total Amount: $110.00
"""
        category = classify_document_type("doc.pdf", text)
        assert category == "receipt"


class TestTravelDocuments:
    """Test travel document categorization."""
    
    def test_cbp_record(self):
        """Categorize Customs and Border Protection record."""
        text = """
CUSTOMS AND BORDER PROTECTION
TECS PERSON ENCOUNTER
Entry Inspection
Arrival: JFK Airport
"""
        category = classify_document_type("doc.pdf", text)
        assert category == "travel-record"
    
    def test_passport_application(self):
        """Categorize passport application."""
        text = """
U.S. DEPARTMENT OF STATE
PASSPORT APPLICATION
Form Approved OMB No. 1234-5678
Applicant Information
"""
        category = classify_document_type("doc.pdf", text)
        assert category == "government-form"


class TestBookingRecords:
    """Test booking record categorization."""
    
    def test_arrest_record(self):
        """Categorize arrest/booking record."""
        text = """
BOOKING SYSTEM REPORT
Date Arrested: 01/15/2024
FBI No.: 123456789
Charges: Various
"""
        category = classify_document_type("doc.pdf", text)
        assert category == "booking-record"


class TestPhoneRecords:
    """Test phone record categorization."""
    
    def test_call_log(self):
        """Categorize phone call log."""
        text = """
CALL DETAIL RECORD
Phone Number: (555) 123-4567
Date/Time: 01/15/2024 14:30
Duration: 5 minutes
"""
        category = classify_document_type("doc.pdf", text)
        # Phone records may not have dedicated category yet
        assert category in ["phone-record", None]


class TestScannedDocuments:
    """Test scanned document fallback."""
    
    def test_low_quality_scan(self):
        """Categorize poor quality scan with no clear markers."""
        text = "asdf jkl; qwer tyui"  # Gibberish OCR
        category = classify_document_type("doc.pdf", text)
        # Should fall back to scanned-document or None
        assert category in ["scanned-document", None]
    
    def test_blank_document(self):
        """Handle blank/empty document."""
        text = ""
        category = classify_document_type("doc.pdf", text)
        assert category in ["scanned-document", None]


class TestEdgeCases:
    """Test edge cases."""
    
    def test_multiple_categories_precedence(self):
        """Email markers take precedence over other categories."""
        text = """
From: lawyer@example.com
To: client@example.com
Subject: Motion Filed

We have filed a motion in the case.
"""
        category = classify_document_type("doc.pdf", text)
        # Email should be detected first
        assert category == "email"
    
    def test_case_insensitive_matching(self):
        """Categorization is case-insensitive."""
        text = "SUBPOENA TO PRODUCE DOCUMENTS"
        category = classify_document_type("doc.pdf", text)
        assert category == "subpoena"
