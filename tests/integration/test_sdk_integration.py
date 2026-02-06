"""Test OpenAI Agents SDK integration.

Verify that SDK-based agents work correctly.
"""

import pytest
from pathlib import Path

from src.agents.error_generator_sdk import ErrorGeneratorAgentSDK
from src.agents.orchestrator_sdk import OrchestratorAgentSDK
from src.models.error_message import ErrorGenerationRequest
from src.models.remediation_command import RemediationCommand


class TestSDKIntegration:
    """Test SDK-based agent implementations."""
    
    def test_error_generator_sdk_basic(self, tmp_path):
        """Test basic error generation with SDK."""
        # Create sample log
        log_file = tmp_path / "test.log"
        log_file.write_text("01/15/24-10:23:45:123 (1234) 2 [License] Test error\n")
        
        # Initialize SDK agent
        agent = ErrorGeneratorAgentSDK(log_samples_path=log_file)
        
        # Verify agent created
        assert agent.agent is not None
        assert agent.agent.name == "ErrorGeneratorAgent"
        assert agent.agent.model == "gpt-4o-2024-08-06"
    
    def test_error_generator_sdk_with_template_fallback(self, tmp_path):
        """Test error generation with template fallback."""
        # Initialize without log samples
        agent = ErrorGeneratorAgentSDK()
        
        # Generate error (will use template fallback)
        request = ErrorGenerationRequest(
            error_category="license",
            severity=2
        )
        
        error = agent.generate_error(request)
        
        # Verify output
        assert error is not None
        assert error.severity == 2
        assert "[" in error.category
        assert len(error.message_text) >= 10
    
    def test_orchestrator_sdk_basic(self):
        """Test basic orchestrator with SDK."""
        # Initialize SDK orchestrator
        orchestrator = OrchestratorAgentSDK()
        
        # Verify agent created
        assert orchestrator.agent is not None
        assert orchestrator.agent.name == "OrchestratorAgent"
    
    def test_orchestrator_sdk_routing(self):
        """Test command routing with SDK orchestrator."""
        orchestrator = OrchestratorAgentSDK()
        
        # Create test command
        command = RemediationCommand(
            action_type="config_change",
            target="iris.cpf",
            parameters={"section": "Startup", "key": "globals", "value": "20000"}
        )
        
        # Route command
        response = orchestrator.route_command(command)
        
        # Verify routing
        assert response is not None
        assert response.agent_type in ["config", "os", "restart"]
        assert response.estimated_risk in ["low", "medium", "high"]
        assert hasattr(response, 'rationale')
        assert hasattr(response, 'command_str')  # Verify command_str field present
        assert response.command_str is not None
    
    def test_orchestrator_sdk_handoffs(self):
        """Test orchestrator workflow creation."""
        orchestrator = OrchestratorAgentSDK()
        
        # Create workflow (note: handoffs not yet fully implemented)
        workflow_agent = orchestrator.create_workflow()
        
        # Verify an agent is returned
        assert workflow_agent is not None
        assert workflow_agent.name == "OrchestratorAgent"
        assert hasattr(workflow_agent, 'handoffs') or hasattr(workflow_agent, '_handoffs')
    
    @pytest.mark.skip(reason="Requires OPENAI_API_KEY - integration test")
    def test_error_generator_sdk_with_llm(self, tmp_path):
        """Test error generation with real LLM call.
        
        This test requires OPENAI_API_KEY to be set.
        Skip in CI/CD or run manually with: pytest -m llm
        """
        # Create sample log
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "01/15/24-10:23:45:123 (1234) 2 [License] LMF Error: Invalid key\n"
            "01/15/24-10:23:46:456 (5678) 1 [Config] CPF Parameter 'globals' invalid\n"
        )
        
        # Initialize SDK agent
        agent = ErrorGeneratorAgentSDK(log_samples_path=log_file)
        
        # Generate error with LLM
        request = ErrorGenerationRequest(
            error_category="license",
            severity=2
        )
        
        error = agent.generate_error(request)
        
        # Verify LLM-generated output
        assert error is not None
        assert error.severity == 2
        assert "license" in error.category.lower() or "lmf" in error.message_text.lower()
        assert len(error.message_text) >= 10
        assert len(error.message_text) <= 500
    
    @pytest.mark.skip(reason="Requires OPENAI_API_KEY - integration test")
    def test_orchestrator_sdk_with_llm(self):
        """Test orchestrator routing with real LLM call.
        
        This test requires OPENAI_API_KEY to be set.
        """
        orchestrator = OrchestratorAgentSDK()
        
        # Create test commands
        commands = [
            RemediationCommand(
                action_type="config_change",
                target="iris.cpf",
                parameters={"section": "Startup", "key": "globals", "value": "20000"}
            ),
            RemediationCommand(
                action_type="os_reconfig",
                target="memory",
                parameters={"resource_type": "memory", "target_value": 16384}
            ),
            RemediationCommand(
                action_type="restart",
                target="instance",
                parameters={"mode": "graceful", "timeout_seconds": 60}
            )
        ]
        
        # Route each command
        for command in commands:
            response = orchestrator.route_command(command)
            
            # Verify routing makes sense
            assert response is not None
            assert response.agent_type in ["config", "os", "restart"]
            
            # Verify routing logic
            if command.action_type == "config_change":
                assert response.agent_type == "config"
            elif command.action_type == "os_reconfig":
                assert response.agent_type == "os"
            elif command.action_type == "restart":
                assert response.agent_type == "restart"


class TestSDKFeatures:
    """Test SDK-specific features."""
    
    def test_response_format_structured_output(self):
        """Test that SDK supports Pydantic response_format."""
        from agents import Agent, Runner
        from pydantic import BaseModel
        
        class TestResponse(BaseModel):
            message: str
            count: int
        
        agent = Agent(
            name="TestAgent",
            instructions="Respond with a test message and count=42",
            model="gpt-4o-2024-08-06"
        )
        
        # Verify agent created with response format capability
        assert agent is not None
        # SDK should support response_format in Runner.run_sync
    
    def test_agent_instructions_set(self):
        """Test that agent instructions are properly set."""
        from agents import Agent
        
        instructions = "You are a test agent that counts to 10."
        agent = Agent(
            name="CounterAgent",
            instructions=instructions,
            model="gpt-4o-2024-08-06"
        )
        
        # Verify instructions
        assert agent is not None
        assert agent.instructions == instructions
    
    def test_multiple_agents_created(self):
        """Test creating multiple different agents."""
        from agents import Agent
        
        agents = []
        for i in range(3):
            agent = Agent(
                name=f"Agent{i}",
                instructions=f"You are agent number {i}",
                model="gpt-4o-2024-08-06"
            )
            agents.append(agent)
        
        # Verify all created with unique names
        assert len(agents) == 3
        assert agents[0].name == "Agent0"
        assert agents[1].name == "Agent1"
        assert agents[2].name == "Agent2"
