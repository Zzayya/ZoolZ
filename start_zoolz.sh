#!/bin/bash
# ZoolZ Startup Script

echo "🚀 Starting ZoolZ Hub..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Start Flask app
echo "✅ Starting server on http://localhost:5001"
echo "🔑 Use passkey: 442767"
echo ""
python app.py
