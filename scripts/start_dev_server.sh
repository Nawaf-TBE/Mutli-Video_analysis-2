#!/bin/bash
# Development server startup script

set -e

echo "🚀 Starting Multi-Video Analysis Development Server"
echo "=================================================="

# Activate virtual environment
source venv/bin/activate

# Check and start Qdrant if needed
echo "🔍 Checking dependencies..."
if ! curl -s http://localhost:6333/collections > /dev/null; then
    echo "⚠️ Qdrant not running. Starting it..."
    python scripts/fix_qdrant_ssl.py
fi

# Check Node.js transcript server
if ! curl -s http://localhost:4000/health > /dev/null 2>&1; then
    echo "⚠️ Node.js transcript server not running."
    echo "💡 Start it manually: cd yt-transcript-server && npm start"
fi

# Start PostgreSQL if not running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "⚠️ PostgreSQL not running. Starting it..."
    brew services start postgresql
fi

echo ""
echo "🌐 Starting FastAPI server..."
echo "Server will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "API Redoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000 