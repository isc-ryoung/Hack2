"""Unit tests for RemediationCommand model validation."""

import pytest
from pydantic import ValidationError
from src.models.remediation_command import RemediationCommand


def test_remediation_command_config_change():
    """Test valid config_change command."""
    cmd = RemediationCommand(
        action_type="config_change",
        target="iris.cpf",
        parameters={
            "section": "Startup",
            "key": "globals",
            "value": "20000"
        },
        priority="high"
    )
    
    assert cmd.action_type == "config_change"
    assert cmd.target == "iris.cpf"
    assert cmd.parameters["section"] == "Startup"
    assert cmd.priority == "high"
    assert cmd.command_id is not None  # UUID generated


def test_remediation_command_os_reconfig():
    """Test valid os_reconfig command."""
    cmd = RemediationCommand(
        action_type="os_reconfig",
        target="hugepages",
        parameters={
            "resource_type": "memory",
            "target_value": 16384
        }
    )
    
    assert cmd.action_type == "os_reconfig"
    assert cmd.parameters["resource_type"] == "memory"


def test_remediation_command_restart():
    """Test valid restart command."""
    cmd = RemediationCommand(
        action_type="restart",
        target="instance",
        parameters={
            "mode": "graceful",
            "timeout_seconds": 60
        }
    )
    
    assert cmd.action_type == "restart"
    assert cmd.parameters["mode"] == "graceful"


def test_remediation_command_missing_parameters():
    """Test validation fails for missing required parameters."""
    with pytest.raises(ValidationError):
        RemediationCommand(
            action_type="config_change",
            target="iris.cpf",
            parameters={"key": "globals"}  # Missing 'section' and 'value'
        )


def test_remediation_command_invalid_restart_mode():
    """Test validation fails for invalid restart mode."""
    with pytest.raises(ValidationError):
        RemediationCommand(
            action_type="restart",
            target="instance",
            parameters={"mode": "invalid"}  # Must be graceful or forced
        )


def test_remediation_command_json_serialization():
    """Test command can be serialized to/from JSON."""
    cmd = RemediationCommand(
        action_type="config_change",
        target="iris.cpf",
        parameters={
            "section": "Startup",
            "key": "globals",
            "value": "20000"
        }
    )
    
    # Serialize to JSON
    json_str = cmd.model_dump_json()
    assert "config_change" in json_str
    
    # Deserialize from JSON
    cmd2 = RemediationCommand.model_validate_json(json_str)
    assert cmd2.action_type == cmd.action_type
    assert cmd2.command_id == cmd.command_id
