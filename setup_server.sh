#!/bin/bash
# Server First-Time Setup Script
# Run this ONCE on the Mac server after transferring files

echo "=========================================="
echo "   ZOOLZ SERVER SETUP"
echo "=========================================="
echo ""

# Check if we're on the server
if [ ! -f "$HOME/Desktop/SERVER" ]; then
    echo "⚠️  Server marker file not found!"
    echo ""
    echo "IMPORTANT: You need to create a marker file first!"
    echo "Run this command:"
    echo "  touch ~/Desktop/SERVER"
    echo ""
    read -p "Press Enter after creating the file, or Ctrl+C to exit..."
    echo ""

    # Check again
    if [ ! -f "$HOME/Desktop/SERVER" ]; then
        echo "❌ Marker file still not found. Exiting."
        exit 1
    fi
fi

echo "✅ Server marker file detected"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python3 --version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 7) else 1)'; then
    echo "❌ Python 3.7+ required! Current version: $PYTHON_VERSION"
    echo "Please install Python 3.7 or higher from python.org"
    exit 1
fi
echo "✅ Python version OK"
echo ""

# Remove old/broken venv if it exists
if [ -d "venv" ]; then
    echo "🗑️  Removing old virtual environment..."
    rm -rf venv
    echo "✅ Old venv removed"
fi

# Create fresh virtual environment
echo "📦 Creating fresh virtual environment..."
python3 -m venv venv
if [ $? -eq 0 ]; then
    echo "✅ Virtual environment created successfully"
else
    echo "❌ Failed to create virtual environment"
    exit 1
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo ""

# Install requirements
echo "📥 Installing Python packages from requirements.txt..."
echo "This might take a few minutes..."
echo ""
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Some packages failed to install."
    echo "This is often okay - we can troubleshoot specific issues."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# spaCy model (DISABLED - using regex fallback instead)
echo "ℹ️  Skipping spaCy language model (not needed - using regex fallback)"
echo "   PeopleFinder will use regex-based entity extraction instead"
echo ""

# Check Redis
echo "🔍 Checking if Redis is installed..."
if command -v redis-server &> /dev/null; then
    echo "✅ Redis found: $(redis-server --version)"
else
    echo "⚠️  Redis not found."
    echo "Modeling program needs Redis for background tasks."
    echo ""
    echo "To install Redis on Mac:"
    echo "  brew install redis"
    echo ""
    read -p "Continue without Redis? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Verify ZoolZmstr works
echo "🧪 Testing ZoolZmstr..."
python3 -c "from ZoolZmstr import is_server, get_environment; print(f'Environment: {get_environment()}'); print('Server mode: {}'.format('YES ✅' if is_server() else 'NO ❌'))"

if [ $? -ne 0 ]; then
    echo "❌ ZoolZmstr test failed!"
    echo "Something is wrong with the installation."
    exit 1
fi
echo ""

# Test config loads
echo "🧪 Testing config..."
python3 -c "from config import Config; print(f'Database folder: {Config.DATABASE_FOLDER}')"

if [ $? -ne 0 ]; then
    echo "❌ Config test failed!"
    exit 1
fi
echo ""

echo "=========================================="
echo "   ✅ SERVER SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Login credentials:"
echo "  Username: Zay"
echo "  Password: 442767"
echo ""
echo "Access at: http://localhost:5001"
echo ""
echo "=========================================="
echo ""
echo "🚀 Starting Zoolz now..."
echo ""

# Auto-start Zoolz
./start_zoolz.sh
