# Model Addition Tutorial

## 🎯 Overview

This tutorial guides you through adding a new AI model to the Amp Evaluation Suite. Whether integrating OpenAI's latest model, Anthropic updates, or local models, follow this systematic approach.

## 📋 Prerequisites

- [ ] API access to the new model
- [ ] Cost estimates for the model ($/token)
- [ ] Understanding of model capabilities and limitations
- [ ] Access to the amp-eval codebase

## 🏗️ Integration Steps

### Step 1: Update Model Configuration

**File**: [`config/agent_settings.yaml`](../config/agent_settings.yaml)

Add your new model to the configuration:

```yaml
models:
  # Existing models...
  your-new-model:
    provider: "openai"  # or "anthropic", "local", etc.
    api_name: "gpt-5-turbo-preview"  # Actual API model name
    max_tokens: 32000
    cost_per_token: 0.00015  # Input token cost
    cost_per_output_token: 0.0006  # Output token cost
    context_window: 128000
    capabilities:
      - "tool_calling"
      - "code_generation"
      - "reasoning"
    upgrade_conditions:
      diff_lines: 50  # Auto-upgrade threshold
      touched_files: 3
```

**Configuration Options:**

| Field | Description | Example |
|-------|-------------|---------|
| `provider` | API provider | `"openai"`, `"anthropic"`, `"local"` |
| `api_name` | Exact model name for API calls | `"gpt-4-turbo"` |
| `max_tokens` | Maximum tokens per request | `32000` |
| `cost_per_token` | Input token cost in USD | `0.00015` |
| `cost_per_output_token` | Output token cost in USD | `0.0006` |
| `context_window` | Total context size | `128000` |
| `capabilities` | List of model features | `["tool_calling"]` |

### Step 2: Implement Model Adapter

**File**: [`src/amp_eval/adapters/model_runner.py`](../src/amp_eval/adapters/)

Add support for your model provider:

```python
class YourProviderRunner(BaseModelRunner):
    def __init__(self, model_config: dict):
        self.model_config = model_config
        self.client = YourProviderClient(
            api_key=os.getenv("YOUR_PROVIDER_API_KEY")
        )
    
    def call_model(self, prompt: str, tools: list = None) -> dict:
        """Make API call to your model provider."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_config["api_name"],
                messages=[{"role": "user", "content": prompt}],
                tools=tools,
                max_tokens=self.model_config["max_tokens"]
            )
            
            return {
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls,
                "tokens_used": response.usage.total_tokens,
                "cost": self._calculate_cost(response.usage)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_cost(self, usage) -> float:
        """Calculate cost based on token usage."""
        input_cost = usage.prompt_tokens * self.model_config["cost_per_token"]
        output_cost = usage.completion_tokens * self.model_config["cost_per_output_token"]
        return input_cost + output_cost
```

### Step 3: Update Model Selection Logic

**File**: [`src/amp_eval/core/model_selector.py`](../src/amp_eval/core/)

Add your model to the selection logic:

```python
def select_model(self, context: dict) -> str:
    """Select appropriate model based on context and rules."""
    
    # Oracle trigger (highest priority)
    if self._is_oracle_trigger(context.get("prompt", "")):
        return "o3"
    
    # CLI/environment override
    if override := self._get_model_override():
        return override
    
    # Your new model conditions
    if self._should_use_your_model(context):
        return "your-new-model"
    
    # Existing upgrade conditions
    if self._should_upgrade_to_gpt5(context):
        return "gpt-5"
    
    return "sonnet-4"  # Default

def _should_use_your_model(self, context: dict) -> bool:
    """Define when to use your new model."""
    # Example: Use for specific task types
    if context.get("task_type") == "complex_reasoning":
        return True
    
    # Example: Use for large contexts
    if context.get("context_size", 0) > 50000:
        return True
    
    return False
```

### Step 4: Add Environment Variables

**File**: [`.env.example`](../.env.example)

```bash
# Existing keys...
YOUR_PROVIDER_API_KEY=your_api_key_here
```

**File**: [`docker-compose.prod.yml`](../docker-compose.prod.yml)

```yaml
environment:
  - YOUR_PROVIDER_API_KEY=${YOUR_PROVIDER_API_KEY}
```

### Step 5: Create Test Evaluation

Create a small test to validate your model integration:

**File**: `evals/test_your_model.yaml`

```yaml
name: test_your_model
description: "Validation test for your new model integration"
registry_path: amp-eval/adapters
tasks:
  - id: "simple_tool_call"
    prompt: "List files in the current directory using available tools"
    expected_tool: "list_directory"
    expected_args: {"path": "."}
    grading_criteria:
      tool_correct: 50
      args_present: 25
      args_correct: 25
    metadata:
      force_model: "your-new-model"  # Force usage for testing

  - id: "reasoning_task"
    prompt: "Explain the time complexity of bubble sort and suggest an improvement"
    expected_keywords: ["O(n^2)", "comparison", "swap"]
    grading_criteria:
      keywords_present: 60
      explanation_quality: 40
    metadata:
      force_model: "your-new-model"
```

