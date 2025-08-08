#!/usr/bin/env python3
"""
Phase 8: Cost Tracking and Governance System

Comprehensive cost monitoring, quota enforcement, and audit logging
based on Amp token usage and API costs.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from threading import Lock
import csv

logger = logging.getLogger(__name__)


# Model-specific cost configurations (per 1K tokens)
MODEL_COSTS = {
    "sonnet-4": {
        "input_cost_per_1k": 0.003,    # $3.00 per 1M input tokens
        "output_cost_per_1k": 0.015,   # $15.00 per 1M output tokens
        "context_window": 200000,
        "max_output": 4096
    },
    "gpt-5": {
        "input_cost_per_1k": 0.01,     # $10.00 per 1M input tokens  
        "output_cost_per_1k": 0.03,    # $30.00 per 1M output tokens
        "context_window": 128000,
        "max_output": 4096
    },
    "o3": {
        "input_cost_per_1k": 0.04,     # $40.00 per 1M input tokens
        "output_cost_per_1k": 0.12,    # $120.00 per 1M output tokens
        "context_window": 200000,
        "max_output": 65536
    },
    "gpt-4o": {
        "input_cost_per_1k": 0.0025,   # $2.50 per 1M input tokens
        "output_cost_per_1k": 0.01,    # $10.00 per 1M output tokens
        "context_window": 128000,
        "max_output": 16384
    }
}


@dataclass
class TokenUsage:
    """Detailed token usage information."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    context_window_used: int = 0
    context_window_limit: int = 0
    
    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class CostRecord:
    """Individual cost record for audit trail."""
    timestamp: float
    evaluation_id: str
    task_id: str
    model: str
    token_usage: TokenUsage
    input_cost: float
    output_cost: float
    total_cost: float
    context_utilization: float  # Percentage of context window used
    degradation_indicator: Optional[str] = None  # Performance degradation notes
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            **asdict(self),
            'token_usage': asdict(self.token_usage),
            'formatted_timestamp': datetime.fromtimestamp(self.timestamp).isoformat()
        }


@dataclass 
class BudgetLimits:
    """Budget and quota limits."""
    daily_cost_limit: float = 100.0      # USD
    monthly_cost_limit: float = 2000.0   # USD
    hourly_token_limit: int = 100000     # Tokens
    daily_token_limit: int = 1000000     # Tokens
    max_context_utilization: float = 0.9  # 90% of context window
    cost_alert_threshold: float = 0.8     # Alert at 80% of budget


@dataclass
class UsageStats:
    """Aggregated usage statistics."""
    total_cost: float = 0.0
    total_tokens: int = 0
    total_evaluations: int = 0
    average_cost_per_evaluation: float = 0.0
    average_tokens_per_evaluation: float = 0.0
    cost_by_model: Dict[str, float] = field(default_factory=dict)
    tokens_by_model: Dict[str, int] = field(default_factory=dict)
    degradation_events: int = 0
    high_context_usage_events: int = 0


