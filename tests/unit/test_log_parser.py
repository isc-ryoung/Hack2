"""Unit tests for log parser with sample log file."""

import pytest
from pathlib import Path
from src.services.log_parser import LogParser
from src.models.error_message import ErrorMessage


def test_log_parser_initialization():
    """Test log parser initialization."""
    parser = LogParser()
    assert parser.total_entries == 0
    assert len(parser.patterns) == 0


def test_parse_log_line_valid():
    """Test parsing a valid log line."""
    parser = LogParser()
    line = "02/06/26-14:30:45:123 (12345) 2 [Utility.Event] LMF Error: No valid license key"
    
    entry = parser.parse_line(line)
    
    assert entry is not None
    assert entry.timestamp == "02/06/26-14:30:45:123"
    assert entry.process_id == 12345
    assert entry.severity == 2
    assert entry.category == "[Utility.Event]"
    assert "license key" in entry.message_text


def test_parse_log_line_invalid():
    """Test parsing an invalid log line."""
    parser = LogParser()
    line = "This is not a valid IRIS log line"
    
    entry = parser.parse_line(line)
    assert entry is None


def test_categorize_license_error():
    """Test categorization of license errors."""
    parser = LogParser()
    entry = ErrorMessage(
        timestamp="02/06/26-14:30:45:123",
        process_id=12345,
        severity=2,
        category="[Utility.Event]",
        message_text="LMF Error: No valid license key"
    )
    
    category = parser._categorize_error(entry)
    assert category == "license"


def test_categorize_config_error():
    """Test categorization of config errors."""
    parser = LogParser()
    entry = ErrorMessage(
        timestamp="02/06/26-14:30:45:123",
        process_id=12345,
        severity=2,
        category="[Generic.Event]",
        message_text="Configuration parameter globals is invalid"
    )
    
    category = parser._categorize_error(entry)
    assert category == "config"


def test_categorize_os_error():
    """Test categorization of OS resource errors."""
    parser = LogParser()
    entry = ErrorMessage(
        timestamp="02/06/26-14:30:45:123",
        process_id=12345,
        severity=2,
        category="[Database]",
        message_text="Shared memory allocation failed"
    )
    
    category = parser._categorize_error(entry)
    assert category == "os"


def test_categorize_journal_error():
    """Test categorization of journal errors."""
    parser = LogParser()
    entry = ErrorMessage(
        timestamp="02/06/26-14:30:45:123",
        process_id=12345,
        severity=3,
        category="[WriteDaemon]",
        message_text="Journal write-image file lock failed"
    )
    
    category = parser._categorize_error(entry)
    assert category == "journal"


def test_get_examples():
    """Test getting examples for a category."""
    parser = LogParser()
    parser.patterns["license"] = [
        ErrorMessage(
            timestamp="02/06/26-14:30:45:123",
            process_id=12345,
            severity=2,
            category="[Utility.Event]",
            message_text="LMF Error 1"
        ),
        ErrorMessage(
            timestamp="02/06/26-14:30:46:123",
            process_id=12346,
            severity=2,
            category="[Utility.Event]",
            message_text="LMF Error 2"
        )
    ]
    
    examples = parser.get_examples("license", count=1)
    assert len(examples) == 1
    assert examples[0].message_text == "LMF Error 1"


def test_get_all_categories():
    """Test getting all categories."""
    parser = LogParser()
    parser.patterns["license"] = []
    parser.patterns["config"] = []
    parser.patterns["os"] = []
    
    categories = parser.get_all_categories()
    assert "license" in categories
    assert "config" in categories
    assert "os" in categories
    assert len(categories) == 3
