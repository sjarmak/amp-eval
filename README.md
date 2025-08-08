# Amp Model Evaluation Suite

Production-grade evaluation platform that benchmarks conversational AI models (Sonnet-4, GPT-5, o3) on coding tasks including tool calling, bug fixing, and complex reasoning. Features structured data capture from Amp debug logs for comprehensive analysis.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Requirements

- Python 3.11+
- Docker (optional)

## Quick Start

### DevContainer (Recommended)
```bash
git clone https://github.com/sjarmak/amp-eval.git
cd amp-eval
code .
# Click "Reopen in Container" when prompted
```

### Local Development
```bash
git clone https://github.com/sjarmak/amp-eval.git
cd amp-eval
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### Docker
```bash
docker build -t amp-eval .
docker run -p 8501:8501 --env-file .env amp-eval
```

### Smoke Test
```bash
make test-smoke

# Expected output:
# ✅ Tool calling test passed  
# ✅ Model selection working
# ✅ Cost tracking active
```

## Running Evaluations

### Basic Usage
```bash
# Tool calling accuracy test
python -m src.amp_eval.cli suite evals/tool_calling_micro.yaml

# Bug fixing capability test
python -m src.amp_eval.cli suite evals/single_file_fix.yaml

# Complex reasoning test (requires oracle trigger)
python -m src.amp_eval.cli suite evals/oracle_knowledge.yaml
```

### Model Selection
```bash
# Force specific model
AMP_MODEL=gpt-5 python -m src.amp_eval.cli suite evals/tool_calling_micro.yaml

# Use oracle for complex reasoning (add "consult the oracle:" to prompts)
AMP_MODEL=o3 python -m src.amp_eval.cli suite evals/oracle_knowledge.yaml
```

## Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

Visit http://localhost:8501 to view results and metrics.

## Configuration

### Environment Variables
```bash
cp .env.example .env
# Edit .env with your settings
```

### Model Selection Rules
Edit `config/agent_settings.yaml`:

```yaml
models:
  sonnet-4:
    upgrade_conditions:
      diff_lines: 20
      touched_files: 2
  
oracle:
  trigger_phrase: "consult the oracle:"
```

## Evaluation Suites

| Suite | Purpose | Tests | Pass Threshold |
|-------|---------|-------|----------------|
| tool_calling_micro | Function calling accuracy | 10 | 70% |
| single_file_fix | Bug fixing capability | 5 | 70% |
| oracle_knowledge | Complex reasoning | 3 | 75% |

## Evaluation Architecture

### Structured Data Capture

The suite captures comprehensive execution data from Amp debug logs:

- **Tool Calls**: Exact tool names, arguments, and execution IDs
- **Token Usage**: Input/output tokens for accurate cost tracking  
- **Performance Metrics**: Inference duration, tokens/second, latency
- **Model Routing**: Automatic model selection based on complexity

### Log-Based Analysis

```json
{
  "tool_calls": [{"name": "glob", "arguments": {"filePattern": "*.py"}}],
  "token_usage": {"input_tokens": 7, "output_tokens": 260},
  "model_performance": {"inferenceDuration": "4.88s", "tokensPerSecond": 53.3},
  "model": "sonnet-4",
  "success": true
}
```

### Fallback System

- **Primary**: Parse structured JSON from Amp debug logs
- **Fallback**: Pattern matching on tool output for robustness
- **Hybrid**: Combine log data with pattern-matched tool names

## Extending

### Adding Models
See [docs/MODEL_ADDITION.md](docs/MODEL_ADDITION.md)

### Creating Evaluations
1. Create YAML file in `evals/`
2. Add test repos in `tasks/repos/`
3. Define grading criteria
4. Register with `amp_runner.py`

### Custom Graders
```python
from amp_eval.grading import BaseGrader

class CustomGrader(BaseGrader):
    def grade(self, response, expected):
        # Custom grading logic
        return score
```

## Architecture

```
amp-eval/
├── config/                 # Configuration files
├── adapters/              # OpenAI-Evals integration  
├── evals/                 # Evaluation definitions
├── tasks/repos/           # Test repositories
├── dashboard/             # Streamlit dashboard
└── scripts/               # Analysis and utilities
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for changes
4. Run `make lint test`
5. Submit pull request

## Troubleshooting

### Common Issues

**"No module named 'amp_runner'"**
- Run from `amp-eval/` directory
- Check `adapters/amp_runner.py` exists

**"Oracle not triggered"**
- Use exact phrase: `"consult the oracle:"`
- Check `AMP_MODEL` environment variable

**"Tests failing immediately"**
- Verify test repos in `tasks/repos/` have correct structure
- Check Python path includes repo directories

## License

MIT License - see [LICENSE](LICENSE) file for details.
