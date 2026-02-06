"""Agent response models for structured outputs."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class OrchestratorResponse(BaseModel):
    """Response from OrchestratorAgent after analyzing command."""
    agent_type: Literal["config", "os", "restart", "none"] = Field(
        description="Which agent should handle this command"
    )
    command_str: str = Field(
        description="Serialized command to pass to selected agent"
    )
    rationale: str = Field(
        description="Explanation of agent selection decision"
    )
    requires_validation: bool = Field(
        description="Whether pre-execution validation needed"
    )
    estimated_risk: Literal["low", "medium", "high"] = Field(
        description="Risk assessment for operation"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [{
                "agent_type": "config",
                "command_str": '{"section": "Startup", "key": "globals", "value": "20000"}',
                "rationale": "Command modifies IRIS CPF configuration parameter 'globals'",
                "requires_validation": True,
                "estimated_risk": "medium"
            }]
        }


class ConfigAgentResponse(BaseModel):
    """Response from ConfigAgent after configuration change."""
    success: bool = Field(description="Whether operation succeeded")
    section: str = Field(description="CPF section modified")
    key: str = Field(description="Configuration key modified")
    old_value: Optional[str] = Field(description="Previous value")
    new_value: str = Field(description="New value")
    requires_restart: bool = Field(description="Whether IRIS restart required")
    backup_path: Optional[str] = Field(description="Path to CPF backup file")
    error_message: Optional[str] = Field(default=None, description="Error details if failed")
    
    class Config:
        json_schema_extra = {
            "examples": [{
                "success": True,
                "section": "Startup",
                "key": "globals",
                "old_value": "10000",
                "new_value": "20000",
                "requires_restart": True,
                "backup_path": "/usr/irissys/iris.cpf.backup.20260206",
                "error_message": None
            }]
        }


class OSAgentResponse(BaseModel):
    """Response from OSAgent after OS reconfiguration."""
    success: bool = Field(description="Whether operation succeeded")
    resource_type: str = Field(description="Resource type modified (memory, cpu)")
    target_value: int = Field(description="Target resource value")
    actual_value: Optional[int] = Field(description="Actual value after change")
    commands_executed: list[str] = Field(description="OS commands that were executed")
    validation_passed: bool = Field(description="Whether post-change validation passed")
    error_message: Optional[str] = Field(default=None, description="Error details if failed")
    
    class Config:
        json_schema_extra = {
            "examples": [{
                "success": True,
                "resource_type": "memory",
                "target_value": 16384,
                "actual_value": 16384,
                "commands_executed": ["echo 8192 > /proc/sys/vm/nr_hugepages"],
                "validation_passed": True,
                "error_message": None
            }]
        }


class RestartAgentResponse(BaseModel):
    """Response from RestartAgent after restart operation."""
    success: bool = Field(description="Whether restart succeeded")
    restart_mode: Literal["graceful", "forced"] = Field(description="Restart mode used")
    connections_drained: int = Field(description="Number of connections drained")
    shutdown_duration_seconds: float = Field(description="Time taken for shutdown")
    startup_duration_seconds: float = Field(description="Time taken for startup")
    instance_status: Literal["running", "stopped", "failed"] = Field(
        description="Final instance status"
    )
    validation_passed: bool = Field(description="Whether post-startup validation passed")
    error_message: Optional[str] = Field(default=None, description="Error details if failed")
    
    class Config:
        json_schema_extra = {
            "examples": [{
                "success": True,
                "restart_mode": "graceful",
                "connections_drained": 5,
                "shutdown_duration_seconds": 12.5,
                "startup_duration_seconds": 8.3,
                "instance_status": "running",
                "validation_passed": True,
                "error_message": None
            }]
        }
