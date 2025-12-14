# ZoolZ Core - Intelligent Program Orchestrator

This directory contains the core logic for ZoolZ, which intelligently manages programs and their service dependencies.

## Architecture

```
zoolz/
├── core.py              # Main orchestrator (brain of ZoolZ)
├── service_manager.py   # Manages Redis, Celery, etc.
├── program_registry.py  # Defines program dependencies
├── admin_api.py         # REST API for Swift admin panel
└── auth.py              # User authentication (TODO: move from app.py)
```

## How It Works

### 1. Program Access Tracking

When a user opens a program (e.g., 3D Modeling), Flask middleware detects this and notifies the orchestrator:

```python
# In app.py middleware
orchestrator.on_program_access('modeling')
```

### 2. Automatic Service Startup

The orchestrator checks what services the program needs and starts them automatically:

```python
# Modeling needs Redis + Celery
# People Finder needs nothing
# Parametric CAD needs Redis + Celery
```

### 3. Smart Cleanup

When no programs need a service, it's automatically stopped to save resources:

```python
# User closes Modeling → stops Redis + Celery (if not needed by others)
# User opens People Finder → no services needed, nothing starts
```

### 4. Multiple Programs

You can run multiple programs simultaneously! ZoolZ tracks all active programs and ensures required services stay running:

```
Active: Modeling + People Finder
→ Redis: RUNNING (needed by Modeling)
→ Celery: RUNNING (needed by Modeling)

Active: People Finder + Digital Footprint
→ Redis: STOPPED (not needed)
→ Celery: STOPPED (not needed)
```

## Program Registry

Add new programs to `program_registry.py`:

```python
PROGRAM_DEPENDENCIES = {
    'modeling': ['redis', 'celery'],
    'my_new_program': ['redis'],  # Add your program here
}

PROGRAM_INFO = {
    'my_new_program': {
        'name': 'My New Program',
        'description': 'What it does',
        'url_prefix': '/my_program',
        'heavy_processing': False,
    }
}
```

Then register the blueprint in `app.py`:

```python
from programs.MyNewProgram.blueprint import my_new_bp
app.register_blueprint(my_new_bp, url_prefix='/my_program')
```

ZoolZ will automatically handle service orchestration!

## Admin API

The Swift admin panel uses these endpoints:

### Status
```bash
GET /api/admin/status
# Returns: services status, active programs, system info
```

### Service Control
```bash
POST /api/admin/service/redis/start
POST /api/admin/service/redis/stop
POST /api/admin/service/redis/restart
```

### Program Control
```bash
POST /api/admin/program/modeling/restart
# Restarts just the Modeling program services
```

### Flask Control
```bash
POST /api/admin/restart   # Restart Flask
POST /api/admin/shutdown  # Shutdown everything
```

### Logs
```bash
GET /api/admin/logs/flask?lines=100
GET /api/admin/logs/redis?lines=50
GET /api/admin/logs/celery?lines=100
```

## File Synchronization

**Use rsync** for file syncing:
1. Edit code on laptop
2. Run `./sync_to_server.sh` from laptop
3. Use admin panel "Restart" button to reload changes

rsync automatically excludes: venv/, __pycache__/, .env, *.pyc

## Server/Client Architecture

### Current: All Processing on Server

Right now, ALL processing happens on the Mac server:
- Flask runs on server
- Redis/Celery on server
- 3D processing on server
- ML models on server

Your laptop just displays the web UI.

**Benefits:**
- Laptop stays fast and cool
- Server handles heavy 3D processing
- Can close laptop and processing continues

### Future: Hybrid Processing

We could split light/heavy tasks:

**Server (Heavy):**
- Cookie cutter generation
- STL thickening/hollowing
- ML model inference
- Database queries

**Client (Light):**
- 3D preview rendering (Three.js)
- Form validation
- UI interactions

This would require client-side JavaScript to handle light tasks and send heavy tasks to the server via API calls. The current setup already does this naturally!

## Adding New Services

To add a new service (e.g., PostgreSQL):

1. **Add to `service_manager.py`:**

```python
self.services['postgres'] = {
    'running': False,
    'pid': None,
    'port': 5432,
    'start_command': 'pg_ctl start -D /path/to/data',
    'stop_command': 'pg_ctl stop',
    'check_command': 'pg_isready',
}
```

2. **Add to program dependencies:**

```python
PROGRAM_DEPENDENCIES = {
    'modeling': ['redis', 'celery', 'postgres'],  # Now needs Postgres
}
```

ZoolZ will automatically manage it!

## Development vs Production

### Development (Laptop)
```bash
./run_dev.sh
# Starts Flask only
# Services start on-demand
```

### Production (Mac Server)
Use the Swift admin panel to:
1. Pull latest code from Git
2. Restart Flask
3. Monitor service status
4. View logs

## Questions Answered

### Can we run multiple programs at once?
**YES!** ZoolZ tracks all active programs and ensures shared services stay running.

### Can we restart just one program?
**YES!** Use `/api/admin/program/<program_id>/restart` to restart a specific program's services without restarting all of Flask.

### Can programs open in separate windows?
**YES!** Each program is at a different URL:
- Modeling: http://localhost:5001/modeling
- People Finder: http://localhost:5001/people_finder
- CAD: http://localhost:5001/parametric

Open each in a separate browser tab/window!

### Does processing happen on server or client?
**Server.** Your laptop just shows the web UI. The Mac server does all the heavy lifting (STL processing, ML, etc.).

### How does Swift admin panel work?
It calls the REST API endpoints in `admin_api.py` to:
- Start/stop services
- Restart Flask
- View logs
- Monitor status

## Example Workflow

1. **Developer on laptop:**
   - Edit code
   - Run `./sync_to_server.sh`

2. **Swift admin panel:**
   - Click "Restart"
   - Calls `/api/admin/restart`

3. **ZoolZ on Mac server:**
   - Restarts Flask (loads rsync'd files)
   - Resumes serving requests

4. **User accesses Modeling:**
   - ZoolZ detects access
   - Starts Redis
   - Starts Celery
   - User can generate cookie cutters

5. **User closes Modeling:**
   - ZoolZ detects no active programs need Redis/Celery
   - Stops Redis
   - Stops Celery
   - Saves resources