class CostTracker:
    """Main cost tracking and monitoring system."""
    
    def __init__(self, db_path: str = "cost_tracking.db", config_path: str = None):
        self.db_path = db_path
        self.config_path = config_path or "cost_limits.json"
        self._lock = Lock()
        self.budget_limits = self._load_budget_limits()
        self._init_database()
        
    def _load_budget_limits(self) -> BudgetLimits:
        """Load budget limits from configuration file."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path) as f:
                    config = json.load(f)
                return BudgetLimits(**config)
        except Exception as e:
            logger.warning(f"Failed to load budget config: {e}, using defaults")
        
        return BudgetLimits()
    
    def _init_database(self):
        """Initialize SQLite database for cost tracking."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    evaluation_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    context_window_used INTEGER NOT NULL,
                    context_window_limit INTEGER NOT NULL,
                    input_cost REAL NOT NULL,
                    output_cost REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    context_utilization REAL NOT NULL,
                    degradation_indicator TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON cost_records(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_evaluation_id ON cost_records(evaluation_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model ON cost_records(model)
            """)
    
    def calculate_cost(self, model: str, token_usage: TokenUsage) -> Tuple[float, float, float]:
        """Calculate input, output, and total cost for given token usage."""
        if model not in MODEL_COSTS:
            logger.warning(f"Unknown model {model}, using default costs")
            input_cost_per_1k = 0.001
            output_cost_per_1k = 0.003
        else:
            config = MODEL_COSTS[model]
            input_cost_per_1k = config["input_cost_per_1k"]
            output_cost_per_1k = config["output_cost_per_1k"]
        
        input_cost = (token_usage.input_tokens / 1000) * input_cost_per_1k
        output_cost = (token_usage.output_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost
        
        return input_cost, output_cost, total_cost
    
    def assess_context_degradation(self, model: str, token_usage: TokenUsage) -> Optional[str]:
        """Assess potential performance degradation based on context usage."""
        if model not in MODEL_COSTS:
            return None
            
        context_limit = MODEL_COSTS[model]["context_window"]
        utilization = token_usage.context_window_used / context_limit
        
        if utilization > 0.95:
            return "critical_context_usage"
        elif utilization > 0.85:
            return "high_context_usage"
        elif utilization > 0.7:
            return "moderate_context_usage"
        
        return None
    
    def record_usage(self, evaluation_id: str, task_id: str, model: str, 
                    token_usage: TokenUsage, metadata: Optional[Dict[str, Any]] = None) -> CostRecord:
        """Record a single usage event."""
        timestamp = time.time()
        input_cost, output_cost, total_cost = self.calculate_cost(model, token_usage)
        
        # Calculate context utilization
        context_limit = MODEL_COSTS.get(model, {}).get("context_window", 128000)
        context_utilization = token_usage.context_window_used / context_limit if context_limit > 0 else 0
        
        # Assess degradation
        degradation_indicator = self.assess_context_degradation(model, token_usage)
        
        cost_record = CostRecord(
            timestamp=timestamp,
            evaluation_id=evaluation_id,
            task_id=task_id,
            model=model,
            token_usage=token_usage,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            context_utilization=context_utilization,
            degradation_indicator=degradation_indicator,
            metadata=metadata or {}
        )
        
        # Store in database
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO cost_records (
                        timestamp, evaluation_id, task_id, model,
                        input_tokens, output_tokens, total_tokens,
                        context_window_used, context_window_limit,
                        input_cost, output_cost, total_cost,
                        context_utilization, degradation_indicator, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, evaluation_id, task_id, model,
                    token_usage.input_tokens, token_usage.output_tokens, token_usage.total_tokens,
                    token_usage.context_window_used, token_usage.context_window_limit,
                    input_cost, output_cost, total_cost,
                    context_utilization, degradation_indicator,
                    json.dumps(metadata or {})
                ))
        
        # Check budget limits
        self._check_budget_limits(cost_record)
        
        return cost_record
    
    def _check_budget_limits(self, cost_record: CostRecord):
        """Check if usage exceeds budget limits and trigger alerts."""
        now = datetime.now()
        
        # Check hourly token limit
        hour_ago = (now - timedelta(hours=1)).timestamp()
        hourly_tokens = self._get_tokens_since(hour_ago)
        if hourly_tokens > self.budget_limits.hourly_token_limit:
            logger.warning(f"Hourly token limit exceeded: {hourly_tokens} > {self.budget_limits.hourly_token_limit}")
        
        # Check daily limits
        day_ago = (now - timedelta(days=1)).timestamp()
        daily_cost = self._get_cost_since(day_ago)
        daily_tokens = self._get_tokens_since(day_ago)
        
        if daily_cost > self.budget_limits.daily_cost_limit:
            logger.error(f"Daily cost limit exceeded: ${daily_cost:.2f} > ${self.budget_limits.daily_cost_limit:.2f}")
        elif daily_cost > self.budget_limits.daily_cost_limit * self.budget_limits.cost_alert_threshold:
            logger.warning(f"Daily cost alert: ${daily_cost:.2f} (>{self.budget_limits.cost_alert_threshold*100:.0f}% of limit)")
        
        if daily_tokens > self.budget_limits.daily_token_limit:
            logger.error(f"Daily token limit exceeded: {daily_tokens} > {self.budget_limits.daily_token_limit}")
        
        # Check context utilization
        if cost_record.context_utilization > self.budget_limits.max_context_utilization:
            logger.warning(f"High context utilization: {cost_record.context_utilization:.1%} for {cost_record.model}")
    
    def _get_cost_since(self, timestamp: float) -> float:
        """Get total cost since given timestamp."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT SUM(total_cost) FROM cost_records WHERE timestamp > ?",
                (timestamp,)
            )
            result = cursor.fetchone()[0]
            return result or 0.0
    
    def _get_tokens_since(self, timestamp: float) -> int:
        """Get total tokens since given timestamp."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT SUM(total_tokens) FROM cost_records WHERE timestamp > ?",
                (timestamp,)
            )
            result = cursor.fetchone()[0]
            return result or 0
    
    def get_usage_stats(self, days: int = 30) -> UsageStats:
        """Get aggregated usage statistics for the last N days."""
        since_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            # Overall stats
            cursor = conn.execute("""
                SELECT 
                    SUM(total_cost), SUM(total_tokens), COUNT(DISTINCT evaluation_id),
                    AVG(total_cost), AVG(total_tokens),
                    SUM(CASE WHEN degradation_indicator IS NOT NULL THEN 1 ELSE 0 END),
                    SUM(CASE WHEN context_utilization > 0.8 THEN 1 ELSE 0 END)
                FROM cost_records 
                WHERE timestamp > ?
            """, (since_timestamp,))
            
            row = cursor.fetchone()
            total_cost, total_tokens, total_evaluations, avg_cost, avg_tokens, degradation_events, high_context_events = row
            
            # Cost by model
            cursor = conn.execute("""
                SELECT model, SUM(total_cost) 
                FROM cost_records 
                WHERE timestamp > ?
                GROUP BY model
            """, (since_timestamp,))
            
            cost_by_model = dict(cursor.fetchall())
            
            # Tokens by model
            cursor = conn.execute("""
                SELECT model, SUM(total_tokens)
                FROM cost_records
                WHERE timestamp > ?
                GROUP BY model
            """, (since_timestamp,))
            
            tokens_by_model = dict(cursor.fetchall())
        
        return UsageStats(
            total_cost=total_cost or 0.0,
            total_tokens=total_tokens or 0,
            total_evaluations=total_evaluations or 0,
            average_cost_per_evaluation=avg_cost or 0.0,
            average_tokens_per_evaluation=avg_tokens or 0.0,
            cost_by_model=cost_by_model,
            tokens_by_model=tokens_by_model,
            degradation_events=degradation_events or 0,
            high_context_usage_events=high_context_events or 0
        )
    
    def generate_cost_report(self, output_path: str, days: int = 30):
        """Generate detailed cost report as CSV."""
        since_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    timestamp, evaluation_id, task_id, model,
                    input_tokens, output_tokens, total_tokens,
                    input_cost, output_cost, total_cost,
                    context_utilization, degradation_indicator
                FROM cost_records
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (since_timestamp,))
            
            records = cursor.fetchall()
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Timestamp', 'Date', 'Evaluation ID', 'Task ID', 'Model',
                'Input Tokens', 'Output Tokens', 'Total Tokens',
                'Input Cost', 'Output Cost', 'Total Cost',
                'Context Utilization', 'Degradation Indicator'
            ])
            
            for record in records:
                timestamp = record[0]
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([timestamp, date_str] + list(record[1:]))
        
        logger.info(f"Cost report generated: {output_path} ({len(records)} records)")
    
    def cleanup_old_records(self, retention_days: int = 90):
        """Remove cost records older than retention period."""
        cutoff_timestamp = (datetime.now() - timedelta(days=retention_days)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cost_records WHERE timestamp < ?",
                (cutoff_timestamp,)
            )
            deleted_count = cursor.rowcount
            
        logger.info(f"Cleaned up {deleted_count} old cost records (older than {retention_days} days)")
        return deleted_count
    
    def check_quota_compliance(self) -> Dict[str, Any]:
        """Check current usage against all quota limits."""
        now = datetime.now()
        compliance_report = {
            "timestamp": now.isoformat(),
            "status": "compliant",
            "warnings": [],
            "errors": []
        }
        
        # Check hourly limits
        hour_ago = (now - timedelta(hours=1)).timestamp()
        hourly_tokens = self._get_tokens_since(hour_ago)
        hourly_compliance = hourly_tokens / self.budget_limits.hourly_token_limit
        
        if hourly_compliance > 1.0:
            compliance_report["errors"].append(f"Hourly token limit exceeded: {hourly_compliance:.1%}")
            compliance_report["status"] = "non_compliant"
        elif hourly_compliance > 0.8:
            compliance_report["warnings"].append(f"High hourly token usage: {hourly_compliance:.1%}")
        
        # Check daily limits
        day_ago = (now - timedelta(days=1)).timestamp()
        daily_cost = self._get_cost_since(day_ago)
        daily_tokens = self._get_tokens_since(day_ago)
        
        daily_cost_compliance = daily_cost / self.budget_limits.daily_cost_limit
        daily_token_compliance = daily_tokens / self.budget_limits.daily_token_limit
        
        if daily_cost_compliance > 1.0:
            compliance_report["errors"].append(f"Daily cost limit exceeded: {daily_cost_compliance:.1%}")
            compliance_report["status"] = "non_compliant"
        elif daily_cost_compliance > 0.8:
            compliance_report["warnings"].append(f"High daily cost usage: {daily_cost_compliance:.1%}")
        
        if daily_token_compliance > 1.0:
            compliance_report["errors"].append(f"Daily token limit exceeded: {daily_token_compliance:.1%}")
            compliance_report["status"] = "non_compliant"
        elif daily_token_compliance > 0.8:
            compliance_report["warnings"].append(f"High daily token usage: {daily_token_compliance:.1%}")
        
        # Add usage metrics
        compliance_report["usage_metrics"] = {
            "hourly_tokens": hourly_tokens,
            "hourly_token_compliance": hourly_compliance,
            "daily_cost": daily_cost,
            "daily_cost_compliance": daily_cost_compliance,
            "daily_tokens": daily_tokens,
            "daily_token_compliance": daily_token_compliance
        }
        
        return compliance_report


# Global cost tracker instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def record_evaluation_cost(evaluation_id: str, task_id: str, model: str,
                          input_tokens: int, output_tokens: int, 
                          context_used: int = 0, metadata: Optional[Dict] = None) -> CostRecord:
    """Convenience function to record evaluation cost."""
    token_usage = TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        context_window_used=context_used,
        context_window_limit=MODEL_COSTS.get(model, {}).get("context_window", 128000)
    )
    
    tracker = get_cost_tracker()
    return tracker.record_usage(evaluation_id, task_id, model, token_usage, metadata)


if __name__ == "__main__":
    # Example usage and testing
    tracker = CostTracker()
    
    # Simulate some usage
    token_usage = TokenUsage(
        input_tokens=1500,
        output_tokens=500,
        context_window_used=75000,
        context_window_limit=128000
    )
    
    cost_record = tracker.record_usage(
        evaluation_id="test_eval_001",
        task_id="task_001", 
        model="gpt-5",
        token_usage=token_usage,
        metadata={"evaluation_type": "tool_calling"}
    )
    
    print(f"Recorded cost: ${cost_record.total_cost:.4f}")
    print(f"Context utilization: {cost_record.context_utilization:.1%}")
    print(f"Degradation indicator: {cost_record.degradation_indicator}")
    
    # Get usage stats
    stats = tracker.get_usage_stats(days=1)
    print(f"\nUsage stats: ${stats.total_cost:.2f}, {stats.total_tokens} tokens")
    
    # Check compliance
    compliance = tracker.check_quota_compliance()
    print(f"\nCompliance status: {compliance['status']}")
    print(f"Warnings: {compliance['warnings']}")
    print(f"Errors: {compliance['errors']}")
