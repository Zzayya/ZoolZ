# ZoolZmstr - Zoolz Master Control Logic

**The brain of Zoolz.** This folder contains all the master orchestration logic for the Zoolz hub system.

## What is ZoolZmstr?

ZoolZmstr is Zoolz's intelligent control system that:
- **Detects environment** - Knows if running on server vs laptop
- **Manages folders** - Sets up clean data structure on the server
- **Orchestrates processes** - Boots Redis/Celery only when needed
- **Coordinates programs** - Handles the 4 (soon to be 65+) programs

Think of it as Zoolz's operating system.

---

## Architecture

### Current Structure

```
ZoolZmstr/
├── __init__.py           # Public API exports
├── detection.py          # Server vs laptop detection
├── folder_manager.py     # ZoolZData folder setup
├── process_manager.py    # Smart process orchestration
├── launcher.py           # Program coordination (future expansion)
└── README.md            # This file
```

---

## Components

### 1. Detection (`detection.py`)

**Purpose:** Know where Zoolz is running

**How it works:**
- Looks for `~/Desktop/SERVER`
- If the marker exists → **server mode** (use ZoolZData folders)
- If not → **laptop mode** (use local project folders)

**Usage:**
```python
from ZoolZmstr import is_server, get_environment

if is_server():
    print("Running on Mac server")
else:
    print("Running on laptop")

env = get_environment()  # Returns 'server' or 'laptop'
```

**Setup server mode:**
```bash
touch ~/Desktop/SERVER
```

---

### 2. Folder Manager (`folder_manager.py`)

**Purpose:** Keep code clean, data organized

**The Problem:**
- Code folder gets synced between laptop/server (via rsync)
- Can't have server data (uploads, databases, logs) mixed with code
- Need separate, organized structure on server

**The Solution:**
```
# On Laptop (development):
ZoolZ/
├── app.py
├── programs/
├── database/       # Local dev data
└── outputs/        # Local dev outputs

# On Server (production):
Desktop/
├── ZoolZ/          # Synced code (clean, no data)
└── ZoolZData/      # ALL server data (not synced)
    ├── database/
    ├── uploads/
    ├── outputs/
    ├── ModelingSaves/
    ├── logs/
    ├── temp/
    └── program-data/
```

**Usage:**
```python
from ZoolZmstr import get_data_paths, setup_server_folders

# Get paths (automatically uses right location)
paths = get_data_paths()
print(paths['database'])   # Laptop: ./database  |  Server: ~/Desktop/ZoolZData/database

# First run on server - creates folder structure
if is_server():
    setup_server_folders(verbose=True)
```

**Functions:**
- `get_data_paths()` - Returns dict of all folder paths
- `setup_server_folders()` - Creates ZoolZData structure
- `migrate_existing_data()` - Move old data to new structure
- `ensure_folders_exist()` - Make sure everything's ready
- `get_status()` - Check current state

---

### 3. Process Manager (`process_manager.py`)

**Purpose:** Smart resource management

**The Problem:**
- Modeling needs Redis + Celery for background tasks
- PeopleFinder might need Redis for caching
- Don't want Redis/Celery running when just on hub
- Future: 65+ programs, each with unique dependencies

**The Solution:**
Zoolz tracks what each program needs and boots/shuts down processes intelligently.

**How it works:**

1. **Program requirements defined:**
```python
# In process_manager.py
modeling = ProgramRequirements('Modeling')
modeling.require(
    'redis',
    start_cmd='redis-server --daemonize yes --port 6379',
    stop_cmd='redis-cli shutdown'
).require(
    'celery',
    start_cmd='celery -A tasks.celery worker --loglevel=info --detach',
    stop_cmd='pkill -f "celery.*worker"'
)
```

2. **User opens Modeling:**
```python
# app.py automatically calls:
process_manager.program_accessed('Modeling')
# → Starts Redis + Celery
```

3. **User closes Modeling:**
```python
process_manager.program_closed('Modeling')
# → Stops Redis + Celery (if no other program needs them)
```

