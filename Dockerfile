# Multi-stage Alpine Python build for amp-eval
FROM python:3.11-alpine AS base

# Install system dependencies needed for Python packages
RUN apk add --no-cache \
    git \
    build-base \
    libffi-dev \
    openssl-dev \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S ampeval && \
    adduser -u 1001 -S ampeval -G ampeval

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt requirements-dev.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY --chown=ampeval:ampeval . .

# Install package in development mode
RUN pip install -e .

# Switch to non-root user
USER ampeval

# Default command
CMD ["python", "-m", "amp_eval.cli"]

# Production stage with minimal dependencies
FROM python:3.11-alpine AS production

# Install only runtime dependencies
RUN apk add --no-cache git && \
    rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S ampeval && \
    adduser -u 1001 -S ampeval -G ampeval

WORKDIR /app

# Copy only production dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=ampeval:ampeval src/ ./src/
COPY --chown=ampeval:ampeval adapters/ ./adapters/
COPY --chown=ampeval:ampeval evals/ ./evals/
COPY --chown=ampeval:ampeval config/ ./config/
COPY --chown=ampeval:ampeval pyproject.toml ./

# Install package
RUN pip install --no-cache-dir .

# Switch to non-root user
USER ampeval

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import amp_eval; print('healthy')" || exit 1

# Default command
CMD ["amp-eval", "--help"]
