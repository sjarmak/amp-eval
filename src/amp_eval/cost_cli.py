#!/usr/bin/env python3
"""
Command-line interface for cost governance and monitoring.
Provides tools for managing budgets, analyzing costs, and generating reports.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from .cost_tracking import CostTracker, get_cost_tracker
from .quota_enforcer import QuotaEnforcer
from .context_monitor import ContextMonitor
from .audit_logger import AuditLogger, get_audit_logger, AuditEventType


def format_currency(amount: float) -> str:
    """Format currency amount."""
    return f"${amount:.2f}"


def format_number(num: int) -> str:
    """Format large numbers with commas."""
    return f"{num:,}"


def print_usage_summary(tracker: CostTracker, days: int = 30):
    """Print usage summary for the specified period."""
    stats = tracker.get_usage_stats(days)
    print(f"\n📊 Usage Summary (Last {days} days)")
    print("=" * 50)
    print(f"Total Cost:         {format_currency(stats.total_cost)}")
    print(f"Total Tokens:       {format_number(stats.total_tokens)}")
    print(f"Total Evaluations:  {format_number(stats.total_evaluations)}")
    print(f"Avg Cost/Eval:      {format_currency(stats.average_cost_per_evaluation)}")
    print(f"Avg Tokens/Eval:    {format_number(int(stats.average_tokens_per_evaluation))}")
    print(f"Degradation Events: {format_number(stats.degradation_events)}")
    print(f"High Context Events: {format_number(stats.high_context_usage_events)}")
    
    if stats.cost_by_model:
        print(f"\n💰 Cost by Model:")
        for model, cost in sorted(stats.cost_by_model.items(), key=lambda x: x[1], reverse=True):
            print(f"  {model:12} {format_currency(cost)}")
    
    if stats.tokens_by_model:
        print(f"\n🔢 Tokens by Model:")
        for model, tokens in sorted(stats.tokens_by_model.items(), key=lambda x: x[1], reverse=True):
            print(f"  {model:12} {format_number(tokens)}")


def print_quota_status(enforcer: QuotaEnforcer):
    """Print current quota status."""
    summary = enforcer.get_quota_summary()
    print(f"\n🚦 Quota Status")
    print("=" * 50)
    
    # Daily budget
    daily = summary["daily_budget"]
    print(f"Daily Budget:    {format_currency(daily['used'])} / {format_currency(daily['limit'])}")
    print(f"  Remaining:     {format_currency(daily['remaining'])}")
    print(f"  Utilization:   {daily['utilization']:.1%}")
    
    # Hourly tokens
    hourly = summary["hourly_tokens"]
    print(f"\nHourly Tokens:   {format_number(hourly['used'])} / {format_number(hourly['limit'])}")
    print(f"  Remaining:     {format_number(hourly['remaining'])}")
    print(f"  Utilization:   {hourly['utilization']:.1%}")
    
    # Monthly budget
    monthly = summary["monthly_budget"]
    print(f"\nMonthly Budget:  {format_currency(monthly['used'])} / {format_currency(monthly['limit'])}")
    print(f"  Remaining:     {format_currency(monthly['remaining'])}")
    print(f"  Utilization:   {monthly['utilization']:.1%}")
    
    # Compliance status
    status = summary["compliance_status"]
    status_emoji = "✅" if status == "compliant" else "⚠️" if summary["warnings"] else "❌"
    print(f"\nCompliance:      {status_emoji} {status}")
    
    if summary["warnings"]:
        print("Warnings:")
        for warning in summary["warnings"]:
            print(f"  ⚠️  {warning}")
    
    if summary["errors"]:
        print("Errors:")
        for error in summary["errors"]:
            print(f"  ❌ {error}")


def print_context_analysis(monitor: ContextMonitor, model: str, days: int = 30):
    """Print context usage analysis."""
    report = monitor.analyze_degradation_patterns(model, days)
    
    print(f"\n🔍 Context Analysis - {model} (Last {days} days)")
    print("=" * 50)
    print(f"Total Evaluations:   {format_number(report.total_evaluations)}")
    print(f"Degraded Evaluations: {format_number(report.degraded_evaluations)}")
    print(f"Degradation Rate:    {report.degradation_rate:.1%}")
    print(f"Wasted Tokens:       {format_number(report.total_wasted_tokens)}")
    print(f"Estimated Waste Cost: {format_currency(report.estimated_wasted_cost)}")
    
    if report.performance_by_tier:
        print(f"\n📈 Performance by Context Tier:")
        for tier, stats in report.performance_by_tier.items():
            print(f"  {tier.upper():12} Count: {stats['count']:4d}, "
                  f"Accuracy: {stats['avg_accuracy']:.2f}, "
                  f"Quality: {stats['avg_quality']:.2f}")
    
    if report.suggestions:
        print(f"\n💡 Optimization Suggestions:")
        for i, suggestion in enumerate(report.suggestions, 1):
            print(f"  {i}. [{suggestion.priority.upper()}] {suggestion.description}")
            print(f"     Expected savings: {format_number(suggestion.expected_savings)} tokens")
            print(f"     Implementation effort: {suggestion.implementation_effort}")


def print_compliance_report(audit_logger: AuditLogger, days: int = 30):
    """Print compliance report from audit logs."""
    summary = audit_logger.get_compliance_summary(days)
    
    print(f"\n📋 Compliance Report ({summary['time_period']})")
    print("=" * 50)
    print(f"Compliance Score:    {summary['compliance_score']:.2f} / 1.00")
    
    metrics = summary['compliance_metrics']
    print(f"Quota Violations:    {metrics['quota_violations']}")
    print(f"Budget Alerts:       {metrics['budget_alerts']}")
    print(f"Degradation Events:  {metrics['degradation_events']}")
    print(f"Total Cost Impact:   {format_currency(metrics['total_cost_impact'])}")
    
    if summary['event_counts']:
        print(f"\n📊 Event Counts:")
        for event_type, count in sorted(summary['event_counts'].items()):
            print(f"  {event_type:20} {count:6d}")


def cmd_status(args):
    """Show current cost and quota status."""
    tracker = get_cost_tracker()
    enforcer = QuotaEnforcer(tracker)
    
    print_usage_summary(tracker, args.days)
    print_quota_status(enforcer)


def cmd_report(args):
    """Generate cost report."""
    tracker = get_cost_tracker()
    
    if args.format == 'csv':
        tracker.generate_cost_report(args.output, days=args.days)
        print(f"✅ Cost report generated: {args.output}")
    else:
        print_usage_summary(tracker, args.days)


def cmd_context(args):
    """Analyze context usage patterns."""
    monitor = ContextMonitor()
    
    if args.model:
        print_context_analysis(monitor, args.model, args.days)
    else:
        # Show efficiency report for all models
        efficiency = monitor.get_context_efficiency_report(days=args.days)
        print(f"\n🎯 Context Efficiency Report ({efficiency['time_period']})")
        print("=" * 50)
        
        for tier, stats in efficiency['efficiency_by_tier'].items():
            print(f"{tier.upper():12} Count: {stats['count']:4d}, "
                  f"Accuracy: {stats['avg_accuracy']:.2f}, "
                  f"Latency: {stats['avg_latency']:.0f}ms, "
                  f"Truncation: {stats['truncation_rate']:.1%}")
        
        print(f"\nRecommendation: {efficiency['recommendation']}")


def cmd_quota(args):
    """Check quota compliance and limits."""
    tracker = get_cost_tracker()
    enforcer = QuotaEnforcer(tracker)
    
    if args.check:
        # Check quota for specific evaluation
        try:
            quota_check = enforcer.check_quota_compliance(
                model=args.model,
                estimated_input_tokens=args.input_tokens,
                estimated_output_tokens=args.output_tokens,
                context_tokens=args.context_tokens
            )
            
            print(f"\n🔍 Quota Check - {args.model}")
            print("=" * 50)
            print(f"Status:              {quota_check.status.value}")
            print(f"Message:             {quota_check.message}")
            print(f"Estimated Cost:      {format_currency(quota_check.estimated_cost)}")
            print(f"Estimated Tokens:    {format_number(quota_check.estimated_tokens)}")
            print(f"Context Utilization: {quota_check.context_utilization:.1%}")
            print(f"Remaining Budget:    {format_currency(quota_check.remaining_daily_budget)}")
            print(f"Remaining Tokens:    {format_number(quota_check.remaining_hourly_tokens)}")
        
        except Exception as e:
            print(f"❌ Error checking quota: {e}")
    else:
        print_quota_status(enforcer)


def cmd_audit(args):
    """Audit and compliance operations."""
    audit_logger = get_audit_logger()
    
    if args.export:
        audit_logger.export_audit_trail(args.export, days=args.days)
        print(f"✅ Audit trail exported: {args.export}")
    elif args.compliance:
        print_compliance_report(audit_logger, args.days)
    else:
        # Show recent events
        events = audit_logger.query_events(limit=args.limit)
        
        print(f"\n📜 Recent Audit Events (Last {args.limit})")
        print("=" * 80)
        
        for event in events:
            timestamp = datetime.fromtimestamp(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{timestamp} [{event['event_type']:20}] {event['component']:15} "
                  f"{event['model']:10} {format_currency(event['cost_impact'])}")


def cmd_cleanup(args):
    """Clean up old data."""
    if args.confirm or input("This will permanently delete old records. Continue? (y/N): ").lower() == 'y':
        tracker = get_cost_tracker()
        audit_logger = get_audit_logger()
        monitor = ContextMonitor()
        
        # Clean up cost records
        cost_deleted = tracker.cleanup_old_records(args.retention_days)
        print(f"✅ Deleted {cost_deleted} old cost records")
        
        # Clean up audit logs
        audit_deleted = audit_logger.cleanup_old_events()
        print(f"✅ Deleted {audit_deleted} old audit events")
        
        # Clean up context metrics (if database exists)
        try:
            import sqlite3
            with sqlite3.connect(monitor.db_path) as conn:
                cutoff = (datetime.now() - timedelta(days=args.retention_days)).timestamp()
                cursor = conn.execute("DELETE FROM context_metrics WHERE timestamp < ?", (cutoff,))
                context_deleted = cursor.rowcount
            print(f"✅ Deleted {context_deleted} old context metrics")
        except Exception as e:
            print(f"⚠️  Context cleanup failed: {e}")
    else:
        print("Cleanup cancelled")


def cmd_config(args):
    """Manage configuration."""
    if args.show:
        # Show current configuration
        tracker = get_cost_tracker()
        limits = tracker.budget_limits
        
        print(f"\n⚙️  Current Configuration")
        print("=" * 50)
        print(f"Daily Cost Limit:         {format_currency(limits.daily_cost_limit)}")
        print(f"Monthly Cost Limit:       {format_currency(limits.monthly_cost_limit)}")
        print(f"Hourly Token Limit:       {format_number(limits.hourly_token_limit)}")
        print(f"Daily Token Limit:        {format_number(limits.daily_token_limit)}")
        print(f"Max Context Utilization:  {limits.max_context_utilization:.1%}")
        print(f"Cost Alert Threshold:     {limits.cost_alert_threshold:.1%}")
    
    elif args.set:
        # Update configuration
        config_file = args.config or "cost_limits.json"
        
        try:
            # Load existing config
            config = {}
            if Path(config_file).exists():
                with open(config_file) as f:
                    config = json.load(f)
            
            # Parse key=value pairs
            for setting in args.set:
                if '=' not in setting:
                    print(f"❌ Invalid setting format: {setting} (use key=value)")
                    continue
                
                key, value = setting.split('=', 1)
                
                # Convert value to appropriate type
                try:
                    if '.' in value:
                        config[key] = float(value)
                    else:
                        config[key] = int(value)
                except ValueError:
                    config[key] = value
            
            # Save updated config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Configuration updated: {config_file}")
            
        except Exception as e:
            print(f"❌ Failed to update configuration: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cost governance and monitoring CLI for amp-eval",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show current cost and quota status')
    status_parser.add_argument('--days', type=int, default=30, help='Time period in days (default: 30)')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate cost reports')
    report_parser.add_argument('--days', type=int, default=30, help='Time period in days (default: 30)')
    report_parser.add_argument('--format', choices=['csv', 'console'], default='console', help='Report format')
    report_parser.add_argument('--output', help='Output file for CSV format')
    
    # Context command
    context_parser = subparsers.add_parser('context', help='Analyze context usage patterns')
    context_parser.add_argument('--model', help='Specific model to analyze')
    context_parser.add_argument('--days', type=int, default=30, help='Time period in days (default: 30)')
    
    # Quota command
    quota_parser = subparsers.add_parser('quota', help='Check quota compliance')
    quota_parser.add_argument('--check', action='store_true', help='Check quota for specific evaluation')
    quota_parser.add_argument('--model', default='gpt-5', help='Model name (default: gpt-5)')
    quota_parser.add_argument('--input-tokens', type=int, default=3000, help='Estimated input tokens')
    quota_parser.add_argument('--output-tokens', type=int, default=1000, help='Estimated output tokens')
    quota_parser.add_argument('--context-tokens', type=int, default=0, help='Context tokens used')
    
    # Audit command
    audit_parser = subparsers.add_parser('audit', help='Audit and compliance operations')
    audit_parser.add_argument('--export', help='Export audit trail to file')
    audit_parser.add_argument('--compliance', action='store_true', help='Show compliance report')
    audit_parser.add_argument('--days', type=int, default=30, help='Time period in days (default: 30)')
    audit_parser.add_argument('--limit', type=int, default=20, help='Number of events to show (default: 20)')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--retention-days', type=int, default=90, help='Retention period in days (default: 90)')
    cleanup_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    config_parser.add_argument('--set', nargs='*', help='Set configuration values (key=value)')
    config_parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'status':
            cmd_status(args)
        elif args.command == 'report':
            cmd_report(args)
        elif args.command == 'context':
            cmd_context(args)
        elif args.command == 'quota':
            cmd_quota(args)
        elif args.command == 'audit':
            cmd_audit(args)
        elif args.command == 'cleanup':
            cmd_cleanup(args)
        elif args.command == 'config':
            cmd_config(args)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
