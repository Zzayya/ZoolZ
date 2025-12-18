#!/bin/bash
# Quick restart ZoolZ on the server
# Run this ON THE SERVER (not laptop)

echo "🔄 Restarting ZoolZ..."

# Kill existing processes
pkill -f 'python.*app.py' 2>/dev/null
pkill -f 'celery' 2>/dev/null

sleep 2

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Start fresh
echo "🚀 Starting ZoolZ..."
./start_zoolz.sh
