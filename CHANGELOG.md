# Changelog

All notable changes to the Amp Evaluation Suite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Amp Model-Efficacy Evaluation Suite
- Support for Sonnet-4, GPT-5, and o3 models
- Intelligent model selection with upgrade rules
- Real-time dashboard with Streamlit
- Cost tracking and budget management
- Slack integration for notifications and commands
- Feedback collection system
- DevContainer development environment
- Comprehensive documentation and guides

### Core Features
- **Evaluation Suites**: tool_calling_micro, single_file_fix, oracle_knowledge
- **Model Selection**: Rule-based automatic model selection and manual overrides
- **Cost Management**: Budget tracking, alerts, and projections
- **Dashboard**: Real-time metrics, charts, and performance monitoring
- **Integrations**: Slack notifications, GitHub issue creation
- **Security**: API key management, audit logging, circuit breakers

### Documentation
- Quick Start Guide for 5-minute setup
- Contribution guidelines with cost impact assessment
- Dashboard interpretation guide
- Model addition tutorial
- Launch planning and rollout strategy

### Infrastructure
- Docker and DevContainer support
- Pre-commit hooks and code quality tools
- CI/CD pipeline foundations
- Testing framework and coverage

## [1.0.0] - Initial Release

### Added
- Complete evaluation framework implementation
- Production-ready documentation
- Launch strategy and rollout plan
- All Phase 9 and Phase 10 deliverables

---

## Release Notes

### v1.0.0 - Production Launch

This initial release provides a complete, production-ready AI model evaluation platform designed for continuous monitoring and cost optimization.

**Key Capabilities:**
- Evaluate AI models on tool-calling, bug-fixing, and reasoning tasks
- Automatic model selection based on task complexity and cost
- Real-time dashboard with performance metrics and cost tracking
- Slack integration for team notifications and commands
- Comprehensive feedback collection and GitHub integration

**Getting Started:**
1. Clone the repository
2. Open in VS Code DevContainer
3. Configure API keys in `.env`
4. Run `make test-smoke` to validate setup
5. Launch dashboard with `streamlit run dashboard/app.py`

**Documentation:**
- [Quick Start Guide](docs/QUICK_START.md) - Get running in 5 minutes
- [Dashboard Guide](docs/DASHBOARD_GUIDE.md) - Interpret metrics and alerts
- [Contributing Guide](docs/CONTRIBUTING.md) - Code standards and cost assessment

**Support:**
- GitHub Issues for bug reports and feature requests
- #amp-eval Slack channel for questions and discussions
- Comprehensive documentation in the `docs/` directory

Ready to optimize your AI model selection? Get started with the [Quick Start Guide](docs/QUICK_START.md)!
