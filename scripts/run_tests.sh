#!/bin/bash
# Comprehensive test runner for multi-video analysis system

set -e

echo "🧪 Running Multi-Video Analysis System Tests"
echo "============================================="

# Activate virtual environment
source venv/bin/activate

# Check if Qdrant is running
echo "🔍 Checking Qdrant status..."
if ! curl -s http://localhost:6333/collections > /dev/null; then
    echo "⚠️ Qdrant not running. Starting it..."
    python scripts/fix_qdrant_ssl.py
fi

echo ""
echo "📝 Running Unit Tests..."
echo "------------------------"
python -m pytest tests/unit/ -v --tb=short

echo ""
echo "🔗 Running Integration Tests..."
echo "-------------------------------"
python -m pytest tests/integration/ -v --tb=short

echo ""
echo "📊 Running Tests with Coverage..."
echo "---------------------------------"
python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html:htmlcov

echo ""
echo "✅ All Tests Complete!"
echo "📈 Coverage report saved to: htmlcov/index.html"
echo ""
echo "🌐 To test API endpoints interactively:"
echo "   1. Start server: uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000"
echo "   2. Open browser: http://localhost:8000/docs"
echo "" 