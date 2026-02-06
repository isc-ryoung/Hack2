"""Integration test for command reception and orchestration workflow.

Tests the complete flow from command reception to agent routing.
"""

import pytest
from unittest.mock import patch, Mock

from src.agents.orchestrator import OrchestratorAgent
from src.models.remediation_command import RemediationCommand
from src.services.command_receiver import CommandReceiverService


class TestCommandReceptionWorkflow:
    """Integration tests for command reception and orchestration."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator agent."""
        return OrchestratorAgent()
    
    @pytest.fixture
    def command_receiver(self):
        """Create command receiver service."""
        return CommandReceiverService()
    
    def test_config_change_routing(self, orchestrator):
        """Test routing of config_change command."""
        command = RemediationCommand(
            action_type="config_change",
            target="iris.cpf",
            parameters={"section": "Startup", "key": "globals", "value": "20000"}
        )
        
        response = orchestrator.route_command(command)
        
        assert response.agent_type == "config"
        assert response.estimated_risk in ["low", "medium", "high"]
        assert len(response.rationale) > 0
    
    def test_os_reconfig_routing(self, orchestrator):
        """Test routing of os_reconfig command."""
        command = RemediationCommand(
            action_type="os_reconfig",
            target="hugepages",
            parameters={"resource_type": "memory", "target_value": 16384}
        )
        
        response = orchestrator.route_command(command)
        
        assert response.agent_type == "os"
        assert response.estimated_risk in ["low", "medium", "high"]
    
    def test_restart_routing(self, orchestrator):
        """Test routing of restart command."""
        command = RemediationCommand(
            action_type="restart",
            target="instance",
            parameters={"mode": "graceful", "timeout_seconds": 60}
        )
        
        response = orchestrator.route_command(command)
        
        assert response.agent_type == "restart"
        assert response.estimated_risk == "high"
    
    def test_command_validation(self, command_receiver):
        """Test command validation on reception."""
        # Valid command
        valid_cmd = RemediationCommand(
            action_type="config_change",
            target="iris.cpf",
            parameters={"section": "Startup", "key": "globals", "value": "20000"}
        )
        
        result = command_receiver.receive_command(valid_cmd.model_dump_json())
        assert result["status"] == "queued"
        
        # Invalid command (missing parameters)
        invalid_json = '{"action_type": "config_change", "target": "iris.cpf"}'
        result = command_receiver.receive_command(invalid_json)
        assert result["status"] == "error"
        assert "validation" in result["error"].lower()
    
    def test_priority_ordering(self, command_receiver):
        """Test that commands are queued by priority."""
        commands = [
            RemediationCommand(action_type="config_change", target="test1", 
                             parameters={"section": "Startup", "key": "k1", "value": "v1"},
                             priority="low"),
            RemediationCommand(action_type="config_change", target="test2", 
                             parameters={"section": "Startup", "key": "k2", "value": "v2"},
                             priority="critical"),
            RemediationCommand(action_type="config_change", target="test3", 
                             parameters={"section": "Startup", "key": "k3", "value": "v3"},
                             priority="medium"),
        ]
        
        # Queue commands
        for cmd in commands:
            command_receiver.receive_command(cmd.model_dump_json())
        
        # Dequeue and verify order
        first = command_receiver.get_next_command()
        assert first.priority == "critical"
        
        second = command_receiver.get_next_command()
        assert second.priority == "medium"
        
        third = command_receiver.get_next_command()
        assert third.priority == "low"
    
    def test_conflict_detection(self, command_receiver):
        """Test detection of conflicting commands."""
        cmd1 = RemediationCommand(
            action_type="config_change",
            target="iris.cpf",
            parameters={"section": "Startup", "key": "globals", "value": "10000"}
        )
        
        cmd2 = RemediationCommand(
            action_type="config_change",
            target="iris.cpf",
            parameters={"section": "Startup", "key": "globals", "value": "20000"}
        )
        
        # Queue first command
        result1 = command_receiver.receive_command(cmd1.model_dump_json())
        assert result1["status"] == "queued"
        
        # Queue conflicting command
        result2 = command_receiver.receive_command(cmd2.model_dump_json())
        assert result2["status"] == "queued"
        assert "conflicts_with" in result2
        assert len(result2["conflicts_with"]) == 1
    
    @patch("src.utils.llm_client.LLMClient.parse")
    def test_llm_based_routing(self, mock_parse, orchestrator):
        """Test LLM-based agent selection."""
        from src.models.agent_responses import OrchestratorResponse
        
        # Mock LLM response
        mock_response = OrchestratorResponse(
            agent_type="config",
            rationale="This requires configuration file modification",
            requires_validation=True,
            estimated_risk="medium"
        )
        mock_parse.return_value = mock_response
        
        # Route command
        command = RemediationCommand(
            action_type="config_change",
            target="iris.cpf",
            parameters={"section": "Startup", "key": "globals", "value": "20000"}
        )
        
        response = orchestrator.route_command(command)
        
        assert response.agent_type == "config"
        assert "configuration" in response.rationale.lower()
    
    def test_fallback_to_rule_routing(self, orchestrator):
        """Test fallback to rule-based routing when LLM fails."""
        # Patch LLM to fail
        with patch("src.agents.orchestrator.LLMClient") as mock_client:
            mock_client.return_value.parse.side_effect = Exception("LLM unavailable")
            
            # Should fall back to rules
            command = RemediationCommand(
                action_type="os_reconfig",
                target="hugepages",
                parameters={"resource_type": "memory", "target_value": 16384}
            )
            
            response = orchestrator.route_command(command)
            
            # Rule-based routing should still work
            assert response.agent_type == "os"
    
    def test_queue_status_reporting(self, command_receiver):
        """Test queue status reporting."""
        # Queue multiple commands
        commands = [
            RemediationCommand(action_type="config_change", target="t1",
                             parameters={"section": "Startup", "key": "k", "value": "v"},
                             priority="high"),
            RemediationCommand(action_type="restart", target="t2",
                             parameters={"mode": "graceful"},
                             priority="critical"),
            RemediationCommand(action_type="os_reconfig", target="t3",
                             parameters={"resource_type": "memory", "target_value": 1024},
                             priority="medium"),
        ]
        
        for cmd in commands:
            command_receiver.receive_command(cmd.model_dump_json())
        
        # Check status
        status = command_receiver.get_queue_status()
        
        assert status["total_commands"] == 3
        assert status["by_priority"]["high"] == 1
        assert status["by_priority"]["critical"] == 1
        assert status["by_priority"]["medium"] == 1
        assert status["by_action"]["config_change"] == 1
        assert status["by_action"]["restart"] == 1
        assert status["by_action"]["os_reconfig"] == 1
