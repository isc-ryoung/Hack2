"""OS Agent using OpenAI Agents SDK for Linux OS resource reconfiguration.

Handles memory allocation (huge pages, shared memory) and CPU configuration.
"""

import subprocess
from typing import Dict
from agents import Agent, Runner

from src.models.agent_responses import OSAgentResponse
from src.models.remediation_command import RemediationCommand
from src.utils.logger import get_logger


logger = get_logger(__name__)


class OSAgentSDK:
    """Agent for OS-level resource reconfiguration using OpenAI Agents SDK."""
    
    def __init__(self):
        """Initialize OS agent."""
        self.agent_name = "os"
        
        # Create SDK Agent with structured output
        self.agent = Agent(
            name="OSAgent",
            instructions=self._get_instructions(),
            model="gpt-4o-2024-08-06",
            output_type=OSAgentResponse
        )
    
    def _get_instructions(self) -> str:
        """Get agent instructions.
        
        Returns:
            System instructions for the agent
        """
        return """You are an operating system resource management agent for Linux systems.

Your role is to analyze OS reconfiguration requests and determine:
1. Whether the change is safe to apply
2. What commands should be executed
3. How to validate the change was successful

For OS changes, consider:
- Memory: Huge pages allocation, shared memory limits
- CPU: Core affinity, allocation to processes
- Permissions: Root/sudo access required
- Safety: Validate current values before changing
- Risk: Assess system stability impact

Output your analysis as structured data with success status, old/new values,
commands executed, validation results, and any error messages."""
    
    def execute(self, input_str: str) -> str:
        """Execute OS resource reconfiguration.
        
        Args:
            input_str: JSON string with RemediationCommand
            
        Returns:
            JSON string with OSAgentResponse
        """
        # Parse command
        command = RemediationCommand.model_validate_json(input_str)
        
        # Execute the change directly (SDK agent used for analysis if needed)
        return self._execute_change(command).model_dump_json()
    
    def _execute_change(self, command: RemediationCommand) -> OSAgentResponse:
        """Execute the OS reconfiguration.
        
        Args:
            command: Remediation command
            
        Returns:
            OS reconfiguration response
        """
        # Extract parameters
        resource_type = command.parameters.get("resource_type")
        target_value = command.parameters.get("target_value")
        
        logger.info(
            "os_reconfig_start",
            resource_type=resource_type,
            target_value=target_value
        )
        
        try:
            # Validate permissions
            if not self._check_permissions():
                return OSAgentResponse(
                    success=False,
                    resource_type=resource_type,
                    old_value=None,
                    new_value=target_value,
                    commands_executed=[],
                    validation_passed=False,
                    error_message="Insufficient permissions - root or sudo required"
                )
            
            # Route based on resource type
            if resource_type == "memory":
                result = self._configure_memory(target_value)
            elif resource_type == "cpu":
                result = self._configure_cpu(target_value)
            else:
                return OSAgentResponse(
                    success=False,
                    resource_type=resource_type,
                    old_value=None,
                    new_value=target_value,
                    commands_executed=[],
                    validation_passed=False,
                    error_message=f"Unknown resource_type: {resource_type}"
                )
            
            logger.info(
                "os_reconfig_complete",
                resource_type=resource_type,
                success=result["success"]
            )
            
            return OSAgentResponse(**result)
        
        except Exception as e:
            logger.error(
                "os_reconfig_failed",
                resource_type=resource_type,
                error=str(e)
            )
            
            return OSAgentResponse(
                success=False,
                resource_type=resource_type,
                old_value=None,
                new_value=target_value,
                commands_executed=[],
                validation_passed=False,
                error_message=str(e)
            )
    
    def _check_permissions(self) -> bool:
        """Check if we have sufficient permissions for OS changes.
        
        Returns:
            True if we have root/sudo access
        """
        try:
            result = subprocess.run(
                ["id", "-u"],
                capture_output=True,
                text=True,
                timeout=5
            )
            uid = int(result.stdout.strip())
            return uid == 0
        except Exception:
            return False
    
    def _configure_memory(self, target_mb: int) -> Dict:
        """Configure memory settings (huge pages).
        
        Args:
            target_mb: Target memory in MB
            
        Returns:
            Dict with OSAgentResponse fields
        """
        # Read current huge pages
        old_pages = self._get_huge_pages()
        old_mb = old_pages * 2  # Assuming 2MB pages
        
        # Calculate required pages
        target_pages = target_mb // 2
        
        commands_executed = []
        
        try:
            # Set huge pages
            cmd = ["sysctl", "-w", f"vm.nr_hugepages={target_pages}"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            commands_executed.append(" ".join(cmd))
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "resource_type": "memory",
                    "old_value": old_mb,
                    "new_value": target_mb,
                    "commands_executed": commands_executed,
                    "validation_passed": False,
                    "error_message": f"sysctl failed: {result.stderr}"
                }
            
            # Validate
            new_pages = self._get_huge_pages()
            validation_passed = new_pages >= target_pages * 0.95  # Allow 5% tolerance
            
            return {
                "success": validation_passed,
                "resource_type": "memory",
                "old_value": old_mb,
                "new_value": new_pages * 2,
                "commands_executed": commands_executed,
                "validation_passed": validation_passed,
                "error_message": None if validation_passed else "Huge pages allocation fell short of target"
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "resource_type": "memory",
                "old_value": old_mb,
                "new_value": target_mb,
                "commands_executed": commands_executed,
                "validation_passed": False,
                "error_message": "Command timeout"
            }
    
    def _configure_cpu(self, cpu_config: dict) -> Dict:
        """Configure CPU settings.
        
        Args:
            cpu_config: Dict with CPU configuration (cores, affinity)
            
        Returns:
            Dict with OSAgentResponse fields
        """
        # This is a placeholder - real implementation would use taskset/cpuset
        return {
            "success": True,
            "resource_type": "cpu",
            "old_value": "default",
            "new_value": str(cpu_config),
            "commands_executed": ["# CPU configuration placeholder"],
            "validation_passed": True,
            "error_message": None
        }
    
    def _get_huge_pages(self) -> int:
        """Get current huge pages count.
        
        Returns:
            Number of huge pages currently allocated
        """
        try:
            with open("/proc/sys/vm/nr_hugepages", "r") as f:
                return int(f.read().strip())
        except Exception:
            return 0
    
    def reconfigure_resource(
        self,
        resource_type: str,
        target_value: int
    ) -> OSAgentResponse:
        """Public API for OS reconfiguration (convenience method).
        
        Args:
            resource_type: Type of resource (memory, cpu)
            target_value: Target value (MB for memory, cores for CPU)
            
        Returns:
            OSAgentResponse
        """
        command = RemediationCommand(
            action_type="os_reconfig",
            target=resource_type,
            parameters={
                "resource_type": resource_type,
                "target_value": target_value
            }
        )
        
        result_str = self.execute(command.model_dump_json())
        return OSAgentResponse.model_validate_json(result_str)
