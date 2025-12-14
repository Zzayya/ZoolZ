#!/bin/bash
# Development launcher for ZoolZ
# For production, use the Swift Admin Panel

echo "🚀 Starting ZoolZ (Development Mode)"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "❌ No virtual environment found. Run ./install_requirements.sh first."
    exit 1
fi

# Set development mode
export FLASK_ENV=development
export DEBUG=True

echo "🌐 Starting Flask..."
echo "   ZoolZ will intelligently start Redis/Celery when needed"
echo "   Access at: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run Flask
python3 app.py
