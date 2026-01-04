#!/bin/bash

# Enterprise AI Analyst System - Startup Script

echo "🚀 Starting Enterprise AI Analyst System..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY"
    echo
fi

# Check for OpenAI API key
if grep -q "sk-your-api-key-here" .env; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set in .env file"
    echo "   Edit .env and replace sk-your-api-key-here with your actual API key"
    echo
fi

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API docs will be available at http://localhost:8000/docs"
echo
echo "Press Ctrl+C to stop the server"
echo

python -m app.main
