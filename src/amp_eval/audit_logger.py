#!/usr/bin/env python3
"""
90-day audit logging system for cost tracking and compliance.
PII-free logging with automated retention management.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    EVALUATION_START = "evaluation_start"
    EVALUATION_COMPLETE = "evaluation_complete"
    COST_RECORDED = "cost_recorded"
    QUOTA_CHECK = "quota_check"
    QUOTA_VIOLATION = "quota_violation"
    BUDGET_ALERT = "budget_alert"
    CONTEXT_DEGRADATION = "context_degradation"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    DATA_RETENTION_CLEANUP = "data_retention_cleanup"


@dataclass
class AuditEvent:
    """Audit event record (PII-free)."""
    timestamp: float
    event_type: AuditEventType
    component: str  # cost_tracker, quota_enforcer, etc.
    evaluation_id: str  # Hashed/anonymized if needed
    model: str
    
    # Event-specific data (no PII)
    event_data: Dict[str, Any]
    
    # Compliance and monitoring
    cost_impact: float = 0.0
    token_count: int = 0
    quota_status: str = "unknown"
    
    # Metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AuditLogger:
    """90-day audit logging system with automatic retention."""
    
    def __init__(self, db_path: str = "audit_logs.db", retention_days: int = 90):
        self.db_path = db_path
        self.retention_days = retention_days
        self._init_database()
    
    def _init_database(self):
        """Initialize audit log database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    component TEXT NOT NULL,
                    evaluation_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    cost_impact REAL NOT NULL,
                    token_count INTEGER NOT NULL,
                    quota_status TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Indexes for efficient querying
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_component ON audit_events(component)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_model ON audit_events(model)")
    
    def log_event(self, event: AuditEvent):
        """Log an audit event."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_events (
                    timestamp, event_type, component, evaluation_id, model,
                    event_data, cost_impact, token_count, quota_status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.event_type.value,
                event.component,
                event.evaluation_id,
                event.model,
                json.dumps(event.event_data),
                event.cost_impact,
                event.token_count,
                event.quota_status,
                json.dumps(event.metadata or {})
            ))
    
    def log_evaluation_start(self, evaluation_id: str, model: str, estimated_cost: float,
                           estimated_tokens: int, metadata: Optional[Dict] = None):
        """Log evaluation start event."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.EVALUATION_START,
            component="evaluation_runner",
            evaluation_id=evaluation_id,
            model=model,
            event_data={
                "estimated_cost": estimated_cost,
                "estimated_tokens": estimated_tokens
            },
            cost_impact=estimated_cost,
            token_count=estimated_tokens,
            quota_status="pending",
            metadata=metadata
        )
        self.log_event(event)
    
    def log_evaluation_complete(self, evaluation_id: str, model: str, actual_cost: float,
                              actual_tokens: int, success: bool, grades: Optional[Dict] = None):
        """Log evaluation completion event."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.EVALUATION_COMPLETE,
            component="evaluation_runner",
            evaluation_id=evaluation_id,
            model=model,
            event_data={
                "actual_cost": actual_cost,
                "actual_tokens": actual_tokens,
                "success": success,
                "grades_summary": self._sanitize_grades(grades) if grades else None
            },
            cost_impact=actual_cost,
            token_count=actual_tokens,
            quota_status="completed" if success else "failed"
        )
        self.log_event(event)
    
    def log_cost_recorded(self, evaluation_id: str, model: str, cost_record: Any):
        """Log cost recording event."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.COST_RECORDED,
            component="cost_tracker",
            evaluation_id=evaluation_id,
            model=model,
            event_data={
                "input_cost": cost_record.input_cost,
                "output_cost": cost_record.output_cost,
                "total_cost": cost_record.total_cost,
                "context_utilization": cost_record.context_utilization,
                "degradation_indicator": cost_record.degradation_indicator
            },
            cost_impact=cost_record.total_cost,
            token_count=cost_record.token_usage.total_tokens,
            quota_status="recorded"
        )
        self.log_event(event)
    
    def log_quota_check(self, evaluation_id: str, model: str, quota_check: Any):
        """Log quota enforcement check."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.QUOTA_CHECK,
            component="quota_enforcer",
            evaluation_id=evaluation_id,
            model=model,
            event_data={
                "status": quota_check.status.value,
                "estimated_cost": quota_check.estimated_cost,
                "estimated_tokens": quota_check.estimated_tokens,
                "remaining_daily_budget": quota_check.remaining_daily_budget,
                "remaining_hourly_tokens": quota_check.remaining_hourly_tokens,
                "context_utilization": quota_check.context_utilization
            },
            cost_impact=quota_check.estimated_cost,
            token_count=quota_check.estimated_tokens,
            quota_status=quota_check.status.value
        )
        self.log_event(event)
    
    def log_quota_violation(self, evaluation_id: str, model: str, violation_type: str,
                          details: Dict[str, Any]):
        """Log quota violation event."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.QUOTA_VIOLATION,
            component="quota_enforcer",
            evaluation_id=evaluation_id,
            model=model,
            event_data={
                "violation_type": violation_type,
                "details": details
            },
            quota_status="violated"
        )
        self.log_event(event)
    
    def log_budget_alert(self, alert_type: str, threshold: float, current_usage: float,
                        model: str = "system"):
        """Log budget alert event."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.BUDGET_ALERT,
            component="cost_tracker",
            evaluation_id="system",
            model=model,
            event_data={
                "alert_type": alert_type,
                "threshold": threshold,
                "current_usage": current_usage,
                "utilization": current_usage / threshold if threshold > 0 else 0
            },
            quota_status="alert"
        )
        self.log_event(event)
    
    def log_context_degradation(self, evaluation_id: str, model: str, context_metrics: Any):
        """Log context degradation event."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.CONTEXT_DEGRADATION,
            component="context_monitor",
            evaluation_id=evaluation_id,
            model=model,
            event_data={
                "context_utilization": context_metrics.context_utilization,
                "performance_tier": context_metrics.performance_tier.value,
                "truncation_detected": context_metrics.truncation_detected,
                "repetition_detected": context_metrics.repetition_detected,
                "coherence_score": context_metrics.coherence_score
            },
            token_count=context_metrics.total_context_tokens,
            quota_status="degraded"
        )
        self.log_event(event)
    
    def log_config_change(self, component: str, change_type: str, old_value: Any,
                         new_value: Any, changed_by: str = "system"):
        """Log system configuration change."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGE,
            component=component,
            evaluation_id="system",
            model="system",
            event_data={
                "change_type": change_type,
                "old_value": self._sanitize_value(old_value),
                "new_value": self._sanitize_value(new_value),
                "changed_by": changed_by
            },
            quota_status="config_changed"
        )
        self.log_event(event)
    
    def log_data_cleanup(self, component: str, records_deleted: int, cutoff_date: datetime):
        """Log data retention cleanup event."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=AuditEventType.DATA_RETENTION_CLEANUP,
            component=component,
            evaluation_id="system",
            model="system",
            event_data={
                "records_deleted": records_deleted,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": self.retention_days
            },
            quota_status="cleaned"
        )
        self.log_event(event)
    
    def _sanitize_grades(self, grades: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize grade data for audit logging (remove PII)."""
        sanitized = {}
        for key, value in grades.items():
            if key in ['score', 'max_score', 'passed', 'accuracy', 'quality']:
                sanitized[key] = value
            elif isinstance(value, (int, float)):
                sanitized[key] = value
        return sanitized
    
    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize configuration values (remove potential PII)."""
        if isinstance(value, dict):
            return {k: v for k, v in value.items() if not self._is_sensitive_key(k)}
        elif isinstance(value, str) and len(value) > 100:
            return value[:100] + "..."  # Truncate long strings
        else:
            return value
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a configuration key might contain sensitive data."""
        sensitive_keys = ['api_key', 'secret', 'password', 'token', 'auth', 'credential']
        return any(sensitive in key.lower() for sensitive in sensitive_keys)
    
    def query_events(self, start_time: Optional[float] = None, end_time: Optional[float] = None,
                    event_type: Optional[AuditEventType] = None, component: Optional[str] = None,
                    model: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Query audit events with filters."""
        where_clauses = []
        params = []
        
        if start_time:
            where_clauses.append("timestamp >= ?")
            params.append(start_time)
        
        if end_time:
            where_clauses.append("timestamp <= ?")
            params.append(end_time)
        
        if event_type:
            where_clauses.append("event_type = ?")
            params.append(event_type.value)
        
        if component:
            where_clauses.append("component = ?")
            params.append(component)
        
        if model:
            where_clauses.append("model = ?")
            params.append(model)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"""
                SELECT * FROM audit_events
                WHERE {where_sql}
                ORDER BY timestamp DESC
                LIMIT ?
            """, params + [limit])
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_compliance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Generate compliance summary from audit logs."""
        since_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            # Event counts by type
            cursor = conn.execute("""
                SELECT event_type, COUNT(*) as count
                FROM audit_events
                WHERE timestamp > ?
                GROUP BY event_type
            """, (since_timestamp,))
            
            event_counts = dict(cursor.fetchall())
            
            # Quota violations
            cursor = conn.execute("""
                SELECT COUNT(*) FROM audit_events
                WHERE timestamp > ? AND event_type = 'quota_violation'
            """, (since_timestamp,))
            
            quota_violations = cursor.fetchone()[0]
            
            # Budget alerts
            cursor = conn.execute("""
                SELECT COUNT(*) FROM audit_events
                WHERE timestamp > ? AND event_type = 'budget_alert'
            """, (since_timestamp,))
            
            budget_alerts = cursor.fetchone()[0]
            
            # Cost impact
            cursor = conn.execute("""
                SELECT SUM(cost_impact) FROM audit_events
                WHERE timestamp > ? AND cost_impact > 0
            """, (since_timestamp,))
            
            total_cost_impact = cursor.fetchone()[0] or 0.0
            
            # Context degradation events
            cursor = conn.execute("""
                SELECT COUNT(*) FROM audit_events
                WHERE timestamp > ? AND event_type = 'context_degradation'
            """, (since_timestamp,))
            
            degradation_events = cursor.fetchone()[0]
        
        return {
            "time_period": f"Last {days} days",
            "event_counts": event_counts,
            "compliance_metrics": {
                "quota_violations": quota_violations,
                "budget_alerts": budget_alerts,
                "degradation_events": degradation_events,
                "total_cost_impact": total_cost_impact
            },
            "compliance_score": self._calculate_compliance_score(
                quota_violations, budget_alerts, degradation_events
            )
        }
    
    def _calculate_compliance_score(self, violations: int, alerts: int, degradations: int) -> float:
        """Calculate compliance score (0-1)."""
        # Start with perfect score
        score = 1.0
        
        # Penalize violations heavily
        score -= violations * 0.1
        
        # Penalize alerts moderately
        score -= alerts * 0.05
        
        # Penalize degradations lightly
        score -= degradations * 0.02
        
        return max(0.0, score)
    
    def cleanup_old_events(self) -> int:
        """Remove audit events older than retention period."""
        cutoff_timestamp = (datetime.now() - timedelta(days=self.retention_days)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM audit_events WHERE timestamp < ?",
                (cutoff_timestamp,)
            )
            deleted_count = cursor.rowcount
        
        # Log the cleanup
        self.log_data_cleanup(
            component="audit_logger",
            records_deleted=deleted_count,
            cutoff_date=datetime.fromtimestamp(cutoff_timestamp)
        )
        
        logger.info(f"Cleaned up {deleted_count} old audit events (older than {self.retention_days} days)")
        return deleted_count
    
    def export_audit_trail(self, output_path: str, days: int = 90):
        """Export audit trail to JSON file for external analysis."""
        since_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
        events = self.query_events(start_time=since_timestamp, limit=10000)
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "time_period": f"{days} days",
            "total_events": len(events),
            "events": events
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Exported {len(events)} audit events to {output_path}")


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


if __name__ == "__main__":
    # Example usage
    audit_logger = AuditLogger()
    
    # Log some events
    audit_logger.log_evaluation_start(
        evaluation_id="test_eval_001",
        model="gpt-5",
        estimated_cost=0.05,
        estimated_tokens=2000
    )
    
    audit_logger.log_budget_alert(
        alert_type="daily_cost_warning",
        threshold=100.0,
        current_usage=85.0
    )
    
    # Query events
    events = audit_logger.query_events(
        event_type=AuditEventType.EVALUATION_START,
        limit=10
    )
    
    print(f"Found {len(events)} evaluation start events")
    
    # Get compliance summary
    summary = audit_logger.get_compliance_summary(days=7)
    print(f"Compliance score: {summary['compliance_score']:.2f}")
    print(f"Quota violations: {summary['compliance_metrics']['quota_violations']}")
