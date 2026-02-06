"""Integration test for complete remediation workflow.

Tests end-to-end flow: error generation → message output → command reception → 
orchestration → agent execution.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path

from src.agents.error_generator import ErrorGeneratorAgent
from src.agents.orchestrator import OrchestratorAgent
from src.agents.config_agent import ConfigAgent
from src.agents.os_agent import OSAgent
from src.agents.restart_agent import RestartAgent
from src.models.error_message import ErrorGenerationRequest
from src.models.remediation_command import RemediationCommand
from src.services.message_sender import MessageSenderService
from src.services.command_receiver import CommandReceiverService


class TestCompleteRemediationWorkflow:
    """Integration tests for complete remediation workflow."""
    
    @pytest.fixture
    def sample_cpf(self, tmp_path):
        """Create sample CPF file for testing."""
        cpf = tmp_path / "test_iris.cpf"
        cpf.write_text("""[Startup]
globals=15000
routines=10000

[config]
test_setting=original_value
""")
        return cpf
    
    @patch("requests.post")
    def test_error_to_output_workflow(self, mock_post, tmp_path):
        """Test error generation and transmission workflow."""
        # Setup
        log_file = tmp_path / "test.log"
        log_file.write_text("01/15/24-10:23:45:123 (1234) 2 [License] Test error\n")
        
        error_agent = ErrorGeneratorAgent(log_samples_path=log_file)
        sender = MessageSenderService(output_endpoint="http://test/api")
        
        # Mock successful HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Generate and send
        request = ErrorGenerationRequest(error_category="license", severity=2)
        error = error_agent.generate_error(request)
        result = sender.send_message(error)
        
        # Verify
        assert result["status"] == "sent"
        mock_post.assert_called_once()
    
    def test_command_to_execution_workflow(self, sample_cpf):
        """Test command reception, orchestration, and execution workflow."""
        # Setup
        receiver = CommandReceiverService()
        orchestrator = OrchestratorAgent()
        config_agent = ConfigAgent(cpf_path=sample_cpf)
        
        # Receive command
        command = RemediationCommand(
            action_type="config_change",
            target="iris.cpf",
            parameters={"section": "Startup", "key": "globals", "value": "20000"}
        )
        
        receive_result = receiver.receive_command(command.model_dump_json())
        assert receive_result["status"] == "queued"
        
        # Get next command
        next_cmd = receiver.get_next_command()
        assert next_cmd is not None
        
        # Route to agent
        routing = orchestrator.route_command(next_cmd)
        assert routing.agent_type == "config"
        
        # Execute with config agent
        execution_result = config_agent.modify_config(
            section="Startup",
            key="globals",
            value="20000"
        )
        
        # Verify execution
        assert execution_result.success
        assert execution_result.old_value == "15000"
        assert execution_result.new_value == "20000"
    
    def test_multi_agent_workflow(self, sample_cpf):
        """Test workflow with multiple agents handling different commands."""
        commands = [
            RemediationCommand(
                action_type="config_change",
                target="iris.cpf",
                parameters={"section": "config", "key": "test_setting", "value": "new_value"},
                priority="high"
            ),
            RemediationCommand(
                action_type="restart",
                target="instance",
                parameters={"mode": "graceful", "timeout_seconds": 60},
                priority="low"
            )
        ]
        
        receiver = CommandReceiverService()
        orchestrator = OrchestratorAgent()
        config_agent = ConfigAgent(cpf_path=sample_cpf)
        restart_agent = RestartAgent()
        
        # Queue all commands
        for cmd in commands:
            receiver.receive_command(cmd.model_dump_json())
        
        # Process commands in priority order
        results = []
        while True:
            cmd = receiver.get_next_command()
            if cmd is None:
                break
            
            # Route
            routing = orchestrator.route_command(cmd)
            
            # Execute appropriate agent
            if routing.agent_type == "config":
                result = config_agent.execute(cmd.model_dump_json())
            elif routing.agent_type == "restart":
                result = restart_agent.execute(cmd.model_dump_json())
            else:
                pytest.fail(f"Unexpected agent type: {routing.agent_type}")
            
            results.append((routing.agent_type, result))
        
        # Verify
        assert len(results) == 2
        # Config should execute first (higher priority)
        assert results[0][0] == "config"
        assert results[1][0] == "restart"
    
    @patch("requests.post")
    def test_error_simulation_loop(self, mock_post, tmp_path):
        """Test continuous error generation and transmission."""
        # Setup
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "01/15/24-10:23:45:123 (1234) 2 [License] Test error 1\n"
            "01/15/24-10:23:46:456 (5678) 1 [Config] Test error 2\n"
        )
        
        error_agent = ErrorGeneratorAgent(log_samples_path=log_file)
        sender = MessageSenderService(output_endpoint="http://test/api")
        
        # Mock HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Generate multiple errors
        categories = ["license", "config", "os", "journal"]
        sent_count = 0
        
        for category in categories:
            request = ErrorGenerationRequest(error_category=category, severity=2)
            error = error_agent.generate_error(request)
            result = sender.send_message(error)
            
            if result["status"] == "sent":
                sent_count += 1
        
        # Verify
        assert sent_count == len(categories)
        assert mock_post.call_count == len(categories)
    
    def test_agent_coordination_with_restart(self, sample_cpf):
        """Test coordination between config changes and restart requirements."""
        config_agent = ConfigAgent(cpf_path=sample_cpf)
        restart_agent = RestartAgent()
        
        # Make config change that requires restart
        config_result = config_agent.modify_config(
            section="Startup",
            key="globals",
            value="25000"
        )
        
        assert config_result.success
        
        # If restart required, execute restart
        if config_result.requires_restart:
            restart_result = restart_agent.restart_instance(
                mode="graceful",
                timeout_seconds=60
            )
            
            # Note: restart will show simulated success
            # In real system, would verify instance restarted with new config
            assert restart_result.mode == "graceful"
    
    def test_observability_across_workflow(self, tmp_path, sample_cpf):
        """Test that trace IDs and observability work across workflow."""
        from src.utils.logger import set_trace_id, get_trace_id
        
        # Set trace ID
        trace_id = "test-workflow-123"
        set_trace_id(trace_id)
        
        # Execute workflow
        log_file = tmp_path / "test.log"
        log_file.write_text("01/15/24-10:23:45:123 (1234) 2 [License] Test\n")
        
        error_agent = ErrorGeneratorAgent(log_samples_path=log_file)
        config_agent = ConfigAgent(cpf_path=sample_cpf)
        
        # Generate error (should use trace ID)
        request = ErrorGenerationRequest(error_category="license", severity=2)
        error_agent.generate_error(request)
        
        # Execute config change (should use same trace ID)
        config_agent.modify_config(
            section="config",
            key="test_setting",
            value="traced_value"
        )
        
        # Verify trace ID is still set
        assert get_trace_id() == trace_id
        
        # Check agent stats
        error_stats = error_agent.get_stats()
        config_stats = config_agent.get_stats()
        
        assert error_stats["total_executions"] >= 1
        assert config_stats["total_executions"] >= 1
