"""Unit tests for cost tracker with token counting."""

import pytest
from src.utils.cost_tracker import (
    TokenUsage,
    TokenBudget,
    CostTracker,
    get_cost_tracker,
    track_tokens,
)


def test_token_usage_cost_calculation():
    """Test cost calculation for token usage."""
    usage = TokenUsage(
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
        model="gpt-4o-2024-08-06",
        operation="test"
    )
    
    cost = usage.calculate_cost()
    assert cost > 0
    # Should be ~$0.0075 (1000 * 0.0000025 + 500 * 0.00001)
    assert 0.007 < cost < 0.008


def test_token_budget_tracking():
    """Test token budget and limits."""
    budget = TokenBudget(
        workflow_limit=1000,
        session_limit=5000,
        daily_limit=10000
    )
    
    # Check budget status
    over = budget.is_over_budget(500)
    assert not over['workflow']
    assert not over['session']
    assert not over['daily']
    
    # Add tokens
    budget.workflow_used = 900
    over = budget.is_over_budget(200)
    assert over['workflow']  # Would exceed
    
    # Check alerts
    budget.workflow_used = 850  # 85% of 1000
    alerts = budget.should_alert()
    assert alerts['workflow']  # Above 80% threshold


def test_cost_tracker():
    """Test cost tracker functionality."""
    tracker = CostTracker()
    
    # Track usage
    usage = TokenUsage(
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        model="gpt-3.5-turbo",
        operation="test"
    )
    tracker.track_usage(usage)
    
    # Check stats
    stats = tracker.get_stats()
    assert stats['total_operations'] == 1
    assert stats['workflow_used'] == 150
    assert stats['total_cost_usd'] > 0


def test_global_tracker():
    """Test global tracker singleton."""
    tracker1 = get_cost_tracker()
    tracker2 = get_cost_tracker()
    assert tracker1 is tracker2


def test_track_tokens_helper():
    """Test track_tokens helper function."""
    # Should not raise errors
    track_tokens(
        model="gpt-3.5-turbo",
        input_tokens=100,
        output_tokens=50,
        operation="test_operation"
    )
