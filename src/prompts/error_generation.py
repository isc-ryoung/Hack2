"""Error generation prompts for LLM-powered error message creation."""

from typing import List
from src.models.error_message import ErrorMessage


def create_error_generation_prompt(
    error_category: str,
    severity: int,
    examples: List[ErrorMessage],
    context: str = ""
) -> str:
    """Create prompt for error message generation.
    
    Args:
        error_category: Type of error (config, license, os, journal)
        severity: Severity level (0-3)
        examples: Example error messages from log parsing
        context: Additional context
        
    Returns:
        Formatted prompt string
    """
    examples_text = ""
    if examples:
        examples_text = "\n\nExample IRIS error messages from actual logs:\n"
        for ex in examples[:3]:  # Limit to 3 examples
            examples_text += f"- {ex.to_log_format()}\n"
    
    category_descriptions = {
        "license": "License Management Facility (LMF) errors - missing keys, expiration, validation failures",
        "config": "Configuration parameter errors - CPF file issues, invalid settings, startup problems",
        "os": "Operating system resource errors - memory allocation, shared memory, CPU constraints",
        "journal": "Journal system errors - Write-Image Journal (WIJ) issues, locking, directory permissions"
    }
    
    severity_descriptions = {
        0: "Informational (0) - normal operations, successful completions",
        1: "Warning (1) - potential issues that don't prevent operation",
        2: "Error (2) - failures that impact functionality",
        3: "Fatal (3) - critical failures that prevent system operation"
    }
    
    prompt = f"""Generate a realistic InterSystems IRIS database error message.

Error Category: {error_category}
Description: {category_descriptions.get(error_category, 'General error')}

Severity Level: {severity}
Description: {severity_descriptions.get(severity, 'Unknown severity')}

{f'Context: {context}' if context else ''}

{examples_text}

Requirements:
1. Match IRIS messages.log format exactly
2. Use realistic technical terminology for IRIS systems
3. Timestamp format: MM/DD/YY-HH:MM:SS:mmm (use current date 02/06/26)
4. Process ID: random 5-6 digit number
5. Category tag: appropriate [Category.Subcategory] format
6. Message text: technically accurate,10-100 words

Generate ONE error message that matches the specified category and severity."""
    
    return prompt


# Fallback regex templates for when LLM is unavailable
FALLBACK_TEMPLATES = {
    "license": [
        "LMF Error: No valid license key. No valid local file found.",
        "License expiration in 30 days. Renew license to avoid service interruption.",
        "License validation failed: key signature mismatch"
    ],
    "config": [
        "Configuration parameter 'globals' value exceeds recommended maximum",
        "CPF file parsing error in section [Startup]",
        "Invalid configuration: routine buffer size must be positive integer"
    ],
    "os": [
        "Shared memory allocation failed: insufficient system resources",
        "Global buffer setting may be too low for optimal performance",
        "Insufficient shared memory for requested global buffers"
    ],
    "journal": [
        "Journal write-image file lock failed, permission denied",
        "Journal directory space low, 10% remaining",
        "WIJ file corruption detected, recovery required"
    ]
}
