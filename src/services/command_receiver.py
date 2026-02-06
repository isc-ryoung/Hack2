"""Command receiver service for accepting remediation commands from external systems.

Handles JSON command parsing, validation, and queueing.
"""

import json
from typing import Dict, List, Optional
from uuid import UUID

from src.models.remediation_command import RemediationCommand
from src.utils.logger import get_logger


logger = get_logger(__name__)


class CommandReceiverService:
    """Service for receiving and validating remediation commands."""
    
    def __init__(self):
        """Initialize command receiver."""
        self.command_queue: Dict[str, RemediationCommand] = {}
        self.command_order: List[UUID] = []
    
    def receive_command(self, command_json: str) -> dict:
        """Receive and validate a remediation command.
        
        Args:
            command_json: JSON string with RemediationCommand
            
        Returns:
            Dictionary with validation result
        """
        logger.info("command_receive_start")
        
        try:
            # Parse and validate command
            command = RemediationCommand.model_validate_json(command_json)
            
            logger.info(
                "command_validated",
                command_id=str(command.command_id),
                action_type=command.action_type,
                priority=command.priority
            )
            
            # Check for conflicts
            conflict = self._check_conflicts(command)
            if conflict:
                logger.warning(
                    "command_conflict_detected",
                    command_id=str(command.command_id),
                    conflict_with=str(conflict),
                    action="Ordering commands sequentially"
                )
            
            # Add to queue
            self.command_queue[str(command.command_id)] = command
            self._insert_by_priority(command)
            
            logger.info(
                "command_queued",
                command_id=str(command.command_id),
                queue_position=self.command_order.index(command.command_id) + 1,
                queue_size=len(self.command_order)
            )
            
            return {
                "status": "accepted",
                "command_id": str(command.command_id),
                "queue_position": self.command_order.index(command.command_id) + 1,
                "conflicts": conflict is not None
            }
        
        except Exception as e:
            logger.error(
                "command_validation_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "status": "rejected",
                "error": str(e)
            }
    
    def _insert_by_priority(self, command: RemediationCommand) -> None:
        """Insert command into queue based on priority.
        
        Args:
            command: Command to insert
        """
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        command_priority = priority_order.get(command.priority, 2)
        
        # Find insertion point
        insert_at = len(self.command_order)
        for i, existing_id in enumerate(self.command_order):
            existing = self.command_queue[str(existing_id)]
            existing_priority = priority_order.get(existing.priority, 2)
            if command_priority < existing_priority:
                insert_at = i
                break
        
        self.command_order.insert(insert_at, command.command_id)
    
    def _check_conflicts(self, command: RemediationCommand) -> Optional[UUID]:
        """Check if command conflicts with queued commands.
        
        Args:
            command: Command to check
            
        Returns:
            UUID of conflicting command or None
        """
        # Check for same target
        for existing_id in self.command_order:
            existing = self.command_queue[str(existing_id)]
            if existing.target == command.target:
                return existing_id
        
        return None
    
    def get_next_command(self) -> Optional[RemediationCommand]:
        """Get next command from queue.
        
        Returns:
            Next RemediationCommand or None
        """
        if not self.command_order:
            return None
        
        command_id = self.command_order.pop(0)
        command = self.command_queue.pop(str(command_id))
        
        logger.info(
            "command_dequeued",
            command_id=str(command_id),
            action_type=command.action_type,
            remaining_queue=len(self.command_order)
        )
        
        return command
    
    def get_queue_size(self) -> int:
        """Get number of queued commands.
        
        Returns:
            Queue size
        """
        return len(self.command_order)
    
    def get_queue_status(self) -> dict:
        """Get detailed queue status.
        
        Returns:
            Dictionary with queue statistics
        """
        priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        action_counts = {"config_change": 0, "os_reconfig": 0, "restart": 0}
        
        for command_id in self.command_order:
            command = self.command_queue[str(command_id)]
            priority_counts[command.priority] += 1
            action_counts[command.action_type] += 1
        
        return {
            "total_commands": len(self.command_order),
            "by_priority": priority_counts,
            "by_action": action_counts
        }
