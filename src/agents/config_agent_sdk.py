"""Config Agent using OpenAI Agents SDK for IRIS CPF configuration file modifications.

Handles configuration parameter changes with backup and restart requirement detection.
"""

from pathlib import Path
from agents import Agent, Runner

from src.models.agent_responses import ConfigAgentResponse
from src.models.remediation_command import RemediationCommand
from src.services.cpf_manager import CPFManager
from src.utils.config import get_config
from src.utils.logger import get_logger


logger = get_logger(__name__)


class ConfigAgentSDK:
    """Agent for IRIS configuration changes using OpenAI Agents SDK."""
    
    def __init__(self, cpf_path: Path = None):
        """Initialize config agent.
        
        Args:
            cpf_path: Path to iris.cpf file (overrides config)
        """
        self.agent_name = "config"
        
        if cpf_path is None:
            config = get_config()
            cpf_path = config.iris.cpf_path
        
        self.cpf_manager = CPFManager(cpf_path)
        
        # Create SDK Agent with structured output
        self.agent = Agent(
            name="ConfigAgent",
            instructions=self._get_instructions(),
            model="gpt-4o-2024-08-06",
            output_type=ConfigAgentResponse
        )
    
    def _get_instructions(self) -> str:
        """Get agent instructions.
        
        Returns:
            System instructions for the agent
        """
        return """You are a configuration management agent for InterSystems IRIS database.

Your role is to analyze configuration change requests and determine:
1. Whether the change is safe to apply
2. What the potential impact is
3. Whether a restart is required

For configuration changes, consider:
- Startup section: Most changes require restart (globals, locksiz, gmheap)
- Config section: Some changes take effect immediately
- Safety: Validate parameter names and value ranges
- Risk: Assess impact on running system

Output your analysis as structured data with success status, old/new values,
restart requirement, and any error messages."""
    
    def execute(self, input_str: str) -> str:
        """Execute configuration change.
        
        Args:
            input_str: JSON string with RemediationCommand
            
        Returns:
            JSON string with ConfigAgentResponse
        """
        # Parse command
        command = RemediationCommand.model_validate_json(input_str)
        
        # Execute the change directly (SDK agent used for validation/analysis if needed)
        return self._execute_change(command).model_dump_json()
    
    def _execute_change(self, command: RemediationCommand) -> ConfigAgentResponse:
        """Execute the configuration change.
        
        Args:
            command: Remediation command
            
        Returns:
            Configuration change response
        """
        # Extract parameters
        section = command.parameters.get("section")
        key = command.parameters.get("key")
        value = command.parameters.get("value")
        
        logger.info(
            "config_change_start",
            section=section,
            key=key,
            target_value=value
        )
        
        try:
            # Read old value
            old_value = self.cpf_manager.read_setting(section, key)
            
            # Write new value
            success, backup_path = self.cpf_manager.write_setting(
                section=section,
                key=key,
                value=value,
                create_backup=True
            )
            
            if not success:
                return ConfigAgentResponse(
                    success=False,
                    section=section,
                    key=key,
                    old_value=old_value,
                    new_value=value,
                    requires_restart=False,
                    backup_path=backup_path,
                    error_message="Failed to write configuration setting"
                )
            
            # Validate CPF
            if not self.cpf_manager.validate_cpf():
                # Rollback
                if backup_path:
                    self.cpf_manager.restore_backup(backup_path)
                
                return ConfigAgentResponse(
                    success=False,
                    section=section,
                    key=key,
                    old_value=old_value,
                    new_value=value,
                    requires_restart=False,
                    backup_path=backup_path,
                    error_message="CPF validation failed, changes rolled back"
                )
            
            # Determine restart requirement
            requires_restart = self.cpf_manager.requires_restart(section, key)
            
            logger.info(
                "config_change_success",
                section=section,
                key=key,
                old_value=old_value,
                new_value=value,
                requires_restart=requires_restart
            )
            
            return ConfigAgentResponse(
                success=True,
                section=section,
                key=key,
                old_value=old_value,
                new_value=value,
                requires_restart=requires_restart,
                backup_path=backup_path,
                error_message=None
            )
        
        except Exception as e:
            logger.error(
                "config_change_failed",
                section=section,
                key=key,
                error=str(e)
            )
            
            return ConfigAgentResponse(
                success=False,
                section=section,
                key=key,
                old_value=None,
                new_value=value,
                requires_restart=False,
                backup_path=None,
                error_message=str(e)
            )
    
    def modify_config(
        self,
        section: str,
        key: str,
        value: str
    ) -> ConfigAgentResponse:
        """Public API for config changes (convenience method).
        
        Args:
            section: CPF section
            key: Configuration key
            value: New value
            
        Returns:
            ConfigAgentResponse
        """
        command = RemediationCommand(
            action_type="config_change",
            target="iris.cpf",
            parameters={
                "section": section,
                "key": key,
                "value": value
            }
        )
        
        result_str = self.execute(command.model_dump_json())
        return ConfigAgentResponse.model_validate_json(result_str)
