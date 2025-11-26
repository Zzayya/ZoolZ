#!/bin/bash
# Quick test script for modeling UI fixes

echo "🔧 Installing usaddress..."
source venv/bin/activate
pip install usaddress

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "🚀 Starting ZoolZ..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Open: http://localhost:5001"
echo "  Login: 442767"
echo "  Click: 3D Modeling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Test checklist:"
echo "  1. Drag Blues Clues image to viewer"
echo "  2. See image preview in left sidebar"
echo "  3. Click 'Extract Outline'"
echo "  4. Generate cookie cutter"
echo "  5. Check galaxy background & fixed sidebar!"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
