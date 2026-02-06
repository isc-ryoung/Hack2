"""Base agent class with observability hooks.

Provides common functionality for all agents including trace ID management,
logging, and error handling.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from src.utils.cost_tracker import get_cost_tracker
from src.utils.logger import get_logger, get_trace_id, set_trace_id, clear_trace_id


class BaseAgent(ABC):
    """Base class for all agents with observability support."""
    
    def __init__(self, agent_name: str):
        """Initialize base agent.
        
        Args:
            agent_name: Name of the agent for logging
        """
        self.agent_name = agent_name
        self.logger = get_logger(f"agent.{agent_name}")
    
    @abstractmethod
    def _execute_impl(self, input_str: str) -> str:
        """Execute agent logic (to be implemented by subclasses).
        
        Args:
            input_str: JSON string input
            
        Returns:
            JSON string output
        """
        pass
    
    def execute(self, input_str: str, trace_id: str = None) -> str:
        """Execute agent with observability hooks.
        
        Args:
            input_str: JSON string input
            trace_id: Optional trace ID (generates new if not provided)
            
        Returns:
            JSON string output
        """
        # Set up trace ID
        if trace_id:
            set_trace_id(trace_id)
        else:
            trace_id = get_trace_id()
        
        try:
            self.logger.info(
                "agent_execution_start",
                agent=self.agent_name,
                trace_id=trace_id,
                input_length=len(input_str),
            )
            
            # Execute agent logic
            result = self._execute_impl(input_str)
            
            self.logger.info(
                "agent_execution_complete",
                agent=self.agent_name,
                trace_id=trace_id,
                output_length=len(result),
            )
            
            return result
        
        except Exception as e:
            self.logger.error(
                "agent_execution_failed",
                agent=self.agent_name,
                trace_id=trace_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        
        finally:
            # Note: Don't clear trace ID here as it might be used by caller
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics.
        
        Returns:
            Dictionary with agent statistics
        """
        tracker = get_cost_tracker()
        return {
            'agent_name': self.agent_name,
            'cost_stats': tracker.get_stats(),
        }
