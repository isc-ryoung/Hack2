"""Unit tests for logger setup and trace ID propagation."""

import pytest
from src.utils.logger import (
    configure_logging,
    get_logger,
    get_trace_id,
    set_trace_id,
    clear_trace_id,
    sanitize_sensitive_data,
)


def test_configure_logging():
    """Test logging configuration."""
    configure_logging(log_level="INFO", log_format="json")
    logger = get_logger("test")
    assert logger is not None


def test_trace_id_management():
    """Test trace ID set/get/clear."""
    # Clear any existing trace ID
    clear_trace_id()
    
    # Generate new trace ID
    trace_id1 = get_trace_id()
    assert trace_id1 is not None
    assert len(trace_id1) > 0
    
    # Set custom trace ID
    custom_id = "test-trace-123"
    set_trace_id(custom_id)
    assert get_trace_id() == custom_id
    
    # Clear trace ID
    clear_trace_id()
    # After clear, get should generate a new one
    trace_id2 = get_trace_id()
    assert trace_id2 != custom_id


def test_sanitize_sensitive_data():
    """Test sensitive data sanitization."""
    data = {
        "api_key": "secret-key-123",
        "username": "user",
        "password": "secret-pass",
        "nested": {
            "token": "secret-token",
            "value": "safe-value"
        }
    }
    
    sanitized = sanitize_sensitive_data(data)
    
    assert sanitized["api_key"] == "***REDACTED***"
    assert sanitized["password"] == "***REDACTED***"
    assert sanitized["username"] == "user"  # Not sensitive
    assert sanitized["nested"]["token"] == "***REDACTED***"
    assert sanitized["nested"]["value"] == "safe-value"


def test_get_logger():
    """Test logger creation."""
    logger = get_logger("test_module")
    assert logger is not None
    
    # Test logging doesn't raise errors
    logger.info("test_message", key="value")
