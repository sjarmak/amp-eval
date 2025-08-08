# Dashboard Interpretation Guide

## 🎯 Overview

The Amp Evaluation Dashboard provides real-time insights into model performance, cost efficiency, and system health. This guide helps you interpret metrics, identify trends, and take appropriate actions.

## 📊 Dashboard Sections

### 1. Executive Summary (Top Panel)

**Key Performance Indicators (KPIs)**

| Metric | Good Range | Warning | Critical | Action Required |
|--------|------------|---------|----------|-----------------|
| **Overall Accuracy** | >85% | 80-85% | <80% | Review failing evaluations |
| **Token Efficiency** | <10K avg | 10-15K | >15K | Optimize prompts |
| **Monthly Cost** | <$500 | $500-800 | >$800 | Review model usage |
| **Oracle Usage** | <5% | 5-10% | >10% | Check triggering logic |

**Status Indicators**
- 🟢 **Green**: All systems normal
- 🟡 **Yellow**: Monitoring required
- 🔴 **Red**: Immediate action needed

### 2. Model Performance Matrix

**Accuracy by Model**
```
┌─────────────┬──────────┬──────────┬──────────┐
│ Model       │ Tool Call│ Bug Fix  │ Oracle   │
├─────────────┼──────────┼──────────┼──────────┤
│ Sonnet-4    │   72%    │   68%    │   N/A    │
│ GPT-5       │   87%    │   82%    │   N/A    │
│ o3 (Oracle) │   94%    │   88%    │   79%    │
└─────────────┴──────────┴──────────┴──────────┘
```

**Interpretation:**
- **Above target**: Model performing well for this task type
- **Below target**: May need prompt engineering or different model
- **Declining trend**: Investigate recent changes or model updates

### 3. Cost Analysis Panel

**Token Usage Trends**
- **Daily tokens**: Track consumption patterns
- **Cost per evaluation**: Identify expensive test suites
- **Model distribution**: Ensure appropriate model selection

**Budget Alerts**
```
Current Month: $347 / $500 budget (69%)
Projected: $523 (105% - OVER BUDGET)
```

**Cost Optimization Recommendations:**
- Switch expensive evaluations to Sonnet-4
- Reduce oracle trigger sensitivity
- Archive unused evaluation suites

### 4. Evaluation Suite Performance

**Per-Suite Breakdown**

| Suite | Runs | Success Rate | Avg Tokens | Cost/Month |
|-------|------|-------------|------------|------------|
| tool_calling_micro | 156 | 94% | 2.1K | $89 |
| single_file_fix | 45 | 78% | 8.7K | $203 |
| oracle_knowledge | 12 | 83% | 24.3K | $187 |

**Red Flags:**
- **Low success rate (<70%)**: Review evaluation design
- **High token usage (>15K)**: Optimize prompts
- **Declining performance**: Check for regressions

### 5. Real-Time Monitoring

**Current Runs**
```
[Running] oracle_knowledge_suite - 45% complete
[Queued]  tool_calling_micro (x3)
[Failed]  single_file_fix - token limit exceeded
```

**System Health**
- **API Rate Limits**: Current usage vs. limits
- **Queue Depth**: Number of pending evaluations
- **Error Rate**: Failed runs requiring attention

## 🔍 Deep Dive Analysis

### Performance Regression Detection

**Automated Alerts Trigger When:**
- Accuracy drops >5% from 7-day average
- Token usage increases >20% week-over-week
- Oracle usage exceeds 10% of total runs
- Any evaluation suite fails >3 times consecutively

**Investigation Workflow:**
1. **Identify affected timeframe**: When did the regression start?
2. **Check recent changes**: Code deployments, evaluation updates
3. **Compare model versions**: Has the underlying model changed?
4. **Review failed prompts**: Are failures consistent or random?

### Cost Anomaly Analysis

**Common Cost Spikes:**

1. **Oracle Overuse**
   - **Symptom**: o3 usage >10%
   - **Cause**: Trigger phrase too broad
   - **Fix**: Tighten oracle conditions in config

