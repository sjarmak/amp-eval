# Quick Start Guide - Amp Evaluation Suite

## 🚀 Get Running in 5 Minutes

This guide gets you from zero to running evaluations quickly.

### Prerequisites
- VS Code with Docker extension
- Git access to the repository
- OpenAI or Anthropic API key

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

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
code .env
```

Add your keys:
```bash
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 4: Test Installation

```bash
# Run smoke test (uses ~$1 in API calls)
make test-smoke

# Expected output:
# ✅ Tool calling test passed
# ✅ Model selection working
# ✅ Cost tracking active
```

### Step 5: Run Your First Evaluation

```bash
# Run basic tool calling evaluation
openai tools evaluate evals/tool_calling_micro.yaml --registry adapters/

# View results in dashboard
streamlit run dashboard/app.py
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
