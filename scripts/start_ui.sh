#!/bin/bash
# Quick launcher for Streamlit UI

set -e

echo "🚀 Starting KYC Document Verification UI..."
echo ""

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run:"
    echo "   uv venv .venv && source .venv/bin/activate && uv pip install -e ."
    exit 1
fi

# Activate venv
source .venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Create one with: cp env.example .env"
    echo "   Then set FIREWORKS_API_KEY"
    echo ""
fi

# Launch Streamlit
echo "✅ Launching UI at http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

streamlit run app.py

