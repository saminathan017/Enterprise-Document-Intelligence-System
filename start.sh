#!/bin/bash

# Enterprise AI Agent Quick Start Script
# This script starts the backend server and opens the frontend

echo "🚀 Starting Enterprise AI Agent..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "✅ Virtual environment activated"
echo ""

# Open frontend in browser
echo "🌐 Opening frontend in browser..."
open frontend/index.html
sleep 1

# Start the backend server
echo "🔧 Starting backend server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python -m app.main
