"""Prompt template management system.

Centralizes all LLM prompt templates for consistency and maintainability.
"""

from typing import Dict, Any


class PromptTemplate:
    """Base class for prompt templates."""
    
    def __init__(self, template: str):
        """Initialize prompt template.
        
        Args:
            template: Template string with {variable} placeholders
        """
        self.template = template
    
    def format(self, **kwargs) -> str:
        """Format template with provided variables.
        
        Args:
            **kwargs: Template variables
            
        Returns:
            Formatted prompt string
        """
        return self.template.format(**kwargs)


# System prompts for agents
SYSTEM_PROMPTS = {
    'error_generator': """You are an expert in InterSystems IRIS database systems.
Generate realistic error messages that match the format and style of actual IRIS messages.log entries.
Consider the technical context, severity levels, and typical error patterns.""",
    
    'orchestrator': """You are an orchestration agent for IRIS database operations.
Analyze remediation commands and determine which specialized agent should handle each task.
Consider dependencies, risks, and the technical nature of each operation.""",
    
    'config_validator': """You are an IRIS configuration expert.
Analyze configuration changes and determine if they require an instance restart.
Consider the parameter type, section, and IRIS startup behavior.""",
}


def get_system_prompt(agent_type: str) -> str:
    """Get system prompt for an agent type.
    
    Args:
        agent_type: Type of agent (error_generator, orchestrator, etc.)
        
    Returns:
        System prompt string
    """
    return SYSTEM_PROMPTS.get(agent_type, "You are a helpful AI assistant.")


def create_messages(system_prompt: str, user_content: str) -> list[Dict[str, str]]:
    """Create message list for LLM API call.
    
    Args:
        system_prompt: System prompt
        user_content: User message content
        
    Returns:
        List of message dictionaries
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
