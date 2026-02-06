"""Execution context and runtime state models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class ExecutionContext:
    """Runtime state and context for agent operations."""
    
    workflow_id: UUID = field(default_factory=uuid4)
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    iris_instance_status: str = "unknown"  # running, stopped, unknown
    pending_commands: List[UUID] = field(default_factory=list)
    active_operations: Dict[str, any] = field(default_factory=dict)
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def add_pending_command(self, command_id: UUID) -> None:
        """Add command to pending queue."""
        if command_id not in self.pending_commands:
            self.pending_commands.append(command_id)
    
    def remove_pending_command(self, command_id: UUID) -> None:
        """Remove command from pending queue."""
        if command_id in self.pending_commands:
            self.pending_commands.remove(command_id)
    
    def set_operation_status(self, operation_id: str, status: str, details: any = None) -> None:
        """Update status of an active operation."""
        self.active_operations[operation_id] = {
            'status': status,
            'details': details,
            'updated_at': datetime.now().isoformat(),
        }
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict]:
        """Get status of an operation."""
        return self.active_operations.get(operation_id)
