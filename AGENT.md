# Agent Implementation Guide

This file documents the implementation details of the Amp Evaluation Suite for future development and maintenance.

## Commands Reference

### Development Commands
```bash
# Typecheck, lint, build
make lint          # Run linting with ruff and black
make type-check    # Run mypy type checking
make format        # Auto-format code with black and ruff

# Testing
make test          # Run full test suite with coverage
make test-fast     # Run tests without coverage
make test-smoke    # Quick smoke test validation

# Environment setup
make dev-install   # Install with dev dependencies
make setup-dev     # Run development environment setup
```

### Evaluation Commands
```bash
# Run evaluation suites
python -m src.amp_eval.cli suite evals/tool_calling_micro.yaml
python -m src.amp_eval.cli suite evals/single_file_fix.yaml

# Force specific models
AMP_MODEL=gpt-5 python -m src.amp_eval.cli suite [eval-file]
AMP_MODEL=o3 python -m src.amp_eval.cli suite [eval-file]

# Debug mode with verbose logging
AMP_LOG_LEVEL=debug python -m src.amp_eval.cli suite [eval-file]
```

## Architecture Overview

### Core Components

1. **AmpRunner** (`src/amp_eval/amp_runner.py`)
   - Executes Amp CLI with debug logging
   - Parses structured JSON logs for tool calls, tokens, performance
   - Handles model selection logic and configuration

2. **Evaluation Engine** (`src/amp_eval/cli.py`)
   - Loads evaluation suites from YAML
   - Orchestrates test execution and grading
   - Saves structured results to JSON

3. **Graders** (`src/amp_eval/graders/`)
   - `tool_call_accuracy.py` - Scores tool calling correctness
   - Weighted scoring: tool name (40%), args present (30%), args correct (30%)

4. **Configuration** (`config/agent_settings.yaml`)
   - Model selection rules and triggers
   - Oracle and GPT-5 activation logic

### Log-Based Evaluation Implementation

#### Debug Log Parsing
```python
def _parse_amp_debug_logs(self, log_path: str) -> ParsedLogs:
    """Extract structured data from Amp debug JSON logs."""
    # Parse for:
    # - invokeTool messages with tool IDs  
    # - token_usage entries (input_tokens, output_tokens)
    # - performance metrics (inferenceDuration, tokensPerSecond)
```

#### Pattern Matching Fallback
```python
def _extract_tool_calls(self, stream: str) -> List[Dict[str, Any]]:
    """Regex patterns to identify tools from natural language output."""
    # Patterns for: glob, Grep, Read, create_file, edit_file, etc.
```

#### Hybrid Enhancement
- **Primary**: Structured data from debug logs (tool_id, tokens, performance)
- **Enrichment**: Pattern matching adds tool names and arguments when missing
- **Robustness**: Falls back to pure pattern matching if log parsing fails

## Model Selection Logic

### Precedence Order
1. **Oracle trigger**: "consult the oracle:" → o3
2. **CLI flag**: `--try-gpt5` → gpt-5  
3. **Environment**: `AMP_MODEL=gpt-5` → gpt-5
4. **Rules**: Based on diff_lines, touched_files → configured model
5. **Default**: sonnet-4

### Configuration Example
```yaml
default_model: 'sonnet-4'
oracle_trigger: 
  phrase: 'consult the oracle:'
  model: 'o3'
cli_flag_gpt5:
  flag: '--try-gpt5'
  model: 'gpt-5'
rules:
  - condition: 'diff_lines > 40 AND touched_files > 2'
    target_model: 'gpt-5'
```

## Data Structures

### ParsedLogs TypedDict
```python
class ParsedLogs(TypedDict):
    tool_calls: List[Dict[str, Any]]    # Tool execution data
    token_usage: Dict[str, int]         # Input/output token counts  
    perf: Dict[str, Any]                # Performance metrics
```

### Evaluation Result Structure
```json
{
  "model": "sonnet-4",
  "latency_s": 4.88,
  "tokens": 267,
  "token_usage": {"input_tokens": 7, "output_tokens": 260},
  "model_performance": {
    "inferenceDuration": "4.88s", 
    "tokensPerSecond": 53.3,
    "outputTokens": 260
  },
  "tool_calls": [{
    "tool_id": "toolu_vrtx_01ABC...",
    "name": "glob", 
    "arguments": {"filePattern": "*.py"}
  }],
  "success": true,
  "stdout": "Found 6 Python files...",
  "stderr": "",
  "returncode": 0
}
```

## Testing Strategy

### Smoke Test Validation
```bash
make test-smoke
# Validates:
# - Tool calling detection works
# - Model selection routing functions  
# - Token usage capture active
```

### Unit Testing Approach
- Mock Amp CLI execution for consistent testing
- Test log parsing with sample debug JSON fixtures
- Validate grader scoring with known tool calls
- Test pattern matching fallback scenarios

## Common Debugging

### Log Analysis
```bash
# Check debug logs
tail -f ~/.cache/amp/logs/cli.log | jq .

# Look for specific log entries
grep "invokeTool\|token_usage" ~/.cache/amp/logs/cli.log
```

### Evaluation Debugging
```bash
# Run single evaluation with debug output
AMP_LOG_LEVEL=debug python -c "
from src.amp_eval.amp_runner import AmpRunner
runner = AmpRunner()
result = runner.run_amp('List Python files', 'sonnet-4')
print(result)
"
```

### Performance Monitoring
```bash
# Check evaluation timing and token usage
cat results/results_*.json | jq '.[] | {latency: .latency_s, tokens: .tokens, model: .model}'
```

## Future Enhancements

### Planned Improvements
- [ ] Real-time evaluation dashboard updates
- [ ] Cost budget alerts and controls  
- [ ] Advanced grading with LLM judges
- [ ] Multi-turn conversation evaluations
- [ ] Repository-level code change evaluations

### Architecture Extensions
- [ ] Plugin system for custom graders
- [ ] Distributed evaluation across multiple Amp instances
- [ ] Integration with CI/CD pipelines
- [ ] Evaluation result comparison and regression detection

## Dependencies

### Core Libraries
- `pydantic` - Configuration validation
- `yaml` - Evaluation suite definitions  
- `loguru` - Structured logging
- `streamlit` - Dashboard interface

### Development Tools
- `pytest` - Testing framework
- `mypy` - Type checking
- `ruff` + `black` - Code linting and formatting
- `pre-commit` - Git hooks for quality

This implementation provides a robust foundation for evaluating AI coding assistants with detailed metrics and structured data capture.
