#!/bin/bash
# ZoolZ Startup Script - Starts Redis, Celery, and Flask

echo "🚀 Starting ZoolZ 3D Modeling Program..."
echo ""
echo "💡 Git quick commands (run in ZoolZ folder):"
echo "   git pull    # grab latest from origin"
echo "   git status  # check local changes"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "⚠️  Redis not installed. Install with: brew install redis"
    echo "   Continuing without background tasks..."
    START_CELERY=false
else
    START_CELERY=true
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down ZoolZ..."

    # Stop Celery worker
    if [ ! -z "$CELERY_PID" ]; then
        echo "   Stopping Celery..."
        kill -TERM $CELERY_PID 2>/dev/null
        sleep 2
        # Force kill if still running
        kill -9 $CELERY_PID 2>/dev/null || true
    fi

    # Stop Redis (if we started it)
    if command -v brew &> /dev/null; then
        echo "   Stopping Redis..."
        brew services stop redis &> /dev/null || true
    fi

    echo "✅ Shutdown complete"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Redis
if [ "$START_CELERY" = true ]; then
    echo "📦 Starting Redis..."

    # Try to start Redis with brew services first (better for server)
    if command -v brew &> /dev/null; then
        brew services start redis &> /dev/null || true
        sleep 1
    fi

    # Check if Redis is running
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"

        # Start Celery
        echo "⚙️  Starting Celery worker..."
        celery -A tasks.celery worker --loglevel=info > celery.log 2>&1 &
        CELERY_PID=$!
        sleep 2 # Wait for Celery to start

        if ps -p $CELERY_PID > /dev/null; then
            echo "✅ Celery started (PID: $CELERY_PID)"
            echo "   Background tasks ENABLED ⚡"
        else
            echo "❌ Failed to start Celery"
            echo "   Check celery.log for details"
            START_CELERY=false
        fi
    else
        echo "❌ Redis not running"
        echo "   Start it with: brew services start redis"
        START_CELERY=false
    fi
fi

echo ""
echo "🌐 Starting Flask web server..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   🎨 ZoolZ Studio"
echo "   Local:    http://localhost:5001"
echo "   Network:  http://$(ipconfig getifaddr en0 2>/dev/null || echo "localhost"):5001"
echo "   External: http://71.60.55.85:5001"
echo ""
if [ "$START_CELERY" = true ]; then
    echo "   ⚡ Background tasks: ENABLED"
else
    echo "   ⚠️  Background tasks: DISABLED"
    echo "      (Operations will run synchronously)"
fi
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start Flask (foreground)
python3 app.py

# Cleanup on exit
cleanup
