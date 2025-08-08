#!/bin/bash
set -e

echo "=== Dev Container Setup ==="

# Update pip first
echo "1. Updating pip..."
pip install --upgrade pip

# Install Node.js packages
echo "2. Installing Amp CLI..."
npm install -g @sourcegraph/amp

# Install Python packages with retries and longer timeouts
echo "3. Installing Python requirements..."
pip install --timeout 180 --retries 5 -r requirements.txt || {
    echo "First attempt failed, trying with --no-cache-dir..."
    pip install --no-cache-dir --timeout 180 --retries 5 -r requirements.txt
}

echo "4. Installing development requirements..."
pip install --timeout 180 --retries 5 -r requirements-dev.txt || {
    echo "First attempt failed, trying with --no-cache-dir..."
    pip install --no-cache-dir --timeout 180 --retries 5 -r requirements-dev.txt
}

echo "5. Installing package in editable mode..."
pip install --timeout 180 --retries 5 -e . || {
    echo "First attempt failed, trying with --no-cache-dir..."
    pip install --no-cache-dir --timeout 180 --retries 5 -e .
}

echo "6. Installing pre-commit hooks..."
pre-commit install || echo "Pre-commit install failed, but continuing..."

echo "7. Verifying installations..."
python --version
node --version
amp --version || echo "Amp CLI not available (might need authentication)"

echo "=== Setup Complete ==="