2. **Model Upgrade Cascade**
   - **Symptom**: GPT-5 usage increased dramatically
   - **Cause**: diff_lines threshold too low
   - **Fix**: Adjust upgrade rules in agent_settings.yaml

3. **Runaway Evaluations**
   - **Symptom**: Single suite consuming >50% of budget
   - **Cause**: Infinite retry loops or oversized prompts
   - **Fix**: Implement circuit breakers

### Trend Analysis

**Week-over-Week Comparison**
```
                This Week    Last Week    Change
Accuracy        84.2%        86.1%        -1.9% ⚠️
Avg Tokens      12.4K        11.8K        +5.1%
Total Cost      $127         $119         +6.7%
Oracle %        3.2%         2.8%         +0.4%
```

**Monthly Trends**
- Track seasonal patterns (e.g., higher usage during sprints)
- Identify gradual degradation vs. sudden drops
- Correlate with product development cycles

## 🚨 Alert Interpretation

### Critical Alerts (Immediate Action)

**"Budget Overrun Imminent"**
- **Trigger**: Projected monthly cost >120% of budget
- **Action**: Pause non-critical evaluations, review queue
- **Timeline**: Within 1 hour

**"Model Performance Cliff"**
- **Trigger**: Any model accuracy <60%
- **Action**: Investigate prompts, check model availability
- **Timeline**: Within 2 hours

**"Oracle Runaway"**
- **Trigger**: o3 usage >15% of daily runs
- **Action**: Review trigger conditions, manual intervention
- **Timeline**: Within 30 minutes

### Warning Alerts (Monitor Closely)

**"Accuracy Degradation"**
- **Trigger**: 5-10% drop in success rate
- **Action**: Schedule investigation, not urgent
- **Timeline**: Within 24 hours

**"Token Efficiency Drop"**
- **Trigger**: 15-25% increase in token usage
- **Action**: Review recent prompt changes
- **Timeline**: Within 48 hours

### Info Alerts (Awareness Only)

**"New Evaluation Suite Added"**
**"Model Usage Shift"**
**"Successful Integration Test"**

## 📈 Optimization Strategies

### Performance Optimization

1. **Prompt Engineering**
   - Shorten verbose prompts
   - Use more specific instructions
   - Remove redundant context

2. **Model Selection Tuning**
   - Adjust upgrade thresholds
   - Review oracle trigger phrases
   - A/B test model assignments

3. **Evaluation Suite Cleanup**
   - Archive unused evaluations
   - Merge duplicate test cases
   - Remove low-value scenarios

### Cost Optimization

1. **Smart Scheduling**
   - Run expensive suites during off-peak
   - Batch evaluations to reduce overhead
   - Use cached results where appropriate

2. **Budget Controls**
   - Set per-suite monthly limits
   - Implement progressive throttling
   - Auto-pause on budget breach

3. **Model Efficiency**
   - Use smallest viable model for each task
   - Implement result caching
   - Reduce oracle dependency

## 🔧 Troubleshooting Common Issues

### Dashboard Not Loading

1. Check Streamlit service status
2. Verify database connectivity
3. Clear browser cache
4. Check error logs in `/logs/dashboard.log`

### Metrics Appear Stale

1. Confirm evaluation jobs are running
2. Check data pipeline status
3. Verify database writes
4. Review aggregation schedule

### Cost Calculations Wrong

1. Verify token counting accuracy
2. Check model pricing updates
3. Review usage attribution logic
4. Cross-reference with provider bills

## 📚 Advanced Features

### Custom Metrics

Define team-specific KPIs:
```yaml
custom_metrics:
  - name: "Frontend Test Coverage"
    query: "suite:frontend_eval"
    target: 90
  - name: "API Response Quality"  
    query: "model:gpt-5 AND task:api_*"
    target: 85
```

### Drill-Down Analysis

- Click any metric to view detailed breakdown
- Filter by date range, model, or evaluation suite
- Export data for external analysis

### Historical Comparisons

- Compare current performance to baseline
- Track improvement over time
- Identify best-performing model combinations

---

**Remember**: The dashboard is your early warning system. Regular monitoring prevents small issues from becoming expensive problems.
