.PHONY: help install dev-install clean test lint format type-check pre-commit build publish

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package
	pip install -e .

dev-install: ## Install package with development dependencies
	pip install -e ".[dev,viz]"
	pre-commit install

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test: ## Run tests
	pytest -v --cov=amp_eval --cov-report=term-missing

test-fast: ## Run tests without coverage
	pytest -v --no-cov

lint: ## Run linting
	ruff check src/ tests/
	black --check src/ tests/

format: ## Format code
	black src/ tests/
	ruff check src/ tests/ --fix

type-check: ## Run type checking
	mypy src/amp_eval/

pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

build: ## Build package
	python -m build

publish-test: ## Publish to TestPyPI
	python -m twine upload --repository testpypi dist/*

publish: ## Publish to PyPI
	python -m twine upload dist/*

setup-dev: ## Set up development environment
	python setup_dev.py

validate: ## Validate configuration
	amp-eval validate-config

cli-help: ## Show CLI help
	amp-eval --help

# CI/CD targets
ci-test: ## Run CI tests
	pytest -v --cov=amp_eval --cov-report=xml --cov-fail-under=90

ci-lint: ## Run CI linting
	black --check src/ tests/
	ruff check src/ tests/
	mypy src/amp_eval/

test-smoke: ## Run smoke test on minimal evaluation
	@if [ -f venv/bin/activate ]; then \
		. venv/bin/activate && python scripts/smoke_test.py; \
	else \
		python3 scripts/smoke_test.py; \
	fi

# Development workflow
dev: dev-install format lint type-check test ## Full development setup and validation
