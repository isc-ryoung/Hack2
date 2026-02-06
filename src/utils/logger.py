"""Structured logging setup with trace ID support.

This module configures structlog for JSON output with contextvars-based
trace ID propagation for correlation across agent operations.
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any, Dict, Optional
from uuid import uuid4

import structlog


# Context variable for trace ID propagation
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


def get_trace_id() -> str:
    """Get current trace ID or generate a new one."""
    trace_id = trace_id_var.get()
    if trace_id is None:
        trace_id = str(uuid4())
        trace_id_var.set(trace_id)
    return trace_id


def set_trace_id(trace_id: str) -> None:
    """Set trace ID for current context."""
    trace_id_var.set(trace_id)


def clear_trace_id() -> None:
    """Clear trace ID from current context."""
    trace_id_var.set(None)


def add_trace_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Processor to add trace ID to log entries."""
    trace_id = trace_id_var.get()
    if trace_id:
        event_dict['trace_id'] = trace_id
    return event_dict


def configure_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Output format ('json' or 'console')
    """
    # Set up stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        add_trace_id,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    # Add appropriate renderer based on format
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def sanitize_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive data from log entries.
    
    Args:
        data: Dictionary potentially containing sensitive data
        
    Returns:
        Sanitized dictionary
    """
    sensitive_keys = {
        'api_key', 'password', 'token', 'secret', 'authorization',
        'OPENAI_API_KEY', 'API_KEY'
    }
    
    sanitized = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in ['key', 'password', 'token', 'secret']):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_sensitive_data(value)
        else:
            sanitized[key] = value
    
    return sanitized
