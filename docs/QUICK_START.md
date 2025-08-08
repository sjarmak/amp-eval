# Quick Start Guide - Amp Evaluation Suite

## 🚀 Get Running in 5 Minutes

This guide gets you from zero to running evaluations quickly.

### Prerequisites
- VS Code with Docker extension
- Git access to the repository
- Amp CLI access (no external API keys needed)

### Step 1: Clone and Open

```bash
git clone <repo-url>
cd amp-eval
code .
```

### Step 2: Open in DevContainer

1. VS Code will prompt: "Reopen in Container" - click **Reopen in Container**
2. Wait for container build (2-3 minutes first time)
3. Dependencies install automatically

### Step 3: Configure Model Selection

```bash
# Copy environment template (optional)
cp .env.example .env

# Optionally set model via environment
# AMP_MODEL=gpt-5  # For GPT-5 instead of default Sonnet-4
# Use 'consult the oracle:' in prompts for o3 access
```

### Step 4: Test Installation

```bash
# Run smoke test (via Amp CLI)
make test-smoke

# Expected output:
# ✅ Tool calling test passed
# ✅ Model selection working
# ✅ Cost tracking active
```

### Step 5: Run Your First Evaluation

```bash
# Run basic tool calling evaluation (Sonnet-4 default)
amp-eval evaluate evals/tool_calling_micro.yaml

# Or with GPT-5
AMP_MODEL=gpt-5 amp-eval evaluate evals/tool_calling_micro.yaml

# View results in dashboard
streamlit run dashboard/streamlit_app.py
```

Visit http://localhost:8501 to see your results!

## 🎯 What's Next?

**For Individual Contributors:**
- Explore [dashboard features](DASHBOARD_GUIDE.md)
- Try different evaluation suites
- Learn about [contributing](CONTRIBUTING.md)

**For Team Leads:**
- Review [launch planning](LAUNCH_PLAN.md) 
- Set up [cost monitoring](DASHBOARD_GUIDE.md#cost-analysis-panel)
- Plan team adoption strategy

**For Platform Teams:**
- Study [model integration](MODEL_ADDITION.md)
- Set up [Slack notifications](../src/amp_eval/integrations/slack.py)
- Configure CI/CD integration

## 🆘 Need Help?

- **Documentation**: Check the [docs/](.) directory
- **Issues**: Create GitHub issue with reproduction steps
- **Questions**: Ask in #amp-eval Slack channel

Happy evaluating! 🎉