**Key Features:**
- ✅ Only run what's needed, when it's needed
- ✅ Share processes (if 2 programs need Redis, start once)
- ✅ Clean shutdown (stops all processes on exit)
- ✅ Process tracking (knows what's running, PIDs, uptime)
- ✅ Easy to add requirements for new programs

**Usage:**
```python
from ZoolZmstr import process_manager, ProgramRequirements

# Define a new program's needs
my_program = ProgramRequirements('MyNewProgram')
my_program.require('redis', start_cmd='redis-server ...')
my_program.require('postgres', start_cmd='pg_ctl start ...')
process_manager.register_program(my_program)

# Zoolz handles the rest automatically
```

**Status check:**
```python
status = process_manager.get_status()
print(status['active_programs'])    # Which programs are open
print(status['running_processes'])  # What's running (PID, uptime)
```

---

### 4. Launcher (`launcher.py`)

**Purpose:** Program coordination (future expansion)

**Current state:** Placeholder for future features

**Future plans:**
- Launch programs as separate processes (not just Flask blueprints)
- Inter-process communication
- Health monitoring and auto-restart
- Load balancing for 65+ programs

Right now, all programs run as Flask blueprints in one process. As Zoolz grows, might need true process isolation.

---

## Integration with Zoolz

### In `config.py`:
```python
from ZoolZmstr import get_data_paths

# Get environment-aware paths
_data_paths = get_data_paths()

UPLOAD_FOLDER = str(_data_paths['uploads'])
OUTPUT_FOLDER = str(_data_paths['outputs'])
DATABASE_FOLDER = str(_data_paths['database'])
```

### In `app.py`:
```python
from ZoolZmstr import (
    is_server,
    setup_server_folders,
    process_manager
)

# Initialize server if needed
if is_server():
    setup_server_folders()

# Cleanup on exit
atexit.register(process_manager.cleanup_all)

# Smart process management
@app.before_request
def manage_program_processes():
    if request.path.startswith('/modeling'):
        process_manager.program_accessed('Modeling')
    # ... etc
```

---

## Server Setup Checklist

When deploying to Mac server for the first time:

### 1. Create server marker
```bash
touch ~/Desktop/SERVER
```

### 2. Sync code with rsync
```bash
# From laptop:
rsync -av ~/Desktop/ZoolZ/ server:~/Desktop/ZoolZ/ \
    --exclude 'database/' \
    --exclude 'outputs/' \
    --exclude 'ModelingSaves/' \
    --exclude 'venv/' \
    --exclude '__pycache__/'
```

### 3. First run
```bash
# On server:
cd ~/Desktop/ZoolZ
python3 app.py
```

Zoolz will automatically:
- Detect it's on the server
- Create `~/Desktop/ZoolZData/` structure
- Use server folders for all data

### 4. Port forwarding (when ready)
- Forward port 5001 to make Zoolz accessible externally
- Update Flask host to `0.0.0.0` (already done)

---

## Adding New Programs

When adding one of the 65+ programs:

### 1. Create the program
```
programs/
└── YourNewProgram/
    ├── blueprint.py
    ├── templates/
    ├── static/
    └── utils/
```

### 2. Define requirements (if needed)
```python
# In ZoolZmstr/process_manager.py

new_program = ProgramRequirements('YourNewProgram')
new_program.require(
    'redis',
    start_cmd='redis-server --daemonize yes',
    stop_cmd='redis-cli shutdown'
)
# Add to _register_default_requirements()
```

### 3. Register in app.py
```python
from programs.YourNewProgram.blueprint import your_bp
app.register_blueprint(your_bp, url_prefix='/yourprogram')

# Add to _program_url_map
_program_url_map['/yourprogram'] = 'YourNewProgram'
```

Done! Zoolz handles the rest.

---

## Diagnostics

### Check environment detection:
```bash
python3 -m ZoolZmstr.detection
```

Output:
```json
{
  "environment": "laptop",
  "is_server": false,
  "marker_exists": false,
  "marker_path": "/Users/isaiahmiro/Desktop/SERVER",
  "instructions": "To set up server mode:\nCreate marker: touch ~/Desktop/SERVER"
}
```

### Check folder status:
```bash
python3 -m ZoolZmstr.folder_manager
```

Output shows:
- Current environment
- Data root location
- All folder paths
- File counts

### Check process status:
```bash
python3 -m ZoolZmstr.process_manager
```

Shows:
- Registered programs
- Process requirements
- What's currently running

---

## Why "ZoolZmstr"?

- **Zoolz** - The product name
- **mstr** - Master (control logic)
- Separates Zoolz's own brain from the programs it manages
- Compartmentalized - easy to find, update, and expand

---

## Future Enhancements

### Multi-user support
- Track which user is using which program
- Per-user process isolation
- Resource allocation and limits

### AI Integration
- ML models as managed processes
- GPU allocation for AI helpers
- Smart resource scheduling

### Monitoring & Logging
- Process health checks
- Performance metrics
- Centralized logging for all programs

### Cloud Ready
- Environment detection beyond server/laptop
- Cloud storage integration
- Distributed process management

---

## Troubleshooting

### "Not detected as server" on Mac server
- Check marker file exists: `ls -la ~/Desktop/SERVER`
- Verify path is exact (case-sensitive)

### "Failed to start process"
- Check process is installed (e.g., `redis-server --version`)
- Check permissions
- View logs for details

### Folders not created
- Run `python3 -m ZoolZmstr.folder_manager` to diagnose
- Check disk permissions
- Verify server detection working

### Process not stopping
- Check PID in process manager status
- Manually kill: `kill <PID>`
- Restart Zoolz to clean up

---

## Documentation

Each module has detailed docstrings. To view:

```python
from ZoolZmstr import is_server, process_manager

help(is_server)
help(process_manager.program_accessed)
```

---

**Built for scalability. Ready for 65+ programs and beyond.**
