# Cost Governance & Monitoring System

## Overview

This document describes the comprehensive cost governance system implemented for the amp-eval project. The system provides real-time cost tracking, quota enforcement, context window monitoring, and performance degradation assessment based on Amp token usage.

## System Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Cost Tracker     │────│  Quota Enforcer     │────│  Context Monitor    │
│                     │    │                     │    │                     │
│ • Token tracking    │    │ • Budget limits     │    │ • Context usage     │
│ • API cost calc     │    │ • Evaluation gates  │    │ • Degradation det.  │
│ • Audit logging     │    │ • Warning system    │    │ • Optimization     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       │
                    ┌─────────────────────┐
                    │   SQLite Database   │
                    │                     │
                    │ • cost_records      │
                    │ • context_metrics   │
                    │ • audit_logs        │
                    └─────────────────────┘
```

## Model Cost Configuration

### Current Model Pricing (per 1K tokens)

| Model    | Input Cost | Output Cost | Context Window | Max Output |
|----------|------------|-------------|----------------|------------|
| sonnet-4 | $0.003     | $0.015      | 200,000        | 4,096      |
| gpt-5    | $0.010     | $0.030      | 128,000        | 4,096      |
| o3       | $0.040     | $0.120      | 200,000        | 65,536     |
| gpt-4o   | $0.0025    | $0.010      | 128,000        | 16,384     |

### Cost Calculation Formula

```python
input_cost = (input_tokens / 1000) * input_cost_per_1k
output_cost = (output_tokens / 1000) * output_cost_per_1k
total_cost = input_cost + output_cost
```

## Budget Limits & Quotas

### Default Budget Configuration

```json
{
    "daily_cost_limit": 100.0,       // USD per day
    "monthly_cost_limit": 2000.0,    // USD per month
    "hourly_token_limit": 100000,    // Tokens per hour
    "daily_token_limit": 1000000,    // Tokens per day
    "max_context_utilization": 0.9,  // 90% of context window
    "cost_alert_threshold": 0.8      // Alert at 80% of budget
}
```

### Quota Enforcement Levels

1. **ALLOWED**: Normal operation, all checks pass
2. **WARNING**: Approaching limits, evaluation proceeds with warning
3. **BLOCKED**: Limits exceeded, evaluation prevented

## Cost Tracking System

### Core Components

#### 1. CostTracker Class
- Real-time cost calculation and tracking
- SQLite database storage for audit trail
- Automatic budget limit monitoring
- 90-day retention policy

#### 2. Key Features
- **Token Usage Tracking**: Input/output tokens with accurate cost calculation
- **Context Window Monitoring**: Track utilization percentage and degradation
- **Budget Enforcement**: Hard limits with warning thresholds
- **Audit Logging**: Complete trail of all evaluation costs
- **Performance Correlation**: Link costs to quality metrics

### Usage Example

```python
from amp_eval.cost_tracking import record_evaluation_cost, get_cost_tracker

# Record evaluation cost
cost_record = record_evaluation_cost(
    evaluation_id="eval_001",
    task_id="task_001", 
    model="gpt-5",
    input_tokens=3000,
    output_tokens=1000,
    context_used=4000,
    metadata={"evaluation_type": "tool_calling"}
)

# Get usage statistics
tracker = get_cost_tracker()
stats = tracker.get_usage_stats(days=30)
print(f"Monthly cost: ${stats.total_cost:.2f}")
```

## Quota Enforcement System

### QuotaEnforcer Class

Prevents evaluations from running if they would exceed budget limits.

```python
from amp_eval.quota_enforcer import enforce_quota, QuotaException

try:
    quota_check = enforce_quota(
        model="gpt-5",
        estimated_input_tokens=3000,
        estimated_output_tokens=1000,
        context_tokens=4000
    )
    print(f"Estimated cost: ${quota_check.estimated_cost:.4f}")
except QuotaException as e:
    print(f"Evaluation blocked: {e.quota_check.message}")
```

### Pre-Evaluation Checks

Before any evaluation runs:
1. Estimate token usage and cost
2. Check against hourly/daily limits
3. Assess context window utilization
4. Allow/warn/block based on thresholds

## Context Window Monitoring

### Performance Degradation Assessment

#### Performance Tiers

| Tier     | Context Usage | Expected Performance | Action Required |
|----------|---------------|---------------------|-----------------|
| OPTIMAL  | 0-60%         | Full performance    | None           |
| GOOD     | 60-75%        | Minor degradation   | Monitor        |
| DEGRADED | 75-90%        | Noticeable issues   | Optimize       |
| POOR     | 90-95%        | Significant loss    | Urgent action  |
| CRITICAL | 95%+          | Severe degradation  | Immediate fix  |

#### Degradation Indicators

1. **Truncation Detection**: Response cut off mid-sentence
2. **Repetition Detection**: Repeated phrases or patterns
3. **Coherence Assessment**: Sentence structure and flow quality
4. **Accuracy Correlation**: Performance vs context usage

### Context Optimization Suggestions

```python
from amp_eval.context_monitor import ContextMonitor

monitor = ContextMonitor()
report = monitor.analyze_degradation_patterns("gpt-5", days=30)

for suggestion in report.suggestions:
    print(f"Priority {suggestion.priority}: {suggestion.description}")
    print(f"Expected savings: {suggestion.expected_savings} tokens")