### Step 6: Update Cost Tracking

**File**: [`src/amp_eval/monitoring/cost_tracker.py`](../src/amp_eval/monitoring/)

```python
PRICING = {
    # Existing models...
    "your-new-model": {
        "input_cost": 0.00015,
        "output_cost": 0.0006,
        "provider": "your_provider"
    }
}

def calculate_monthly_projection(self) -> dict:
    """Project monthly costs based on current usage."""
    projections = {}
    
    for model_name in ["sonnet-4", "gpt-5", "o3", "your-new-model"]:
        usage = self.get_model_usage(model_name)
        projections[model_name] = self._project_cost(usage)
    
    return projections
```

### Step 7: Test Integration

Run validation tests to ensure everything works:

```bash
# Test model selection logic
python -m pytest tests/test_model_selector.py -v

# Test API integration
python -m pytest tests/test_your_provider_runner.py -v

# Run smoke test with your model
AMP_MODEL=your-new-model make test-smoke

# Run your validation evaluation
amp-eval suite evals/test_your_model.yaml
```

## 🔍 Validation Checklist

### API Integration
- [ ] Model responds to simple prompts
- [ ] Tool calling works correctly (if supported)
- [ ] Error handling works for rate limits/failures
- [ ] Cost calculation is accurate

### Configuration
- [ ] Model appears in selection logic
- [ ] Upgrade conditions work as expected
- [ ] Environment variables are documented
- [ ] Configuration validates correctly

### Performance
- [ ] Response times are reasonable
- [ ] Token usage is tracked accurately
- [ ] Cost projections are realistic
- [ ] Memory usage is acceptable

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Smoke tests complete successfully
- [ ] No regression in existing models

## 🚨 Common Issues

### Authentication Errors

```
Error: Invalid API key for your_provider
```

**Solution**: Verify API key in environment variables and test manually:

```bash
curl -H "Authorization: Bearer $YOUR_PROVIDER_API_KEY" \
     https://api.yourprovider.com/v1/models
```

### Model Not Found

```
Error: Model 'your-new-model' not found
```

**Solutions**:
1. Check `api_name` in configuration matches provider's model name
2. Verify model access permissions
3. Confirm model is generally available (not private beta)

### Unexpected Costs

```
Warning: Model usage 300% above estimate
```

**Investigation**:
1. Check token counting accuracy with provider's tokenizer
2. Verify cost-per-token configuration
3. Review prompt length and response size
4. Compare with provider's billing dashboard

### Selection Logic Not Working

```
Expected 'your-new-model', got 'sonnet-4'
```

**Debug Steps**:
1. Add logging to selection conditions
2. Verify context contains expected fields
3. Check condition priority order
4. Test with `force_model` metadata

## 📊 Performance Benchmarking

Run comprehensive evaluation to establish baselines:

```bash
# Run all evaluation suites with your model
AMP_MODEL=your-new-model ./scripts/run_full_evaluation.sh

# Compare results with existing models
python scripts/compare_models.py --baseline sonnet-4 --new your-new-model

# Generate performance report
python scripts/model_performance_report.py --model your-new-model
```

**Expected Outputs:**
- Accuracy comparison across task types
- Token efficiency analysis
- Cost-per-task breakdown
- Response time benchmarks

## 🎯 Best Practices

### Model Naming
- Use descriptive, versioned names: `gpt-5-turbo-2024`
- Avoid abbreviations that could be confusing
- Include provider prefix for clarity: `anthropic-claude-3-opus`

### Cost Management
- Start with conservative estimates
- Monitor actual usage vs. projections
- Implement budget alerts for new models
- Document cost justification

### Selection Criteria
- Make conditions specific and testable
- Avoid overlap with existing model conditions
- Consider both performance and cost factors
- Document decision logic clearly

### Error Handling
- Implement graceful fallbacks to existing models
- Log failures for debugging
- Respect rate limits with exponential backoff
- Handle partial responses appropriately

## 🚀 Going Live

### Pre-Production
1. **Staging Tests**: Run full evaluation suite in staging
2. **Cost Validation**: Confirm actual costs match projections
3. **Performance Review**: Compare against existing models
4. **Team Approval**: Get sign-off from engineering lead

### Production Rollout
1. **Gradual Introduction**: Start with 5% of evaluations
2. **Monitor Closely**: Watch dashboards for anomalies
3. **Collect Feedback**: Gather team input on performance
4. **Scale Up**: Increase usage based on results

### Post-Launch
1. **Update Documentation**: Reflect any lessons learned
2. **Monitor Long-term**: Track monthly cost and performance trends
3. **Optimize**: Tune selection conditions based on real usage
4. **Share Results**: Present findings to broader team

---

**Success Criteria**: New model integrates smoothly, provides value for specific use cases, and stays within budget projections.
