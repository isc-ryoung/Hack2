"""Restart Agent using OpenAI Agents SDK for IRIS instance restart operations.

Handles graceful and forced restart scenarios with connection draining and monitoring.
"""

import time
import subprocess
from typing import Dict
from agents import Agent, Runner

from src.models.agent_responses import RestartAgentResponse
from src.models.remediation_command import RemediationCommand
from src.utils.logger import get_logger


logger = get_logger(__name__)


class RestartAgentSDK:
    """Agent for IRIS instance restart operations using OpenAI Agents SDK."""
    
    def __init__(self, iris_instance: str = "IRIS"):
        """Initialize restart agent.
        
        Args:
            iris_instance: Name of IRIS instance to manage
        """
        self.agent_name = "restart"
        self.iris_instance = iris_instance
        
        # Create SDK Agent with structured output
        self.agent = Agent(
            name="RestartAgent",
            instructions=self._get_instructions(),
            model="gpt-4o-2024-08-06",
            output_type=RestartAgentResponse
        )
    
    def _get_instructions(self) -> str:
        """Get agent instructions.
        
        Returns:
            System instructions for the agent
        """
        return """You are a database instance restart management agent for InterSystems IRIS.

Your role is to analyze restart requests and determine:
1. Whether graceful or forced restart is appropriate
2. How to drain connections before shutdown
3. How to validate successful startup

For restart operations, consider:
- Graceful: Drain connections, careful shutdown, monitor startup (30-60s)
- Forced: Immediate shutdown, emergency scenarios only (<10s)
- Safety: Validate instance is operational after restart
- Risk: Assess downtime impact on applications

Output your analysis as structured data with success status, connections drained,
shutdown/startup durations, operational status, and any error messages."""
    
    def execute(self, input_str: str) -> str:
        """Execute restart operation.
        
        Args:
            input_str: JSON string with RemediationCommand
            
        Returns:
            JSON string with RestartAgentResponse
        """
        # Parse command
        command = RemediationCommand.model_validate_json(input_str)
        
        # Execute the restart directly (SDK agent used for analysis if needed)
        return self._execute_restart(command).model_dump_json()
    
    def _execute_restart(self, command: RemediationCommand) -> RestartAgentResponse:
        """Execute the restart operation.
        
        Args:
            command: Remediation command
            
        Returns:
            Restart operation response
        """
        # Extract parameters
        mode = command.parameters.get("mode", "graceful")
        timeout_seconds = command.parameters.get("timeout_seconds", 60)
        
        logger.info(
            "restart_start",
            mode=mode,
            timeout_seconds=timeout_seconds,
            instance=self.iris_instance
        )
        
        try:
            # Execute restart based on mode
            if mode == "graceful":
                result = self._graceful_restart(timeout_seconds)
            elif mode == "forced":
                result = self._forced_restart()
            else:
                return RestartAgentResponse(
                    success=False,
                    mode=mode,
                    connections_drained=0,
                    shutdown_duration_seconds=0,
                    startup_duration_seconds=0,
                    operational_status="unknown",
                    error_message=f"Unknown restart mode: {mode}"
                )
            
            logger.info(
                "restart_complete",
                mode=mode,
                success=result["success"],
                operational_status=result["operational_status"]
            )
            
            return RestartAgentResponse(**result)
        
        except Exception as e:
            logger.error(
                "restart_failed",
                mode=mode,
                error=str(e)
            )
            
            return RestartAgentResponse(
                success=False,
                mode=mode,
                connections_drained=0,
                shutdown_duration_seconds=0,
                startup_duration_seconds=0,
                operational_status="error",
                error_message=str(e)
            )
    
    def _graceful_restart(self, timeout_seconds: int) -> Dict:
        """Perform graceful restart with connection draining.
        
        Args:
            timeout_seconds: Maximum time to wait for graceful shutdown
            
        Returns:
            Dict with RestartAgentResponse fields
        """
        start_time = time.time()
        
        # Step 1: Drain connections
        connections_drained = self._drain_connections(timeout_seconds // 2)
        
        # Step 2: Graceful shutdown
        shutdown_start = time.time()
        shutdown_success = self._shutdown_instance(graceful=True, timeout=timeout_seconds // 2)
        shutdown_duration = int(time.time() - shutdown_start)
        
        if not shutdown_success:
            return {
                "success": False,
                "mode": "graceful",
                "connections_drained": connections_drained,
                "shutdown_duration_seconds": shutdown_duration,
                "startup_duration_seconds": 0,
                "operational_status": "shutdown_failed",
                "error_message": "Graceful shutdown failed"
            }
        
        # Step 3: Start instance
        startup_start = time.time()
        startup_success = self._startup_instance()
        startup_duration = int(time.time() - startup_start)
        
        if not startup_success:
            return {
                "success": False,
                "mode": "graceful",
                "connections_drained": connections_drained,
                "shutdown_duration_seconds": shutdown_duration,
                "startup_duration_seconds": startup_duration,
                "operational_status": "startup_failed",
                "error_message": "Instance startup failed"
            }
        
        # Step 4: Validate operational status
        operational_status = self._validate_operational()
        
        return {
            "success": operational_status == "operational",
            "mode": "graceful",
            "connections_drained": connections_drained,
            "shutdown_duration_seconds": shutdown_duration,
            "startup_duration_seconds": startup_duration,
            "operational_status": operational_status,
            "error_message": None if operational_status == "operational" else "Post-startup validation failed"
        }
    
    def _forced_restart(self) -> Dict:
        """Perform forced restart (immediate shutdown).
        
        Returns:
            Dict with RestartAgentResponse fields
        """
        # Step 1: Forced shutdown (no connection draining)
        shutdown_start = time.time()
        shutdown_success = self._shutdown_instance(graceful=False, timeout=10)
        shutdown_duration = int(time.time() - shutdown_start)
        
        if not shutdown_success:
            return {
                "success": False,
                "mode": "forced",
                "connections_drained": 0,
                "shutdown_duration_seconds": shutdown_duration,
                "startup_duration_seconds": 0,
                "operational_status": "shutdown_failed",
                "error_message": "Forced shutdown failed"
            }
        
        # Step 2: Start instance
        startup_start = time.time()
        startup_success = self._startup_instance()
        startup_duration = int(time.time() - startup_start)
        
        if not startup_success:
            return {
                "success": False,
                "mode": "forced",
                "connections_drained": 0,
                "shutdown_duration_seconds": shutdown_duration,
                "startup_duration_seconds": startup_duration,
                "operational_status": "startup_failed",
                "error_message": "Instance startup failed"
            }
        
        # Step 3: Validate operational status
        operational_status = self._validate_operational()
        
        return {
            "success": operational_status == "operational",
            "mode": "forced",
            "connections_drained": 0,
            "shutdown_duration_seconds": shutdown_duration,
            "startup_duration_seconds": startup_duration,
            "operational_status": operational_status,
            "error_message": None if operational_status == "operational" else "Post-startup validation failed"
        }
    
    def _drain_connections(self, timeout_seconds: int) -> int:
        """Drain active connections before shutdown.
        
        Args:
            timeout_seconds: Maximum time to wait for draining
            
        Returns:
            Number of connections drained
        """
        # Placeholder - in real implementation would:
        # 1. Get active connection count from IRIS
        # 2. Set instance to "no new connections" mode
        # 3. Wait for connections to close
        # 4. Return count
        logger.info("connection_draining", timeout=timeout_seconds)
        time.sleep(min(timeout_seconds, 2))  # Simulate draining
        return 5  # Simulated count
    
    def _shutdown_instance(self, graceful: bool, timeout: int) -> bool:
        """Shutdown IRIS instance.
        
        Args:
            graceful: Whether to use graceful shutdown
            timeout: Maximum time to wait for shutdown
            
        Returns:
            True if shutdown successful
        """
        try:
            # In real implementation: iris stop IRIS [carefully|force]
            cmd = ["echo", "iris", "stop", self.iris_instance, "carefully" if graceful else "force"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            logger.info(
                "instance_shutdown",
                graceful=graceful,
                returncode=result.returncode
            )
            
            return result.returncode == 0
        
        except subprocess.TimeoutExpired:
            logger.error("shutdown_timeout", timeout=timeout)
            return False
    
    def _startup_instance(self) -> bool:
        """Start IRIS instance.
        
        Returns:
            True if startup successful
        """
        try:
            # In real implementation: iris start IRIS
            cmd = ["echo", "iris", "start", self.iris_instance]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            logger.info(
                "instance_startup",
                returncode=result.returncode
            )
            
            # Wait for instance to be ready
            time.sleep(2)
            
            return result.returncode == 0
        
        except subprocess.TimeoutExpired:
            logger.error("startup_timeout")
            return False
    
    def _validate_operational(self) -> str:
        """Validate instance is operational.
        
        Returns:
            Status string: operational, degraded, error
        """
        try:
            # In real implementation: check IRIS system status
            # For now, simulate validation
            logger.info("validating_operational_status")
            return "operational"
        
        except Exception as e:
            logger.error("validation_failed", error=str(e))
            return "error"
    
    def restart_instance(
        self,
        mode: str = "graceful",
        timeout_seconds: int = 60
    ) -> RestartAgentResponse:
        """Public API for instance restart (convenience method).
        
        Args:
            mode: Restart mode (graceful or forced)
            timeout_seconds: Maximum time for graceful shutdown
            
        Returns:
            RestartAgentResponse
        """
        command = RemediationCommand(
            action_type="restart",
            target="instance",
            parameters={
                "mode": mode,
                "timeout_seconds": timeout_seconds
            }
        )
        
        result_str = self.execute(command.model_dump_json())
        return RestartAgentResponse.model_validate_json(result_str)
