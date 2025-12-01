# 🚀 How to Start Celery Background Workers

## Prerequisites

1. **Install Redis** (the message broker)
```bash
# On macOS:
brew install redis

# Start Redis (keep this running):
brew services start redis

# Or start manually:
redis-server
```

2. **Install Celery** (should already be installed)
```bash
pip install celery redis
```

## Starting ZoolZ with Background Tasks

You need **3 terminal windows**:

### Terminal 1: Redis Server
```bash
# Start Redis (if not using brew services)
redis-server

# You should see:
# * Ready to accept connections
```

### Terminal 2: Celery Worker
```bash
# Navigate to ZoolZ directory
cd /Users/isaiahmiro/Desktop/ZoolZ

# Activate your venv
source venv/bin/activate  # or whatever your venv is called

# Start Celery worker
celery -A tasks worker --loglevel=info

# You should see:
# celery@YourMac ready.
# - tasks.generate_cookie_cutter
# - tasks.thicken_mesh
# - tasks.hollow_mesh
# - tasks.boolean_operation
```

### Terminal 3: Flask App
```bash
# Navigate to ZoolZ directory
cd /Users/isaiahmiro/Desktop/ZoolZ

# Activate your venv
source venv/bin/activate

# Start Flask
python3 app.py

# Visit: http://localhost:5001
```

## Testing Background Tasks

1. Upload an image for cookie cutter
2. Click "Generate"
3. You'll see a progress bar!
4. Check Terminal 2 to see Celery processing the task
5. Multiple users can now generate at the same time!

## Stopping Everything

```bash
# Stop Flask: Ctrl+C in Terminal 3
# Stop Celery: Ctrl+C in Terminal 2
# Stop Redis: Ctrl+C in Terminal 1 (or brew services stop redis)
```

## Troubleshooting

### "Connection refused" error:
- Redis isn't running. Start it with `redis-server`

### "No module named 'celery'":
- Install it: `pip install celery redis`

### Tasks not running:
- Make sure Celery worker is running in Terminal 2
- Check for errors in the Celery terminal

## Production Deployment

For production, use supervisord or systemd to keep Redis and Celery running:

```bash
# Example supervisord config:
[program:celery]
command=/path/to/venv/bin/celery -A tasks worker --loglevel=info
directory=/path/to/ZoolZ
user=youruser
autostart=true
autorestart=true
```

That's it! You now have background task processing! 🎉
