"""Unit tests for ErrorMessage model validation."""

import pytest
from pydantic import ValidationError
from src.models.error_message import ErrorMessage, ErrorGenerationRequest


def test_error_message_valid():
    """Test valid ErrorMessage creation."""
    msg = ErrorMessage(
        timestamp="02/06/26-14:30:45:123",
        process_id=12345,
        severity=2,
        category="[Utility.Event]",
        message_text="LMF Error: No valid license key"
    )
    
    assert msg.timestamp == "02/06/26-14:30:45:123"
    assert msg.process_id == 12345
    assert msg.severity == 2
    assert msg.category == "[Utility.Event]"


def test_error_message_to_log_format():
    """Test conversion to IRIS log format."""
    msg = ErrorMessage(
        timestamp="02/06/26-14:30:45:123",
        process_id=12345,
        severity=2,
        category="[Utility.Event]",
        message_text="LMF Error: No valid license key"
    )
    
    log_line = msg.to_log_format()
    expected = "02/06/26-14:30:45:123 (12345) 2 [Utility.Event] LMF Error: No valid license key"
    assert log_line == expected


def test_error_message_invalid_severity():
    """Test invalid severity validation."""
    with pytest.raises(ValidationError):
        ErrorMessage(
            timestamp="02/06/26-14:30:45:123",
            process_id=12345,
            severity=5,  # Invalid: must be 0-3
            category="[Utility.Event]",
            message_text="Test error"
        )


def test_error_message_invalid_category():
    """Test invalid category format."""
    with pytest.raises(ValidationError):
        ErrorMessage(
            timestamp="02/06/26-14:30:45:123",
            process_id=12345,
            severity=2,
            category="Invalid",  # Must be [Category.Subcategory]
            message_text="Test error"
        )


def test_error_generation_request():
    """Test ErrorGenerationRequest model."""
    req = ErrorGenerationRequest(
        error_category="license",
        severity=2
    )
    
    assert req.error_category == "license"
    assert req.severity == 2
    assert req.context == ""


def test_error_generation_request_invalid_category():
    """Test invalid error category."""
    with pytest.raises(ValidationError):
        ErrorGenerationRequest(
            error_category="invalid",  # Must be config, license, os, or journal
            severity=2
        )
