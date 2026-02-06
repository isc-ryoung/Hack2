"""Cost tracking utilities for LLM token usage and budget management.

Tracks token consumption across agent operations and provides budget alerts.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.utils.logger import get_logger


logger = get_logger(__name__)


# Token pricing (as of 2024, adjust as needed)
TOKEN_PRICING = {
    'gpt-4o-2024-08-06': {
        'input': 2.50 / 1_000_000,  # $2.50 per 1M input tokens
        'output': 10.00 / 1_000_000,  # $10.00 per 1M output tokens
    },
    'gpt-3.5-turbo': {
        'input': 0.50 / 1_000_000,  # $0.50 per 1M input tokens
        'output': 1.50 / 1_000_000,  # $1.50 per 1M output tokens
    },
}


@dataclass
class TokenUsage:
    """Token usage statistics for a single operation."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    operation: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def calculate_cost(self) -> float:
        """Calculate cost in USD for this token usage."""
        if self.model not in TOKEN_PRICING:
            return 0.0
        
        pricing = TOKEN_PRICING[self.model]
        input_cost = self.input_tokens * pricing['input']
        output_cost = self.output_tokens * pricing['output']
        return input_cost + output_cost


@dataclass
class TokenBudget:
    """Token budget tracking for various time periods."""
    workflow_limit: int = 5_000
    session_limit: int = 50_000
    daily_limit: int = 500_000
    alert_threshold: float = 0.8
    
    workflow_used: int = 0
    session_used: int = 0
    daily_used: int = 0
    
    session_start: datetime = field(default_factory=datetime.now)
    daily_start: datetime = field(default_factory=datetime.now)
    
    def reset_workflow(self) -> None:
        """Reset workflow token counter."""
        self.workflow_used = 0
    
    def reset_session(self) -> None:
        """Reset session token counter."""
        self.session_used = 0
        self.session_start = datetime.now()
    
    def reset_daily(self) -> None:
        """Reset daily token counter."""
        self.daily_used = 0
        self.daily_start = datetime.now()
    
    def check_and_reset(self) -> None:
        """Check if daily reset is needed."""
        if datetime.now() - self.daily_start > timedelta(days=1):
            self.reset_daily()
    
    def is_over_budget(self, tokens: int = 0) -> Dict[str, bool]:
        """Check if adding tokens would exceed any budget.
        
        Returns:
            Dictionary with budget level keys and boolean values
        """
        return {
            'workflow': (self.workflow_used + tokens) > self.workflow_limit,
            'session': (self.session_used + tokens) > self.session_limit,
            'daily': (self.daily_used + tokens) > self.daily_limit,
        }
    
    def should_alert(self) -> Dict[str, bool]:
        """Check if any budget level exceeded alert threshold.
        
        Returns:
            Dictionary with budget level keys and boolean values
        """
        return {
            'workflow': self.workflow_used > (self.workflow_limit * self.alert_threshold),
            'session': self.session_used > (self.session_limit * self.alert_threshold),
            'daily': self.daily_used > (self.daily_limit * self.alert_threshold),
        }


class CostTracker:
    """Global cost tracker for LLM token usage."""
    
    def __init__(self, budget: Optional[TokenBudget] = None):
        """Initialize cost tracker.
        
        Args:
            budget: Token budget configuration
        """
        self.budget = budget or TokenBudget()
        self.usage_history: list[TokenUsage] = []
        self.total_cost: float = 0.0
    
    def track_usage(self, usage: TokenUsage) -> None:
        """Track token usage from an LLM call.
        
        Args:
            usage: Token usage information
        """
        self.budget.check_and_reset()
        
        # Update counters
        tokens = usage.total_tokens
        self.budget.workflow_used += tokens
        self.budget.session_used += tokens
        self.budget.daily_used += tokens
        
        # Calculate cost
        cost = usage.calculate_cost()
        self.total_cost += cost
        
        # Store history
        self.usage_history.append(usage)
        
        # Check budgets
        over_budget = self.budget.is_over_budget()
        should_alert = self.budget.should_alert()
        
        # Log usage
        logger.info(
            "llm_token_usage",
            model=usage.model,
            operation=usage.operation,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            cost_usd=cost,
            workflow_usage=f"{self.budget.workflow_used}/{self.budget.workflow_limit}",
            session_usage=f"{self.budget.session_used}/{self.budget.session_limit}",
            daily_usage=f"{self.budget.daily_used}/{self.budget.daily_limit}",
        )
        
        # Alert if thresholds exceeded
        for level, alert in should_alert.items():
            if alert:
                logger.warning(
                    f"token_budget_alert_{level}",
                    level=level,
                    used=getattr(self.budget, f"{level}_used"),
                    limit=getattr(self.budget, f"{level}_limit"),
                    percent=getattr(self.budget, f"{level}_used") / getattr(self.budget, f"{level}_limit") * 100,
                )
        
        # Error if over budget
        for level, over in over_budget.items():
            if over:
                logger.error(
                    f"token_budget_exceeded_{level}",
                    level=level,
                    used=getattr(self.budget, f"{level}_used"),
                    limit=getattr(self.budget, f"{level}_limit"),
                )
    
    def get_stats(self) -> Dict[str, any]:
        """Get current token usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return {
            'total_operations': len(self.usage_history),
            'total_cost_usd': self.total_cost,
            'workflow_used': self.budget.workflow_used,
            'workflow_limit': self.budget.workflow_limit,
            'session_used': self.budget.session_used,
            'session_limit': self.budget.session_limit,
            'daily_used': self.budget.daily_used,
            'daily_limit': self.budget.daily_limit,
        }


# Global cost tracker instance
_global_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = CostTracker()
    return _global_tracker


def track_tokens(model: str, input_tokens: int, output_tokens: int, operation: str = "") -> None:
    """Track token usage for an LLM operation.
    
    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        operation: Operation description
    """
    usage = TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        model=model,
        operation=operation,
    )
    get_cost_tracker().track_usage(usage)
