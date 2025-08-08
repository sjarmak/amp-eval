# Quick Start Guide - Amp Evaluation Suite

Get running evaluations in 5 minutes with structured data capture from Amp debug logs.

## Prerequisites
- Python 3.11+
- VS Code with Docker extension (for DevContainer)
- Amp API key from [ampcode.com](https://ampcode.com/settings/api-keys)

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

### Step 3: Set Your Amp API Key

**Important**: You need to configure your Amp API key inside the container to run evaluations.

```bash
# Inside the devcontainer terminal:
export AMP_API_KEY="your-key-from-ampcode.com-settings"

# Verify authentication works
python check_amp_auth.py
```

> 💡 **Get your API key**: Visit [ampcode.com](https://ampcode.com) → Settings → API Keys

### Step 4: Configure Model Selection

```bash
# Copy environment template (optional)
cp .env.example .env

# Optionally set model via environment
# AMP_MODEL=gpt-5  # For GPT-5 instead of default Sonnet-4
# Use 'consult the oracle:' in prompts for o3 access
```

### Step 5: Test Installation

```bash
# Run smoke test (via Amp CLI)
make test-smoke

# Expected output:
# ✅ Tool calling test passed
# ✅ Model selection working
# ✅ Cost tracking active
```

### Step 6: Run Your First Evaluation

```bash
# Run basic tool calling evaluation (Sonnet-4 default)
python -m src.amp_eval.cli suite evals/tool_calling_micro.yaml

# Or with GPT-5
AMP_MODEL=gpt-5 python -m src.amp_eval.cli suite evals/tool_calling_micro.yaml

# View results in dashboard
streamlit run dashboard/streamlit_app.py
```

Visit http://localhost:8501 to see your results!

## Next Steps

- Try different evaluation suites in `evals/`
- Explore dashboard features at http://localhost:8501
- See [Agent Reference](AGENT_REFERENCE.md) for technical details
- Check [contributing guidelines](CONTRIBUTING.md) to add evaluations

## Need Help?

- Check documentation in `docs/` directory
- Create GitHub issue with reproduction steps
- Review troubleshooting in [Agent Reference](AGENT_REFERENCE.md)