```

## Audit & Compliance

### Data Retention

- **Cost Records**: 90 days automatic retention
- **Context Metrics**: 90 days automatic retention  
- **Audit Logs**: PII-free, complete transaction history
- **Cleanup**: Automated deletion of expired records

### Compliance Monitoring

```python
# Check current compliance status
compliance = tracker.check_quota_compliance()
print(f"Status: {compliance['status']}")
print(f"Warnings: {compliance['warnings']}")
print(f"Errors: {compliance['errors']}")
```

### Monthly Cost Reports

Generate detailed CSV reports for financial analysis:

```python
tracker.generate_cost_report("monthly_report.csv", days=30)
```

Report includes:
- Per-evaluation cost breakdown
- Model usage patterns
- Context utilization trends
- Degradation event tracking

## Integration with Existing Systems

### amp_runner.py Integration

```python
from amp_eval.cost_tracking import record_evaluation_cost
from amp_eval.quota_enforcer import enforce_quota
from amp_eval.context_monitor import create_context_metrics_from_evaluation

class AmpRunner:
    def run_evaluation(self, task):
        # Pre-check quotas
        quota_check = enforce_quota(
            model=task.model,
            estimated_input_tokens=task.estimated_input,
            estimated_output_tokens=task.estimated_output
        )
        
        # Run evaluation
        result = self._execute_evaluation(task)
        
        # Record costs
        cost_record = record_evaluation_cost(
            evaluation_id=task.eval_id,
            task_id=task.task_id,
            model=task.model,
            input_tokens=result.usage.input_tokens,
            output_tokens=result.usage.output_tokens,
            context_used=result.usage.total_tokens
        )
        
        # Track context usage
        context_metrics = create_context_metrics_from_evaluation(
            evaluation_id=task.eval_id,
            task_id=task.task_id,
            model=task.model,
            prompt_data=task.prompt_data,
            response_data=result.response_data,
            performance_scores=result.grades
        )
        
        return result
```

### Rate Limiter Integration

The existing `rate_limiter.py` integrates seamlessly:

```python
from amp_eval.cost_tracking import get_cost_tracker

# Update existing circuit breaker to use new cost tracking
@rate_limited(estimated_tokens=5000, estimated_cost=0.05)
def make_api_call():
    # API call logic
    pass
```

## Monitoring Dashboard Integration

### Key Metrics for Dashboard

```python
# Daily cost summary
{
    "daily_cost": 45.67,
    "daily_budget": 100.0,
    "daily_utilization": 0.457,
    "trend": "increasing"
}

# Model efficiency
{
    "gpt-5": {
        "cost_per_evaluation": 0.0234,
        "tokens_per_evaluation": 1567,
        "success_rate": 0.94
    }
}

# Context health
{
    "avg_context_utilization": 0.67,
    "degradation_rate": 0.12,
    "optimization_opportunities": 3
}
```

### Alert Conditions

1. **Daily budget >80%**: Warning notification
2. **Daily budget >100%**: Error alert + evaluation pause
3. **Hourly token limit exceeded**: Rate limiting activated
4. **High degradation rate (>30%)**: Context optimization alert
5. **Critical context usage**: Immediate optimization required

## Command Line Tools

### Cost Report Generation

```bash
# Generate monthly cost report
python -m amp_eval.cost_tracking --report monthly_costs.csv --days 30

# Check quota status  
python -m amp_eval.quota_enforcer --status

# Analyze context efficiency
python -m amp_eval.context_monitor --efficiency-report gpt-5 --days 7
```

### Configuration Management

```bash
# Update budget limits
echo '{"daily_cost_limit": 150.0}' > cost_limits.json

# Clean up old records
python -m amp_eval.cost_tracking --cleanup --retention-days 90
```

## Security & Privacy

### Data Protection

- **No PII**: Cost tracking stores only technical metrics
- **Encrypted Storage**: Database encryption at rest
- **Access Control**: Role-based access to cost data
- **Audit Trail**: Complete log of all cost-related operations

### Rate Limiting Integration

- Circuit breaker patterns for cost protection
- Exponential backoff with cost awareness
- Global cost limits across all evaluation runners

## Troubleshooting

### Common Issues

1. **"Daily budget exceeded"**
   - Check current usage: `tracker.get_usage_stats(days=1)`
   - Review high-cost evaluations in database
   - Consider increasing budget or optimizing prompts

2. **"Context utilization critical"**
   - Run degradation analysis: `monitor.analyze_degradation_patterns()`
   - Implement suggested optimizations
   - Split large prompts into smaller chunks

3. **"Quota enforcement blocking evaluations"**
   - Check quota status: `enforcer.get_quota_summary()`
   - Wait for quota reset or increase limits
   - Review evaluation scheduling

### Performance Optimization

1. **Database Tuning**
   - Regular VACUUM operations
   - Index optimization for time-series queries
   - Partition by month for large datasets

2. **Memory Management**
   - Batch cost record inserts
   - Lazy loading of historical data
   - Cache frequently accessed quotas

3. **Cost Reduction Strategies**
   - Prompt template optimization
   - Context window management
   - Model selection based on cost/performance ratio

## Future Enhancements

### Planned Features

1. **Real-time Cost Streaming**: WebSocket updates for live monitoring
2. **Predictive Budgeting**: ML-based cost forecasting
3. **Multi-tenant Support**: Organization-level cost isolation
4. **Advanced Analytics**: Anomaly detection and cost optimization
5. **Integration APIs**: External billing and monitoring systems

### Metrics Expansion

1. **Quality-Adjusted Costs**: Cost per quality unit
2. **Context Efficiency Ratios**: Performance per token
3. **Model ROI Analysis**: Value generation per dollar spent
4. **Optimization Impact Tracking**: Savings from improvements

This comprehensive cost governance system ensures financial control while maintaining visibility into model performance and usage patterns.
