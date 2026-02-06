"""Remediation command data models.

Pydantic models for remediation commands from external systems.
"""

from typing import Any, Dict, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class RemediationCommand(BaseModel):
    """Remediation command received from external system in JSON format.
    
    Example:
    {
        "command_id": "550e8400-e29b-41d4-a716-446655440000",
        "action_type": "config_change",
        "target": "iris.cpf",
        "parameters": {
            "section": "Startup",
            "key": "globals",
            "value": "20000"
        },
        "priority": "high"
    }
    """
    command_id: UUID = Field(
        default_factory=uuid4,
        description="Unique command identifier"
    )
    action_type: Literal["config_change", "os_reconfig", "restart"] = Field(
        description="Type of remediation action"
    )
    target: str = Field(
        description="Target resource (e.g., 'iris.cpf', 'hugepages', 'instance')",
        min_length=1,
        max_length=100
    )
    parameters: Dict[str, Any] = Field(
        description="Action-specific parameters"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Execution priority"
    )
    requester: Optional[str] = Field(
        default=None,
        description="Identity of requesting system"
    )
    
    @field_validator('parameters')
    @classmethod
    def validate_parameters_by_action(cls, v: Dict, info) -> Dict:
        """Validate parameters match action_type requirements."""
        action_type = info.data.get('action_type')
        
        if action_type == "config_change":
            required = {"section", "key", "value"}
            if not required.issubset(v.keys()):
                raise ValueError(f"config_change requires: {required}")
        
        elif action_type == "os_reconfig":
            required = {"resource_type", "target_value"}
            if not required.issubset(v.keys()):
                raise ValueError(f"os_reconfig requires: {required}")
        
        elif action_type == "restart":
            if "mode" in v and v["mode"] not in ["graceful", "forced"]:
                raise ValueError("restart mode must be 'graceful' or 'forced'")
        
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "command_id": "550e8400-e29b-41d4-a716-446655440000",
                    "action_type": "config_change",
                    "target": "iris.cpf",
                    "parameters": {
                        "section": "Startup",
                        "key": "globals",
                        "value": "20000"
                    },
                    "priority": "high",
                    "requester": "monitoring-system"
                },
                {
                    "command_id": "550e8400-e29b-41d4-a716-446655440001",
                    "action_type": "os_reconfig",
                    "target": "hugepages",
                    "parameters": {
                        "resource_type": "memory",
                        "target_value": 16384
                    },
                    "priority": "medium"
                },
                {
                    "command_id": "550e8400-e29b-41d4-a716-446655440002",
                    "action_type": "restart",
                    "target": "instance",
                    "parameters": {
                        "mode": "graceful",
                        "timeout_seconds": 60
                    },
                    "priority": "high"
                }
            ]
        }
