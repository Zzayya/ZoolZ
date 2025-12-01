#!/bin/bash
# ZoolZ Startup Script - Starts Redis, Celery, and Flask

echo "🚀 Starting ZoolZ 3D Modeling Program..."
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
    if [ ! -z "$REDIS_PID" ]; then
        echo "   Stopping Redis..."
        kill $REDIS_PID 2>/dev/null
    fi
    if [ ! -z "$CELERY_PID" ]; then
        echo "   Stopping Celery..."
        kill $CELERY_PID 2>/dev/null
    fi
    echo "✅ Shutdown complete"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Redis
if [ "$START_CELERY" = true ]; then
    echo "📦 Starting Redis..."
    redis-server --daemonize yes --port 6379
    REDIS_PID=$(pgrep -f "redis-server.*6379")

    if [ -z "$REDIS_PID" ]; then
        echo "❌ Failed to start Redis"
        START_CELERY=false
    else
        echo "✅ Redis started (PID: $REDIS_PID)"

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
    fi
fi

echo ""
echo "🌐 Starting Flask web server..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   ZoolZ 3D Modeling Program"
echo "   URL: http://localhost:5000"
echo "   Passkey: 442767"
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
