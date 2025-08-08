#!/usr/bin/env python3
"""
Setup script for Phase 8 Cost Governance system.
Initializes databases, creates default configuration, and verifies installation.
"""

import json
import os
import sqlite3
from pathlib import Path

from src.amp_eval.cost_tracking import CostTracker, BudgetLimits
from src.amp_eval.quota_enforcer import QuotaEnforcer
from src.amp_eval.context_monitor import ContextMonitor
from src.amp_eval.audit_logger import AuditLogger


def create_default_config():
    """Create default cost governance configuration."""
    config_path = "cost_limits.json"
    
    if not Path(config_path).exists():
        default_config = {
            "daily_cost_limit": 100.0,
            "monthly_cost_limit": 2000.0,
            "hourly_token_limit": 100000,
            "daily_token_limit": 1000000,
            "max_context_utilization": 0.9,
            "cost_alert_threshold": 0.8
        }
        
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"✅ Created default configuration: {config_path}")
    else:
        print(f"ℹ️  Configuration already exists: {config_path}")


def initialize_databases():
    """Initialize all databases for cost governance."""
    print("🗄️  Initializing databases...")
    
    # Cost tracking database
    cost_tracker = CostTracker()
    print("  ✅ Cost tracking database initialized")
    
    # Context monitoring database
    context_monitor = ContextMonitor()
    print("  ✅ Context monitoring database initialized")
    
    # Audit logging database
    audit_logger = AuditLogger()
    print("  ✅ Audit logging database initialized")
    
    return cost_tracker, context_monitor, audit_logger


def verify_installation():
    """Verify that all components are working correctly."""
    print("🔍 Verifying installation...")
    
    try:
        # Test cost tracking
        from src.amp_eval.cost_tracking import get_cost_tracker, TokenUsage
        tracker = get_cost_tracker()
        
        # Test quota enforcement
        from src.amp_eval.quota_enforcer import QuotaEnforcer
        enforcer = QuotaEnforcer(tracker)
        
        # Test context monitoring
        from src.amp_eval.context_monitor import ContextMonitor
        monitor = ContextMonitor()
        
        # Test audit logging
        from src.amp_eval.audit_logger import get_audit_logger
        audit_logger = get_audit_logger()
        
        print("  ✅ All components imported successfully")
        
        # Test basic functionality
        quota_summary = enforcer.get_quota_summary()
        print(f"  ✅ Quota system working (status: {quota_summary['compliance_status']})")
        
        usage_stats = tracker.get_usage_stats(days=1)
        print(f"  ✅ Cost tracking working (evaluations: {usage_stats.total_evaluations})")
        
        efficiency_report = monitor.get_context_efficiency_report(days=1)
        print(f"  ✅ Context monitoring working")
        
        compliance_summary = audit_logger.get_compliance_summary(days=1)
        print(f"  ✅ Audit logging working (score: {compliance_summary['compliance_score']:.2f})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Verification failed: {e}")
        return False


def create_example_usage():
    """Create example usage script."""
    example_script = """#!/usr/bin/env python3
\"\"\"
Example usage of the Phase 8 Cost Governance system.
\"\"\"

from src.amp_eval.cost_tracking import record_evaluation_cost, get_cost_tracker
from src.amp_eval.quota_enforcer import enforce_quota, QuotaException
from src.amp_eval.context_monitor import create_context_metrics_from_evaluation
from src.amp_eval.audit_logger import get_audit_logger

def example_evaluation_with_cost_tracking():
    \"\"\"Example of running an evaluation with full cost tracking.\"\"\"
    
    # Step 1: Check quota before running evaluation
    try:
        quota_check = enforce_quota(
            model="gpt-5",
            estimated_input_tokens=3000,
            estimated_output_tokens=1000,
            context_tokens=4000
        )
        print(f"✅ Quota check passed: {quota_check.message}")
        print(f"Estimated cost: ${quota_check.estimated_cost:.4f}")
        
    except QuotaException as e:
        print(f"❌ Quota check failed: {e}")
        return
    
    # Step 2: Simulate evaluation execution
    evaluation_id = "example_eval_001"
    task_id = "task_001"
    model = "gpt-5"
    
    # Simulate actual token usage (would come from real API response)
    actual_input_tokens = 2800
    actual_output_tokens = 1200
    context_used = 4000
    
    # Step 3: Record the cost
    cost_record = record_evaluation_cost(
        evaluation_id=evaluation_id,
        task_id=task_id,
        model=model,
        input_tokens=actual_input_tokens,
        output_tokens=actual_output_tokens,
        context_used=context_used,
        metadata={"evaluation_type": "example", "user": "demo"}
    )
    
    print(f"💰 Cost recorded: ${cost_record.total_cost:.4f}")
    print(f"🔍 Context utilization: {cost_record.context_utilization:.1%}")
    if cost_record.degradation_indicator:
        print(f"⚠️  Degradation detected: {cost_record.degradation_indicator}")
    
    # Step 4: Log audit events
    audit_logger = get_audit_logger()
    audit_logger.log_evaluation_complete(
        evaluation_id=evaluation_id,
        model=model,
        actual_cost=cost_record.total_cost,
        actual_tokens=cost_record.token_usage.total_tokens,
        success=True,
        grades={"accuracy": 0.85, "quality": 0.8}
    )
    
    # Step 5: Get updated usage statistics
    tracker = get_cost_tracker()
    stats = tracker.get_usage_stats(days=1)
    print(f"📊 Today's usage: ${stats.total_cost:.2f}, {stats.total_tokens:,} tokens")


if __name__ == "__main__":
    example_evaluation_with_cost_tracking()
"""
    
    with open("example_cost_governance.py", 'w') as f:
        f.write(example_script)
    
    print("✅ Created example usage script: example_cost_governance.py")


def main():
    """Main setup function."""
    print("🚀 Setting up Phase 8 Cost Governance System")
    print("=" * 50)
    
    # Create configuration
    create_default_config()
    
    # Initialize databases
    cost_tracker, context_monitor, audit_logger = initialize_databases()
    
    # Verify installation
    if verify_installation():
        print("\n✅ Phase 8 Cost Governance setup completed successfully!")
        
        # Create example script
        create_example_usage()
        
        print("\n📖 Quick Start:")
        print("1. Check status:           python -m src.amp_eval.cost_cli status")
        print("2. Check quotas:           python -m src.amp_eval.cost_cli quota")
        print("3. Generate report:        python -m src.amp_eval.cost_cli report --format csv --output report.csv")
        print("4. Analyze context:        python -m src.amp_eval.cost_cli context --model gpt-5")
        print("5. View audit trail:       python -m src.amp_eval.cost_cli audit")
        print("6. Clean old data:         python -m src.amp_eval.cost_cli cleanup")
        print("7. Run example:            python example_cost_governance.py")
        
        print("\n📚 Documentation: docs/PHASE8_COST_GOVERNANCE.md")
        
    else:
        print("\n❌ Setup failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
