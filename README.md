# 🚀 Amp Model-Efficacy Evaluation Suite

> Production-grade AI model evaluation platform for continuous monitoring, cost optimization, and data-driven model selection.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎯 Purpose

Benchmark and continuously monitor AI models (**Sonnet-4**, **GPT-5**, **o3**) across:
- **Tool-calling accuracy** - Function calling and parameter extraction
- **Code-fix success** - Bug resolution and refactoring capabilities  
- **Knowledge-retrieval** - Complex reasoning and domain expertise
- **Cost efficiency** - Token usage and budget optimization

## ⚡ Quick Start

```bash
# 1. Clone and open in VS Code
git clone https://github.com/your-org/amp-eval.git
cd amp-eval
code .

# 2. Open in DevContainer (when prompted)
# 3. Configure API keys
cp .env.example .env
# Edit .env with your OpenAI/Anthropic keys

# 4. Run smoke test
make test-smoke

# 5. Start dashboard
streamlit run dashboard/app.py
```

🎉 Visit http://localhost:8501 to see your evaluation dashboard!

**Need more help?** → [Quick Start Guide](docs/QUICK_START.md)

## 🛠️ Core Features

### 📊 Real-Time Dashboard
- Live performance metrics and cost tracking
- Interactive charts and trend analysis  
- Automated alerts for regressions and budget overruns
- Team performance analytics

### 🧠 Intelligent Model Selection
- **Oracle trigger**: Automatically use o3 for complex reasoning
- **Cost optimization**: Smart model selection based on task complexity
- **Custom rules**: Define upgrade conditions per use case
- **Override support**: Manual model selection when needed

### 💰 Cost Management
- **Budget tracking**: Monthly limits with proactive alerts
- **Token efficiency**: Optimize prompts and reduce waste
- **Cost projections**: Predict monthly spend based on usage
- **ROI analysis**: Track performance improvements vs cost

### 🔧 Evaluation Suites

| Suite | Purpose | Tests | Target Accuracy |
|-------|---------|-------|-----------------|
| **tool_calling_micro** | Function calling precision | 10 | >85% |
| **single_file_fix** | Bug fixing capability | 5 | >80% |
| **oracle_knowledge** | Complex reasoning | 3 | >75% |

## 📈 Performance Targets

| Model | Tool Calling | Bug Fixing | Oracle Knowledge | Monthly Cost |
|-------|-------------|------------|------------------|--------------|
| **Sonnet-4** | ≥70% | ≥65% | N/A | <$200 |
| **GPT-5** | ≥85% | ≥80% | N/A | <$400 |
| **o3** | ≥90% | ≥85% | ≥75% | <$800 |

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Evaluation    │    │  Model Selection│    │    Dashboard    │
│     Engine      │────│     Engine      │────│   (Streamlit)   │
│ (OpenAI-Evals)  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ├───────────────────────┼───────────────────────┤
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cost Tracker │    │   Result Store  │    │ Slack/GitHub    │
│                 │    │   (SQLite)      │    │  Integration    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Installation Options

### Option 1: DevContainer (Recommended)
```bash
# Open in VS Code, click "Reopen in Container"
code .
```

### Option 2: Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

### Option 3: Docker
```bash
# Build and run
docker build -t amp-eval .
docker run -p 8501:8501 --env-file .env amp-eval
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [Quick Start](docs/QUICK_START.md) | Get running in 5 minutes |
| [Contributing](docs/CONTRIBUTING.md) | Contribution guidelines with cost assessment |
| [Dashboard Guide](docs/DASHBOARD_GUIDE.md) | Interpret metrics and alerts |
| [Model Addition](docs/MODEL_ADDITION.md) | Add new AI models |
| [Launch Plan](docs/LAUNCH_PLAN.md) | Production deployment strategy |

## 🎯 Usage Examples

### Run Evaluations
```bash
# Basic evaluation with default model selection
openai tools evaluate evals/tool_calling_micro.yaml --registry adapters/

# Force specific model
AMP_MODEL=gpt-5 openai tools evaluate evals/single_file_fix.yaml --registry adapters/

# Oracle-only evaluation  
AMP_MODEL=o3 openai tools evaluate evals/oracle_knowledge.yaml --registry adapters/
```

### Dashboard & Monitoring
```bash
# Start dashboard
streamlit run dashboard/app.py

# View cost summary
python -m amp_eval.monitoring.cost_tracker --summary

# Generate weekly report
python scripts/weekly_report.py
```

### Slack Integration
```bash
# In Slack
/amp-eval status          # System status
/amp-eval run tool_calling # Run evaluation
/amp-eval cost            # Cost summary
```

## 🔧 Configuration

### Model Selection Rules
```yaml
# config/agent_settings.yaml
models:
  sonnet-4:
    cost_per_token: 0.00003
    upgrade_conditions:
      diff_lines: 20
      touched_files: 2

  gpt-5:
    cost_per_token: 0.00015
    upgrade_conditions:
      diff_lines: 50
      touched_files: 4

oracle:
  trigger_phrase: "consult the oracle:"
  max_usage_percent: 10
```

### Budget Controls
```yaml
# Monthly budget enforcement
budget:
  monthly_limit: 500.00
  alert_thresholds:
    - 50  # $50 spent
    - 80  # 80% of budget
    - 95  # 95% of budget
  circuit_breaker: 110  # Stop at 110%
```

## 📊 Results & Analytics

### Viewing Results
```bash
# Latest results summary
python scripts/results_summary.py

# Historical analysis
jupyter notebook scripts/analysis.ipynb

# Export to CSV
python scripts/export_results.py --format csv --days 30
```

### Custom Metrics
```python
from amp_eval.analytics import MetricsCalculator

calc = MetricsCalculator()
accuracy = calc.model_accuracy("gpt-5", days=7)
cost_efficiency = calc.cost_per_success("sonnet-4")
```

## 🛡️ Security & Compliance

- **API Key Management**: Environment variables only, 90-day rotation
- **Audit Logging**: All evaluations logged with user attribution
- **Cost Controls**: Circuit breakers prevent runaway spending
- **Data Privacy**: No PII in evaluation prompts or logs

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for:
- Code standards and pre-commit hooks
- Cost impact assessment requirements  
- Testing and documentation standards
- Review process and approval thresholds

### Development Workflow
```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Make changes with tests
# 3. Run quality checks
make lint test

# 4. Submit PR with cost impact assessment
```

## 📞 Support

- **Documentation**: Check [docs/](docs/) first
- **Issues**: Create GitHub issue with reproduction steps
- **Slack**: Join `#amp-eval` for questions and discussions
- **Security**: Email security@yourcompany.com for vulnerabilities

## 📈 Roadmap

### Phase 1: Foundation ✅
- [x] Core evaluation framework
- [x] Model selection engine
- [x] Basic dashboard
- [x] Cost tracking

### Phase 2: Production Features 🚧
- [ ] Advanced analytics and reporting
- [ ] Multi-language evaluation support
- [ ] Enterprise security features
- [ ] Performance optimization

### Phase 3: Scale & Intelligence 📋
- [ ] Auto-tuning model selection
- [ ] Custom evaluation frameworks
- [ ] Multi-organization support
- [ ] Advanced cost optimization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI Evals framework for evaluation infrastructure
- Anthropic Claude for model comparison capabilities
- Streamlit for dashboard development
- The engineering team for feedback and testing

---

**Ready to start?** → [Quick Start Guide](docs/QUICK_START.md) | **Questions?** → [Open an Issue](https://github.com/your-org/amp-eval/issues)
