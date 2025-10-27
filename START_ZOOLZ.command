#!/bin/bash
# ZoolZ Flask App Launcher (Mac/Linux)
# Double-click this file to start the app

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "========================================="
echo "   ZoolZ - Multi-Purpose 3D Design Tool"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ ERROR: Virtual environment not found!"
    echo "Please run setup from the project directory first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    read -p "Press any key to exit..."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Dependencies not installed!"
    echo "Please install dependencies first:"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    read -p "Press any key to exit..."
    exit 1
fi

echo "✅ Dependencies OK"
echo ""
echo "🚀 Starting ZoolZ..."
echo ""
echo "========================================="
echo "   App will open at: http://localhost:5001"
echo "========================================="
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Open browser after 2 seconds (in background)
(sleep 2 && open http://localhost:5001) &

# Start Flask app
python app.py

# Wait for user input before closing
echo ""
echo "Server stopped."
read -p "Press any key to exit..."
