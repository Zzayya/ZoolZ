# ZoolZ Deployment Guide

## Quick Start (Mac Server Setup)

### 1. First-Time Setup

```bash
# Clone repository
cd ~/Desktop
git clone <your-repo-url> ZoolZ
cd ZoolZ

# Install dependencies
./install_requirements.sh

# Create .env file
cp .env.example .env
nano .env  # Edit with your settings
```

### 2. Start ZoolZ

#### Development (Manual)
```bash
./run_dev.sh
```

#### Production (Recommended: Use Swift Admin Panel)
The Swift admin panel will handle starting/stopping/restarting ZoolZ for you!

---

## Swift Admin Panel Integration

### API Endpoints for Your Swift App

#### 1. Get Status
```swift
func getStatus() async -> ZoolzStatus {
    let url = URL(string: "http://mac-server:5001/api/admin/status")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(ZoolzStatus.self, from: data)
}

// Response:
{
  "services": {
    "redis": {"running": true, "port": 6379},
    "celery": {"running": true}
  },
  "programs": {
    "modeling": {"active": true, "dependencies": ["redis", "celery"]},
    "people_finder": {"active": false}
  },
  "system": {
    "flask_running": true,
    "pid": 12345,
    "python_version": "3.12.4"
  }
}
```

#### 2. Start/Stop Services
```swift
func startService(_ name: String) async {
    let url = URL(string: "http://mac-server:5001/api/admin/service/\(name)/start")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    let (data, _) = try await URLSession.shared.data(for: request)
    // Handle response
}

// Available services: "redis", "celery"
```

#### 3. View Logs
```swift
func getLogs(service: String, lines: Int = 100) async -> [String] {
    let url = URL(string: "http://mac-server:5001/api/admin/logs/\(service)?lines=\(lines)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    let response = try JSONDecoder().decode(LogResponse.self, from: data)
    return response.lines
}

// Available: "flask", "redis", "celery"
```

#### 5. Restart Specific Program
```swift
func restartProgram(_ programId: String) async {
    let url = URL(string: "http://mac-server:5001/api/admin/program/\(programId)/restart")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    try await URLSession.shared.data(for: request)
}

// Available: "modeling", "parametric", "people_finder", "digital_footprint"
```

---

## File Synchronization

**Use rsync** for file syncing:
1. Edit code on laptop
2. Run `./sync_to_server.sh` (syncs to Mac server)
3. Use admin panel "Restart" button to reload changes
4. Done!

**Setup rsync:**
```bash
# On laptop: Edit sync_to_server.sh with your Mac's IP/hostname
# Then run: ./sync_to_server.sh
# Excludes: venv/, __pycache__/, .env
```

---

## Architecture Answers

### Can We Run Multiple Programs Simultaneously?

**YES!** ZoolZ intelligently manages services.

**Example 1: Modeling + People Finder**
```
User opens Modeling      → Redis: STARTS, Celery: STARTS
User opens People Finder → Redis: STAYS RUNNING, Celery: STAYS RUNNING
User closes Modeling     → Redis: STAYS (PF might need it), Celery: STOPS
User closes People Finder→ Redis: STOPS (nothing needs it)
```

**Example 2: Just People Finder**
```
User opens People Finder → Redis: NOT STARTED (not needed)
                        → Celery: NOT STARTED (not needed)
```

### Can We Restart Just One Program?

**YES!** Two ways:

1. **Restart Program's Services** (doesn't restart Flask)
```bash
POST /api/admin/program/modeling/restart
# Stops and restarts Redis + Celery for Modeling
# Flask keeps running, other programs unaffected
```

2. **Full Flask Restart** (restarts everything)
```bash
POST /api/admin/restart
# Restarts entire Flask process
# All programs restart, services reset
```

### Can Programs Open in Separate Windows?

**YES!** Each program has its own URL:

```
http://localhost:5001/modeling          (3D Modeling)
http://localhost:5001/parametric        (Parametric CAD)
http://localhost:5001/people_finder     (People Finder)
http://localhost:5001/footprint         (Digital Footprint)
```

