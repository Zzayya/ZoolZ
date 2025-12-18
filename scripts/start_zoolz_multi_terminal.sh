#!/bin/bash
# ZoolZ Multi-Terminal Launcher
# Opens separate terminals for Flask, Celery, and Redis monitoring

echo "🚀 Launching ZoolZ in Multi-Terminal Mode..."
echo ""
echo "💡 Git quick commands (run in ZoolZ folder):"
echo "   git pull    # grab latest from origin"
echo "   git status  # check local changes"
echo ""

# Get current directory
ZOOLZ_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Multi-terminal mode only works on macOS"
    echo "   Use ./start_zoolz.sh instead"
    exit 1
fi

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "   Run setup script first: ./zoolz/server/setup_server_FINAL.sh"
    exit 1
fi

# Start Redis service
echo "📦 Starting Redis..."
brew services start redis &> /dev/null || true
sleep 2

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "❌ Redis failed to start"
    echo "   Install with: brew install redis"
    exit 1
fi
echo "✅ Redis running"

# Detect server IP address
if [ -f ~/Desktop/SERVER ]; then
    # Server mode - get actual IP
    SERVER_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")
else
    SERVER_IP="localhost"
fi

# Terminal 1: Flask Server
echo "🌐 Opening Flask terminal..."
osascript -e "tell application \"Terminal\" to do script \"cd '$ZOOLZ_DIR' && source venv/bin/activate && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' && echo '   🌐 FLASK WEB SERVER' && echo '   Local:  http://'$SERVER_IP':5001' && echo '   Public: http://71.60.55.85:5001' && echo '   Login:  Zay / 442767' && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' && echo '' && python3 app.py\"" &

sleep 2

# Terminal 2: Celery Worker
echo "⚙️  Opening Celery terminal..."
osascript -e "tell application \"Terminal\" to do script \"cd '$ZOOLZ_DIR' && source venv/bin/activate && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' && echo '   ⚙️  CELERY WORKER (Background Tasks)' && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' && echo '' && celery -A tasks.celery worker --loglevel=info\"" &

sleep 1

# Terminal 3: Redis Monitor
echo "📊 Opening Redis monitor..."
osascript -e "tell application \"Terminal\" to do script \"cd '$ZOOLZ_DIR' && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' && echo '   📊 REDIS MONITOR (Live Commands)' && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' && echo '' && redis-cli monitor\"" &

sleep 1

# Terminal 4: System Stats
echo "📈 Opening system stats..."
osascript -e "tell application \"Terminal\" to do script \"cd '$ZOOLZ_DIR' && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' && echo '   📈 SYSTEM STATS & LOGS' && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' && echo '' && while true; do clear; echo '═══ FLASK LOG (last 20 lines) ═══'; tail -20 zoolz_server.log 2>/dev/null || echo 'No Flask log yet'; echo ''; echo '═══ CELERY LOG (last 20 lines) ═══'; tail -20 celery.log 2>/dev/null || echo 'No Celery log yet'; echo ''; echo '═══ SYSTEM RESOURCES ═══'; echo 'CPU:' \$(top -l 1 | grep 'CPU usage' | awk '{print \$3, \$5}'); echo 'Memory:' \$(top -l 1 | grep PhysMem | awk '{print \$2, \$6}'); echo ''; echo '(Refreshing every 3 seconds... Press Ctrl+C to stop)'; sleep 3; done\"" &

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🚀 ZOOLZ LAUNCHED IN 4 TERMINALS! 🚀              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Terminal 1: Flask web server (http://localhost:5001)"
echo "✅ Terminal 2: Celery background tasks"
echo "✅ Terminal 3: Redis live monitor"
echo "✅ Terminal 4: System stats & logs"
echo ""
echo "🛑 To stop everything:"
echo "   1. Close Terminal 1 (Flask) with Ctrl+C"
echo "   2. Close Terminal 2 (Celery) with Ctrl+C"
echo "   3. Close Terminal 3 (Redis monitor) with Ctrl+C"
echo "   4. Run: brew services stop redis"
echo ""
echo "Or use: pkill -f 'python.*app.py' && pkill -f celery && brew services stop redis"
echo ""
