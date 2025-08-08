# Contributing to Amp Evaluation Suite

## 🎯 Overview

Thank you for contributing to the Amp Model-Efficacy Evaluation Suite! This guide helps you understand our contribution process, cost considerations, and quality standards.

## 💰 Cost Impact Assessment

### Before Contributing

**Every evaluation costs money.** Before adding new evaluations or modifying existing ones:

1. **Estimate Token Usage**: New evaluations consume API tokens across multiple models
2. **Calculate Monthly Impact**: A single new evaluation can cost $50-200/month in API fees
3. **Justify Value**: Ensure the evaluation provides actionable insights for model selection

### Cost Categories

| Change Type | Estimated Monthly Cost | Approval Required |
|-------------|----------------------|-------------------|
| New micro-evaluation (1-5 prompts) | $10-50 | Team Lead |
| New suite (5-15 tasks) | $50-200 | Engineering Manager |
| Multi-file refactoring suite | $200-500 | Director Approval |
| Custom model integration | $500+ | Budget Committee |

## 🔧 Development Setup

### Quick Start with DevContainer

1. Open repository in VS Code
2. Click "Reopen in Container" when prompted
3. Wait for automatic dependency installation
4. Run smoke test: `make test-smoke`

### Manual Setup

```bash
# Clone and enter directory
git clone <repo-url>
cd amp-eval

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Configure environment
cp .env.example .env
# Add your OpenAI/Anthropic API keys
```

## 📝 Contribution Types

### 1. Adding New Evaluations

**Cost Impact: HIGH** - Requires approval and cost justification

```yaml
# Template: evals/your_evaluation.yaml
name: your_evaluation
description: "Brief description of what this tests"
tasks:
  - prompt: "Your test prompt here"
    expected_tool: "tool_name"
    expected_args: {"arg": "value"}
    grading_criteria:
      tool_correct: 40
      args_present: 30
      args_correct: 30
```

**Requirements:**
- [ ] Cost justification in PR description
- [ ] Baseline results across all models
- [ ] Documentation for interpreting results
- [ ] Test coverage for grading logic

### 2. Improving Existing Evaluations

**Cost Impact: MEDIUM** - Test changes thoroughly

- Modify grading criteria carefully
- Document expected result changes
- Run regression tests before/after

### 3. Infrastructure & Tooling

**Cost Impact: LOW** - Generally safe to iterate

- Bug fixes in amp_runner.py
- Dashboard improvements
- Documentation updates
- CI/CD enhancements

## 🧪 Testing Requirements

### Pre-Submission Checklist

```bash
# Code quality
make lint
make type-check
make test

# Cost validation
make test-smoke  # Quick validation (<$1 in API costs)
make estimate-cost  # Calculate monthly impact

# Integration testing
make test-integration  # Runs 3 smallest evaluations
```

### Test Coverage Standards

- **Unit tests**: 90%+ coverage for core logic
- **Integration tests**: Each evaluation YAML must have smoke test
- **Regression tests**: Golden file comparisons for grading consistency

## 📊 Quality Gates

### Automated Checks (GitHub Actions)

- [x] **Linting**: black, ruff, mypy pass
- [x] **Security**: No hardcoded secrets or API keys
- [x] **Tests**: All unit/integration tests pass
- [x] **Cost**: Estimated monthly impact < threshold

### Manual Review Requirements

| Change Type | Required Reviewers | Cost Threshold |
|-------------|-------------------|----------------|
| Documentation | 1 team member | N/A |
| Bug fixes | 1 team member | < $10/month |
| New evaluations | 2 team members + lead | > $50/month |
| Model integration | Engineering manager | > $100/month |

## 🚀 Submission Process

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Implement Changes

- Follow existing code patterns
- Add comprehensive tests
- Update documentation
- Run cost estimation

### 3. Submit Pull Request

**PR Template Requirements:**

```markdown
## Cost Impact Assessment
- **Estimated monthly cost**: $X
- **Token usage per run**: X tokens
- **Frequency**: X runs/day
- **Justification**: Why this evaluation is needed

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Smoke test runs successfully
- [ ] Cost estimation completed

## Documentation
- [ ] Code comments added where needed
- [ ] README updated if relevant
- [ ] Dashboard interpretation guide updated
```

### 4. Address Review Feedback

- Respond to all review comments
- Update cost estimates if scope changes
- Re-run tests after modifications

## 📈 Performance Standards

### Response Time

- **Evaluations**: Complete within 5 minutes per suite
- **Dashboard**: Load within 3 seconds
- **API calls**: Honor rate limits with exponential backoff

### Resource Usage

- **Memory**: < 1GB per evaluation process
- **CPU**: Efficient enough for CI/CD integration
- **Storage**: Results compressed and archived

## 🔒 Security Guidelines

### API Key Management

- **Never commit keys**: Use environment variables only
- **Rotate regularly**: Keys expire every 90 days
- **Scope minimally**: Use read-only keys where possible
- **Audit access**: Log all API usage with eval_id tracking

### Data Handling

- **No PII**: Evaluation prompts must not contain personal data
- **Audit logs**: Retain for 90 days, then auto-delete
- **Cost caps**: Circuit breakers prevent runaway costs

## 🎓 Learning Resources

### Model Integration Guide

- See [docs/MODEL_ADDITION.md](./MODEL_ADDITION.md)
- Study existing adapter patterns in `adapters/`
- Test with smallest evaluation first

### Dashboard Interpretation

- See [docs/DASHBOARD_GUIDE.md](./DASHBOARD_GUIDE.md)
- Understand metric definitions and thresholds
- Know when to escalate performance regressions

### Evaluation Design

- Study existing YAML files in `evals/`
- Understand grading criteria trade-offs
- Balance specificity vs. generalizability

## 🆘 Getting Help

### Common Issues

**"Evaluation taking too long"**
- Check token limits in config
- Verify model selection logic
- Consider prompt complexity

**"Unexpected cost spike"**
- Review recent evaluation additions
- Check if oracle (o3) trigger is working correctly
- Audit model upgrade conditions

**"Results inconsistent"**
- Ensure deterministic prompts
- Check for race conditions in parallel runs
- Verify grading criteria implementation

### Support Channels

1. **Documentation**: Check existing guides first
2. **Issues**: Create GitHub issue with reproduction steps
3. **Slack**: #amp-eval channel for quick questions
4. **On-call**: Critical cost/security issues only

## 🏆 Recognition

### Contributor Levels

**Bronze**: Documentation, bug fixes, minor improvements
**Silver**: New evaluation suites, infrastructure enhancements  
**Gold**: Model integrations, major feature additions
**Platinum**: Architecture improvements, cost optimizations

### Acknowledgments

- Contributors listed in README
- Monthly shout-outs in engineering all-hands
- Conference speaking opportunities for major contributions

---

**Remember**: Every line of code and every evaluation impacts our monthly AI budget. Contribute thoughtfully, test thoroughly, and optimize relentlessly.