Open each in a separate browser tab/window. They all work independently!

### Where Does Processing Happen?

**Mac Server does ALL heavy processing:**
- STL file generation
- Mesh thickening/hollowing
- ML model inference (People Finder)
- Database queries
- Background tasks (Celery)

**Laptop/Browser does light processing:**
- 3D preview rendering (Three.js in browser)
- Form validation (JavaScript)
- UI interactions

**Benefits:**
- Your laptop stays cool and fast
- Mac server (with more RAM/CPU) handles heavy work
- You can close laptop and server keeps processing
- Multiple users can access same server

### If We Only Update CAD, Do We Restart Everything?

**No!** Options:

1. **Smart Restart** (recommended)
```bash
POST /api/admin/program/parametric/restart
# Only restarts CAD program's services
# Modeling, People Finder keep running
```

2. **Full Restart** (if you changed core files)
```bash
POST /api/admin/restart
# Restarts all of Flask
# Use this if you changed app.py, config.py, etc.
```

---

## Production Checklist

### Before Deploying to Mac Server:

- [ ] Update `.env` with production SECRET_KEY
- [ ] Set `FLASK_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Configure absolute paths in `.env`:
  ```
  UPLOAD_FOLDER=/Users/isaiahmiro/Desktop/ZoolZ/uploads
  OUTPUT_FOLDER=/Users/isaiahmiro/Desktop/ZoolZ/outputs
  DATABASE_FOLDER=/Users/isaiahmiro/Desktop/ZoolZ/database
  ```
- [ ] Ensure Redis is installed: `brew install redis`
- [ ] Test admin API endpoints work
- [ ] Set up SSH access from laptop to Mac server
- [ ] Configure `sync_to_server.sh` with Mac server IP

### Swift Admin Panel Features to Implement:

- [ ] Dashboard with service status cards
- [ ] Start/Stop/Restart buttons for each service
- [ ] "Restart" button to reload after file changes
- [ ] Live log viewer (tail logs in real-time)
- [ ] System resource monitoring (CPU/RAM)
- [ ] Notification when service crashes
- [ ] Health check heartbeat

---

## Troubleshooting

### Services Won't Start

**Redis:**
```bash
# Check if Redis is installed
redis-cli --version

# Install if missing
brew install redis

# Test manually
redis-server
```

**Celery:**
```bash
# Test manually
cd ~/Desktop/ZoolZ
source venv/bin/activate
celery -A tasks worker --loglevel=info

# Check for errors in output
```

### Flask Won't Start

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check venv
source venv/bin/activate
which python3  # Should be in venv

# Check dependencies
pip list | grep Flask

# Test manually
python3 app.py
```

### Admin API Not Working

```bash
# Test health endpoint
curl http://localhost:5001/api/admin/health

# Test status endpoint
curl http://localhost:5001/api/admin/status

# Check Flask logs
tail -f flask.log
```

---

## Security Notes

### Production Security

1. **Use HTTPS** (get SSL certificate)
2. **Firewall** - Only allow your laptop's IP
3. **Update password hashing** - Replace SHA-256 with bcrypt:
   ```python
   import bcrypt
   hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
   ```
4. **Rate limiting** - Add to admin endpoints
5. **Authentication** - Add API key for admin panel

### Admin API Authentication (TODO)

Add this to `admin_api.py`:

```python
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('ADMIN_API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Then add to routes:
@admin_bp.route('/status')
@require_api_key
def get_status():
    ...
```

---

## Performance Tips

1. **Redis Memory** - Set max memory limit:
   ```bash
   redis-cli CONFIG SET maxmemory 256mb
   redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

2. **Celery Workers** - Adjust worker count:
   ```bash
   celery -A tasks worker --concurrency=4
   ```

3. **Flask** - Use production WSGI server (future):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5001 app:app
   ```

---

## Support

If something breaks:
1. Check logs: `/api/admin/logs/flask`
2. Check service status: `/api/admin/status`
3. Restart everything: `/api/admin/restart`
4. Pull latest code: `/api/admin/git/pull`
5. Check GitHub issues
