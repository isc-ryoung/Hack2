"""Orchestrator Agent using OpenAI Agents SDK with handoffs.

Routes remediation commands to specialized agents using SDK handoff mechanism.
"""

from agents import Agent, Runner
from typing import List

from src.models.remediation_command import RemediationCommand
from src.models.agent_responses import OrchestratorResponse
from src.utils.logger import get_logger


logger = get_logger(__name__)


class OrchestratorAgentSDK:
    """Orchestrator using OpenAI Agents SDK handoffs."""
    
    def __init__(self):
        """Initialize orchestrator agent."""
        self.agent_name = "orchestrator"
        
        # Create orchestrator agent with structured output
        self.agent = Agent(
            name="OrchestratorAgent",
            instructions=self._get_instructions(),
            model="gpt-4o-2024-08-06",
            output_type=OrchestratorResponse
        )
    
    def _get_instructions(self) -> str:
        """Get orchestrator instructions.
        
        Returns:
            System instructions for routing
        """
        return """You are an orchestrator for IRIS database remediation commands.

Your role is to analyze remediation commands and determine which specialized agent should handle them:

1. **ConfigAgent**: For IRIS CPF configuration file changes
   - Action type: config_change
   - Handles: Startup parameters, system settings, configuration modifications
   - Risk: Medium (requires restart for some changes)

2. **OSAgent**: For operating system resource reconfiguration  
   - Action type: os_reconfig
   - Handles: Huge pages, memory allocation, CPU configuration
   - Risk: High (can affect system stability)

3. **RestartAgent**: For IRIS instance restart operations
   - Action type: restart
   - Handles: Graceful restarts, forced restarts, startup monitoring
   - Risk: High (causes downtime)

Analyze each command and output:
{
  "agent_type": "config|os|restart",
  "rationale": "Brief explanation of why this agent was selected",
  "estimated_risk": "low|medium|high",
  "requires_validation": true|false
}

Consider:
- Command action_type determines primary routing
- Risk level based on operation impact
- Validation needs for high-risk operations"""
    
    def route_command(self, command: RemediationCommand) -> OrchestratorResponse:
        """Route command to appropriate agent.
        
        Args:
            command: Remediation command to route
            
        Returns:
            Orchestrator routing decision
        """
        logger.info(
            "routing_start",
            action_type=command.action_type,
            target=command.target
        )
        
        try:
            # Format command as prompt
            prompt = f"""Analyze this remediation command and determine routing:

Command:
- Action: {command.action_type}
- Target: {command.target}
- Parameters: {command.parameters}
- Priority: {command.priority}

Which agent should handle this command?"""
            
            # Run orchestrator (output_type on Agent handles structured output)
            result = Runner.run_sync(
                self.agent,
                prompt
            )
            
            # Extract response
            if hasattr(result, 'final_output'):
                if isinstance(result.final_output, OrchestratorResponse):
                    response = result.final_output
                elif isinstance(result.final_output, str):
                    response = OrchestratorResponse.model_validate_json(result.final_output)
                else:
                    # Fallback to rules
                    logger.warning("orchestrator_fallback_to_rules")
                    response = self._route_with_rules(command)
            else:
                response = self._route_with_rules(command)
            
            logger.info(
                "routing_complete",
                agent_type=response.agent_type,
                risk=response.estimated_risk
            )
            
            return response
        
        except Exception as e:
            logger.error("routing_failed", error=str(e))
            return self._route_with_rules(command)
    
    def _route_with_rules(self, command: RemediationCommand) -> OrchestratorResponse:
        """Fallback rule-based routing.
        
        Args:
            command: Command to route
            
        Returns:
            Routing decision
        """
        # Simple rule-based routing
        routing_map = {
            "config_change": ("config", "CPF configuration modification", "medium", True),
            "os_reconfig": ("os", "Operating system resource reconfiguration", "high", True),
            "restart": ("restart", "Instance restart operation", "high", True)
        }
        
        agent_type, rationale, risk, validation = routing_map.get(
            command.action_type,
            ("config", "Default routing to config agent", "low", False)
        )
        
        # Serialize command for agent
        import json
        command_str = json.dumps(command.parameters)
        
        return OrchestratorResponse(
            agent_type=agent_type,
            command_str=command_str,
            rationale=rationale,
            estimated_risk=risk,
            requires_validation=validation
        )
    
    def create_workflow(self) -> Agent:
        """Create workflow with all specialized agents.
        
        Note: The SDK's Handoff mechanism is more complex than originally documented.
        Handoffs require:
        - tool_name: String identifier for the handoff
        - tool_description: Description of when to use this handoff
        - input_json_schema: JSON schema for handoff input
        - on_invoke_handoff: Async callback function that returns the target agent
        - agent_name: Name of the target agent
        
        For now, orchestrator uses direct routing via route_command().
        Advanced handoff implementation would require restructuring the agent workflow.
        
        Returns:
            Orchestrator agent (handoffs not yet implemented)
        """
        logger.warning(
            "handoff_not_implemented",
            message="SDK handoffs require complex setup. Using direct routing instead."
        )
        return self.agent
