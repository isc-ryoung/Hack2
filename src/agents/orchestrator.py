"""Orchestrator Agent for routing remediation commands to specialized agents.

Analyzes commands and determines which agent should handle execution.
"""

from src.agents.base_agent import BaseAgent
from src.models.agent_responses import OrchestratorResponse
from src.models.remediation_command import RemediationCommand
from src.prompts import get_system_prompt, create_messages
from src.prompts.orchestration import create_orchestration_prompt
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger


logger = get_logger(__name__)


class OrchestratorAgent(BaseAgent):
    """Agent for orchestrating remediation command routing."""
    
    def __init__(self):
        """Initialize orchestrator agent."""
        super().__init__("orchestrator")
        self.llm_client = get_llm_client()
    
    def _execute_impl(self, input_str: str) -> str:
        """Route command to appropriate agent.
        
        Args:
            input_str: JSON string with RemediationCommand
            
        Returns:
            JSON string with OrchestratorResponse
        """
        # Parse command
        command = RemediationCommand.model_validate_json(input_str)
        
        logger.info(
            "orchestration_start",
            command_id=str(command.command_id),
            action_type=command.action_type,
            target=command.target
        )
        
        try:
            # Try LLM-based routing
            response = self._route_with_llm(command)
        except Exception as e:
            logger.warning(
                "llm_routing_failed",
                error=str(e),
                fallback="Using rule-based routing"
            )
            # Fall back to rule-based routing
            response = self._route_with_rules(command)
        
        logger.info(
            "orchestration_complete",
            command_id=str(command.command_id),
            selected_agent=response.agent_type,
            risk=response.estimated_risk
        )
        
        return response.model_dump_json()
    
    def _route_with_llm(self, command: RemediationCommand) -> OrchestratorResponse:
        """Route using LLM analysis.
        
        Args:
            command: Command to route
            
        Returns:
            OrchestratorResponse
        """
        # Create prompt
        prompt = create_orchestration_prompt(command)
        
        # Call LLM with structured output
        messages = create_messages(
            system_prompt=get_system_prompt("orchestrator"),
            user_content=prompt
        )
        
        result = self.llm_client.parse(
            messages=messages,
            response_format=OrchestratorResponse,
            operation="route_command"
        )
        
        return result
    
    def _route_with_rules(self, command: RemediationCommand) -> OrchestratorResponse:
        """Route using rule-based logic (fallback).
        
        Args:
            command: Command to route
            
        Returns:
            OrchestratorResponse
        """
        # Simple rule-based routing
        agent_map = {
            "config_change": "config",
            "os_reconfig": "os",
            "restart": "restart"
        }
        
        agent_type = agent_map.get(command.action_type, "none")
        
        # Prepare command string for selected agent
        command_str = command.model_dump_json()
        
        # Determine risk based on action type
        risk_map = {
            "config_change": "medium",
            "os_reconfig": "high",
            "restart": "high"
        }
        risk = risk_map.get(command.action_type, "medium")
        
        rationale = f"Rule-based routing: {command.action_type} maps to {agent_type} agent"
        
        return OrchestratorResponse(
            agent_type=agent_type,
            command_str=command_str,
            rationale=rationale,
            requires_validation=True if risk != "low" else False,
            estimated_risk=risk
        )
    
    def route_command(self, command: RemediationCommand) -> OrchestratorResponse:
        """Public API for routing commands (convenience method).
        
        Args:
            command: Command to route
            
        Returns:
            OrchestratorResponse
        """
        result_str = self.execute(command.model_dump_json())
        return OrchestratorResponse.model_validate_json(result_str)
