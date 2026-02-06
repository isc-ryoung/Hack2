"""Orchestration prompts for intelligent agent routing."""

from src.models.remediation_command import RemediationCommand


def create_orchestration_prompt(command: RemediationCommand) -> str:
    """Create prompt for orchestrator agent selection.
    
    Args:
        command: Remediation command to route
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""Analyze this IRIS remediation command and determine the appropriate specialized agent to handle it.

Command Details:
- Action Type: {command.action_type}
- Target: {command.target}
- Parameters: {command.parameters}
- Priority: {command.priority}

Available Agents:
1. **config** - ConfigAgent: Handles IRIS CPF configuration file modifications
   - Modifies configuration parameters in iris.cpf
   - Determines restart requirements
   - Creates backups before changes
   - Validates configuration syntax

2. **os** - OSAgent: Handles operating system resource configuration
   - Adjusts memory settings (huge pages, shared memory)
   - Configures CPU settings (affinity, allocation)
   - Validates system resources
   - Checks permissions

3. **restart** - RestartAgent: Handles IRIS instance restart operations
   - Graceful shutdown with connection draining
   - Forced shutdown for emergencies
   - Startup monitoring and validation
   - Connection verification

4. **none** - No agent: Command cannot be handled or is invalid

Decision Criteria:
- action_type="config_change" → Usually ConfigAgent
- action_type="os_reconfig" → Usually OSAgent
- action_type="restart" → Usually RestartAgent
- Consider target and parameters for edge cases

Risk Assessment:
- low: Read-only or non-critical changes
- medium: Configuration changes that may need restart
- high: OS changes or forced restarts that could cause downtime

Provide a structured decision including:
1. Which agent should handle this (config, os, restart, or none)
2. The command data to pass to that agent (as JSON string)
3. Clear rationale for the decision
4. Whether pre-execution validation is needed
5. Estimated risk level (low, medium, high)
"""
    
    return prompt
