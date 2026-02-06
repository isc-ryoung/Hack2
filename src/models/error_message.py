"""Error message data models.

Pydantic models for IRIS error messages with validation and formatting.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ErrorMessage(BaseModel):
    """Represents an IRIS messages.log error entry.
    
    Example format:
    11/14/25-09:45:57:762 (50803) 2 [Generic.Event] Kerberos authentication unavailable
    """
    timestamp: str = Field(
        description="Timestamp in MM/DD/YY-HH:MM:SS:mmm format",
        pattern=r"^\d{2}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}:\d{3}$"
    )
    process_id: int = Field(
        description="IRIS process ID",
        ge=1,
        le=999999
    )
    severity: Literal[0, 1, 2, 3] = Field(
        description="Severity level: 0=info, 1=warning, 2=error, 3=fatal"
    )
    category: str = Field(
        description="Error category tag in [Category.Subcategory] format",
        pattern=r"^\[[\w\.]+\]$"
    )
    message_text: str = Field(
        description="Human-readable error description",
        min_length=10,
        max_length=500
    )
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        """Ensure timestamp matches IRIS format."""
        try:
            # Validate format can be parsed
            parts = v.split('-')
            if len(parts) != 2:
                raise ValueError("Must contain date-time separator")
            date_part, time_part = parts[0], parts[1]
            
            # Validate date part (MM/DD/YY)
            datetime.strptime(date_part, "%m/%d/%y")
            
            # Validate time part (HH:MM:SS:mmm)
            time_components = time_part.split(':')
            if len(time_components) != 4:
                raise ValueError("Time must have HH:MM:SS:mmm format with 4 components")
            
            h, m, s, ms = time_components
            if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59 and 0 <= int(s) <= 59 and len(ms) == 3):
                raise ValueError("Invalid time component values")
            
            return v
        except Exception as e:
            raise ValueError(f"Invalid timestamp format: {v} - {str(e)}")
    
    def to_log_format(self) -> str:
        """Convert to IRIS messages.log line format."""
        return f"{self.timestamp} ({self.process_id}) {self.severity} {self.category} {self.message_text}"
    
    class Config:
        json_schema_extra = {
            "examples": [{
                "timestamp": "02/06/26-14:30:45:123",
                "process_id": 12345,
                "severity": 2,
                "category": "[Utility.Event]",
                "message_text": "LMF Error: No valid license key. No valid local file found."
            }]
        }


class ErrorGenerationRequest(BaseModel):
    """Request to generate an error message."""
    error_category: Literal["config", "license", "os", "journal"] = Field(
        description="Type of error to generate"
    )
    severity: Literal[0, 1, 2, 3] = Field(
        default=2,
        description="Severity level for generated error"
    )
    context: str = Field(
        default="",
        description="Additional context for error generation"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [{
                "error_category": "license",
                "severity": 2,
                "context": "License expiration scenario"
            }]
        }
