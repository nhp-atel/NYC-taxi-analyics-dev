#!/bin/bash
# Setup script for local development environment

set -e

echo "=== NYC Taxi Analytics - Local Setup ==="
echo

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$PYTHON_VERSION" < "3.11" ]]; then
    echo "Error: Python 3.11+ is required (found $PYTHON_VERSION)"
    exit 1
fi
echo "✓ Python $PYTHON_VERSION"

# Check for required tools
check_tool() {
    if command -v "$1" &> /dev/null; then
        echo "✓ $1 found"
    else
        echo "✗ $1 not found - please install it"
        return 1
    fi
}

echo
echo "Checking required tools..."
check_tool "gcloud"
check_tool "terraform"
check_tool "docker"
check_tool "docker-compose" || check_tool "docker compose"

# Create virtual environment
echo
echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e ".[dev]"

# Install pre-commit hooks
echo
echo "Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type pre-push

# Create data directory
echo
echo "Creating data directory..."
mkdir -p data

# Check GCP authentication
echo
echo "Checking GCP authentication..."
if gcloud auth application-default print-access-token &> /dev/null; then
    echo "✓ GCP authentication configured"
else
    echo "⚠ GCP authentication not configured"
    echo "  Run: gcloud auth application-default login"
fi

echo
echo "=== Setup Complete ==="
echo
echo "Next steps:"
echo "  1. Download sample data: make download-sample"
echo "  2. Run producer in dry-run mode: make producer"
echo "  3. Start local Airflow: make airflow"
echo "  4. Run API locally: make api"
echo
echo "For GCP deployment:"
echo "  1. Create project 'nyc-taxi-analytics-dev' in GCP Console"
echo "  2. Enable required APIs"
echo "  3. Run: make terraform-init && make terraform-apply"
