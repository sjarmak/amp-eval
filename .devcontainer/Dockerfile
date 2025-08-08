FROM mcr.microsoft.com/devcontainers/python:3.11

# Install additional system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for development
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Install OpenAI Evals (if not in requirements)
RUN pip install openai-evals

# Set up development environment
WORKDIR /workspaces/amp-eval
ENV PYTHONPATH="/workspaces/amp-eval/src:${PYTHONPATH}"

# Create directories for evaluation artifacts
RUN mkdir -p /workspaces/amp-eval/results /workspaces/amp-eval/logs

# Set up git configuration placeholders
RUN git config --global user.name "Dev Container User" && \
    git config --global user.email "dev@ampcode.com"
