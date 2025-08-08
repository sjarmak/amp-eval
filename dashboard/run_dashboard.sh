#!/bin/bash
"""
Launch script for Amp Evaluation Dashboard
"""

# Set environment variables if not already set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Default configuration
DEFAULT_PORT=8501
DEFAULT_RESULTS_DIR="../results"

# Parse command line arguments
PORT=${1:-$DEFAULT_PORT}
RESULTS_DIR=${2:-$DEFAULT_RESULTS_DIR}

echo "🚀 Starting Amp Model Evaluation Dashboard"
echo "   Port: $PORT"
echo "   Results Directory: $RESULTS_DIR"
echo "   Dashboard URL: http://localhost:$PORT"
echo ""

# Check if results directory exists
if [ ! -d "$RESULTS_DIR" ]; then
    echo "⚠️  Warning: Results directory '$RESULTS_DIR' not found"
    echo "   Run evaluations first to generate data"
fi

# Install dependencies if needed
if [ ! -f "venv/bin/activate" ]; then
    echo "📦 Installing dependencies..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Import existing JSON files to metrics store
echo "📊 Importing evaluation results..."
python metrics_store.py --import-json --results-dir "$RESULTS_DIR"

# Launch Streamlit dashboard
echo "🌐 Launching dashboard..."
streamlit run streamlit_app.py --server.port "$PORT" --server.headless true
