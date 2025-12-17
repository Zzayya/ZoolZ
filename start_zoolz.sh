#!/bin/bash
# ZoolZ Unified Startup Script
# Uses smart process management - services start automatically when needed

echo "🚀 Starting ZoolZ Studio..."
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check dependencies
echo "🔍 Checking system dependencies..."
if ! command -v redis-server &> /dev/null; then
    echo "⚠️  Warning: Redis not installed"
    echo "   Install with: brew install redis (Mac) or apt install redis (Linux)"
    echo "   Modeling features will run synchronously without Redis"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   🎨 ZoolZ Studio - Multi-Purpose 3D Design Suite"
echo ""
echo "   🌐 Access at: http://localhost:5001"
echo ""
echo "   Programs:"
echo "   • 3D Modeling       → /modeling"
echo "   • Parametric CAD    → /parametric"
echo "   • People Finder     → /people_finder"
echo "   • Digital Footprint → /footprint"
echo ""
echo "   ⚡ Smart Process Management ENABLED"
echo "      Services auto-start when programs need them"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start Flask - it handles everything else via ZoolZmstr
python3 app.py
