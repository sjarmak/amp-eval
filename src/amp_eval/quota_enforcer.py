#!/usr/bin/env python3
"""
Quota enforcement system that integrates with cost tracking.
Prevents evaluations from proceeding if budget limits would be exceeded.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .cost_tracking import CostTracker, TokenUsage, MODEL_COSTS, get_cost_tracker

logger = logging.getLogger(__name__)


class QuotaStatus(Enum):
    """Quota compliance status."""
    ALLOWED = "allowed"
    WARNING = "warning"  
    BLOCKED = "blocked"


@dataclass
class QuotaCheck:
    """Result of quota compliance check."""
    status: QuotaStatus
    estimated_cost: float
    estimated_tokens: int
    message: str
    remaining_daily_budget: float
    remaining_hourly_tokens: int
    context_utilization: float


class QuotaEnforcer:
    """Enforces budget and usage quotas before evaluations run."""
    
    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        self.cost_tracker = cost_tracker or get_cost_tracker()
    
    def estimate_evaluation_cost(self, model: str, estimated_input_tokens: int, 
                                estimated_output_tokens: int) -> Tuple[float, int]:
        """Estimate cost and total tokens for an evaluation."""
        if model not in MODEL_COSTS:
            logger.warning(f"Unknown model {model}, using conservative estimates")
            # Use highest cost model for safety
            input_cost_per_1k = 0.04
            output_cost_per_1k = 0.12
        else:
            config = MODEL_COSTS[model]
            input_cost_per_1k = config["input_cost_per_1k"]
            output_cost_per_1k = config["output_cost_per_1k"]
        
        input_cost = (estimated_input_tokens / 1000) * input_cost_per_1k
        output_cost = (estimated_output_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost
        total_tokens = estimated_input_tokens + estimated_output_tokens
        
        return total_cost, total_tokens
    
    def check_quota_compliance(self, model: str, estimated_input_tokens: int,
                             estimated_output_tokens: int, 
                             context_tokens: int = 0) -> QuotaCheck:
        """Check if evaluation can proceed without violating quotas."""
        estimated_cost, estimated_tokens = self.estimate_evaluation_cost(
            model, estimated_input_tokens, estimated_output_tokens
        )
        
        # Check context window utilization
        context_limit = MODEL_COSTS.get(model, {}).get("context_window", 128000)
        context_utilization = context_tokens / context_limit if context_limit > 0 else 0
        
        # Get current usage and limits
        compliance_report = self.cost_tracker.check_quota_compliance()
        usage_metrics = compliance_report["usage_metrics"]
        
        # Calculate remaining budgets
        daily_budget_used = usage_metrics["daily_cost"]
        daily_budget_limit = self.cost_tracker.budget_limits.daily_cost_limit
        remaining_daily_budget = daily_budget_limit - daily_budget_used
        
        hourly_tokens_used = usage_metrics["hourly_tokens"]
        hourly_token_limit = self.cost_tracker.budget_limits.hourly_token_limit
        remaining_hourly_tokens = hourly_token_limit - hourly_tokens_used
        
        # Determine quota status
        status = QuotaStatus.ALLOWED
        message = "Evaluation approved"
        
        # Check hard limits (blocking conditions)
        if estimated_cost > remaining_daily_budget:
            status = QuotaStatus.BLOCKED
            message = f"Daily budget exceeded: ${estimated_cost:.2f} > ${remaining_daily_budget:.2f} remaining"
        elif estimated_tokens > remaining_hourly_tokens:
            status = QuotaStatus.BLOCKED
            message = f"Hourly token limit exceeded: {estimated_tokens} > {remaining_hourly_tokens} remaining"
        elif context_utilization > self.cost_tracker.budget_limits.max_context_utilization:
            status = QuotaStatus.BLOCKED
            message = f"Context utilization too high: {context_utilization:.1%} > {self.cost_tracker.budget_limits.max_context_utilization:.1%}"
        
        # Check warning conditions (if not already blocked)
        elif status == QuotaStatus.ALLOWED:
            warning_threshold = self.cost_tracker.budget_limits.cost_alert_threshold
            
            if (daily_budget_used + estimated_cost) / daily_budget_limit > warning_threshold:
                status = QuotaStatus.WARNING
                message = f"High daily budget usage after evaluation: {((daily_budget_used + estimated_cost) / daily_budget_limit):.1%}"
            elif (hourly_tokens_used + estimated_tokens) / hourly_token_limit > warning_threshold:
                status = QuotaStatus.WARNING
                message = f"High hourly token usage after evaluation: {((hourly_tokens_used + estimated_tokens) / hourly_token_limit):.1%}"
            elif context_utilization > 0.8:
                status = QuotaStatus.WARNING
                message = f"High context utilization: {context_utilization:.1%}"
        
        return QuotaCheck(
            status=status,
            estimated_cost=estimated_cost,
            estimated_tokens=estimated_tokens,
            message=message,
            remaining_daily_budget=remaining_daily_budget,
            remaining_hourly_tokens=remaining_hourly_tokens,
            context_utilization=context_utilization
        )
    
    def check_evaluation_suite(self, evaluation_plan: Dict[str, Any]) -> Dict[str, QuotaCheck]:
        """Check quota compliance for an entire evaluation suite."""
        results = {}
        
        for eval_name, eval_config in evaluation_plan.items():
            model = eval_config.get("model", "gpt-5")
            estimated_tokens = eval_config.get("estimated_tokens", 5000)
            input_ratio = eval_config.get("input_ratio", 0.7)  # 70% input, 30% output
            
            estimated_input = int(estimated_tokens * input_ratio)
            estimated_output = estimated_tokens - estimated_input
            context_tokens = eval_config.get("context_tokens", estimated_input)
            
            quota_check = self.check_quota_compliance(
                model, estimated_input, estimated_output, context_tokens
            )
            
            results[eval_name] = quota_check
        
        return results
    
    def get_quota_summary(self) -> Dict[str, Any]:
        """Get current quota usage summary."""
        compliance_report = self.cost_tracker.check_quota_compliance()
        usage_metrics = compliance_report["usage_metrics"]
        
        daily_budget_limit = self.cost_tracker.budget_limits.daily_cost_limit
        hourly_token_limit = self.cost_tracker.budget_limits.hourly_token_limit
        monthly_budget_limit = self.cost_tracker.budget_limits.monthly_cost_limit
        
        # Get monthly usage
        monthly_stats = self.cost_tracker.get_usage_stats(days=30)
        
        return {
            "daily_budget": {
                "used": usage_metrics["daily_cost"],
                "limit": daily_budget_limit,
                "remaining": daily_budget_limit - usage_metrics["daily_cost"],
                "utilization": usage_metrics["daily_cost_compliance"]
            },
            "hourly_tokens": {
                "used": usage_metrics["hourly_tokens"],
                "limit": hourly_token_limit,
                "remaining": hourly_token_limit - usage_metrics["hourly_tokens"],
                "utilization": usage_metrics["hourly_token_compliance"]
            },
            "monthly_budget": {
                "used": monthly_stats.total_cost,
                "limit": monthly_budget_limit,
                "remaining": monthly_budget_limit - monthly_stats.total_cost,
                "utilization": monthly_stats.total_cost / monthly_budget_limit
            },
            "compliance_status": compliance_report["status"],
            "warnings": compliance_report["warnings"],
            "errors": compliance_report["errors"]
        }


class QuotaException(Exception):
    """Raised when quota limits prevent evaluation from proceeding."""
    
    def __init__(self, quota_check: QuotaCheck):
        self.quota_check = quota_check
        super().__init__(quota_check.message)


def enforce_quota(model: str, estimated_input_tokens: int, estimated_output_tokens: int,
                 context_tokens: int = 0, allow_warnings: bool = True) -> QuotaCheck:
    """Convenience function to enforce quota limits."""
    enforcer = QuotaEnforcer()
    quota_check = enforcer.check_quota_compliance(
        model, estimated_input_tokens, estimated_output_tokens, context_tokens
    )
    
    if quota_check.status == QuotaStatus.BLOCKED:
        raise QuotaException(quota_check)
    elif quota_check.status == QuotaStatus.WARNING and not allow_warnings:
        raise QuotaException(quota_check)
    
    return quota_check


if __name__ == "__main__":
    # Example usage
    enforcer = QuotaEnforcer()
    
    # Check quota for a single evaluation
    quota_check = enforcer.check_quota_compliance(
        model="gpt-5",
        estimated_input_tokens=3000,
        estimated_output_tokens=1000,
        context_tokens=4000
    )
    
    print(f"Quota status: {quota_check.status.value}")
    print(f"Message: {quota_check.message}")
    print(f"Estimated cost: ${quota_check.estimated_cost:.4f}")
    print(f"Context utilization: {quota_check.context_utilization:.1%}")
    
    # Get quota summary
    summary = enforcer.get_quota_summary()
    print(f"\nDaily budget: ${summary['daily_budget']['used']:.2f} / ${summary['daily_budget']['limit']:.2f}")
    print(f"Hourly tokens: {summary['hourly_tokens']['used']} / {summary['hourly_tokens']['limit']}")
    print(f"Compliance: {summary['compliance_status']}")
