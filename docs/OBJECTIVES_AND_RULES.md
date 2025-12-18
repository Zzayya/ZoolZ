# ZoolZ - Objectives and Rules

**Target Platform**: 2012 iMac, macOS Catalina 10.15.7, Python 3.12.12
**Deployment Location**: Mac server at `~/Desktop/ZoolZ/`
**Access Method**: Laptop connects to server via network (server IP: local network, external IP: 71.60.55.85)

---

## Core Principles

1. **Server is the ONLY deployment target** - Mac server runs ZoolZ 24/7, laptop is just for development
2. **No laptop execution** - Laptop syncs code to server, accesses via browser
3. **Hard-coded for Mac where needed** - Don't over-engineer cross-platform compatibility
4. **Everything must WORK** - No fake success messages, no partial functionality
5. **Single folder deployment** - Everything lives in `~/Desktop/ZoolZ/`, no scattered files

---

## Server Setup Script (`zoolz/server/setup_server_FINAL.sh`)

### Job Description:
Create a Python virtual environment on the Mac server that EXACTLY matches what's needed to run ZoolZ.

### Requirements:
1. **Python 3.12.12** - Exact version match
2. **Virtual environment** - `~/Desktop/ZoolZ/venv/` (isolated from system Python)
3. **Package installation** - Install ALL packages from `requirements.txt`
4. **Smart OpenCV handling** - Auto-detect which opencv-python version has wheels for this Mac
5. **Real verification** - Actually test imports, catch errors, NO FAKE SUCCESS MESSAGES
6. **Version checking** - Verify Python version, pip version, critical package versions
7. **Folder structure** - Create necessary folders (logs, uploads, etc.)
8. **Environment detection** - Check for `~/Desktop/SERVER` marker file

### What it does NOT do:
- Does NOT start the Flask server
- Does NOT auto-launch monitoring
- Does NOT modify code files

### Success criteria:
- Virtual environment exists at `~/Desktop/ZoolZ/venv/`
- All packages install without errors
- `python3 -c "from app import app"` succeeds (Flask can start)
- `python3 -c "import cv2"` succeeds (OpenCV works)
- `python3 -c "from zoolz.ZoolZmstr import is_server"` succeeds
- Celery and Redis are ready

### Output on success:
```
✅ Setup complete!

To start ZoolZ:
  cd ~/Desktop/ZoolZ
  source venv/bin/activate
  python3 app.py

To start monitoring:
  ./start_zoolz_multi_terminal.sh
```

---

## Flask Application (`app.py`)

### Job Description:
Web server that runs ZoolZ and serves all 4 program blueprints.

### Requirements:
1. **Bind to 0.0.0.0** - Accept connections from network (not just localhost)
2. **Port 5001** - Hard-coded, router forwards external 71.60.55.85:5001 to Mac
3. **Server detection** - Use `zoolz.ZoolZmstr.is_server()` to detect environment
4. **Blueprint registration** - Load all 4 programs (Modeling, PeopleFinder, ParametricCAD, DigitalFootprint)
5. **Static file serving** - Serve JS/CSS from both root and program folders
6. **Login system** - Username: Zay, Password: 442767
7. **Celery integration** - Background tasks for long-running operations

### Network setup:
- **Local access**: `http://192.168.1.x:5001` (Mac's local IP)
- **External access**: `http://71.60.55.85:5001` (router forwards to Mac)
- **Flask binding**: `0.0.0.0:5001` (accepts all connections)

### Success criteria:
- Flask starts without import errors
- Accessible from laptop browser via `http://71.60.55.85:5001`
- All 4 programs load correctly
- Celery tasks can be queued

---

## ZoolZmstr System (`zoolz/ZoolZmstr/`)

### Job Description:
Detect whether we're on the server or laptop, manage folders accordingly.

### Components:
1. **Server detection** - Check for `~/Desktop/SERVER` marker file
2. **Folder management** - Create necessary folders based on environment
3. **Process monitoring** - Track running services (Flask, Celery, Redis)
4. **Health checks** - Verify services are responding

### Folder structure on server:
```
~/Desktop/ZoolZ/                    # Main program folder
├── venv/                           # Python virtual environment
├── app.py                          # Flask application
├── tasks.py                        # Celery tasks
├── programs/                       # The 4 programs
│   ├── Modeling/
│   ├── PeopleFinder/
│   ├── ParametricCAD/
│   └── DigitalFootprint/
├── zoolz/                          # Core system
│   ├── ZoolZmstr/                  # Server detection & management
│   └── server/                     # Setup scripts
├── uploads/                        # User uploaded files
├── logs/                           # Application logs
└── static/                         # Global static files
```

### What about ZoolZData?
**Decision needed**: Do we need a separate `~/Desktop/ZoolZData/` folder, or keep everything in `~/Desktop/ZoolZ/`?

Current preference: Keep everything in `~/Desktop/ZoolZ/` for simplicity.

---

## OpenCV Version Strategy

### The Problem:
Different Mac architectures have different available opencv-python wheel versions. Compiling from source fails on Python 3.12.

### The Solution:
Setup script should:
1. Try to install the requested version (currently 4.6.0.66)
2. If it fails, query pip to find available versions
3. Install the highest available version with a wheel
4. Verify it actually works with `import cv2`

### Fallback strategy:
If NO opencv-python version works:
1. Try `opencv-python-headless` (smaller, no GUI components)
2. If that fails, ERROR and tell user to check architecture

### Why not replace OpenCV?
The cookie_cutter logic uses OpenCV extensively:
- Edge detection, contour finding, morphological operations, GrabCut algorithm
- Replacing would require rewriting 200+ lines of image processing code
- High risk of breaking cookie cutter functionality

---

## Modeling Program

### Job Description:
3D modeling tools - cookie cutter generator, stamp generator, parametric shapes, mesh operations.

### Critical dependencies:
- **OpenCV** - Image processing for cookie cutters
- **trimesh** - 3D mesh operations
- **numpy** - Array operations (must be <2.0 for compatibility)
- **shapely** - 2D polygon operations
- **pymeshlab** - Advanced mesh processing

### Features:
1. **Cookie Cutter Generator** - Upload image → 3D printable STL
2. **Stamp Generator** - Extract inner details for stamping
3. **Parametric Shapes** - Procedural 3D shapes
4. **Mesh Operations** - Hollow, thicken, boolean operations

### Success criteria:
- Can upload image and generate cookie cutter
- Preview shows 3D model correctly
- STL downloads and prints successfully on Ender 3 V2

---

## Multi-Terminal Monitoring (`start_zoolz_multi_terminal.sh`)

### Job Description:
Launch 4 separate Terminal windows to monitor different services.

### Terminal 1: Flask Server
- Shows Flask web server output
- Displays correct URLs (not localhost)
- Shows login credentials

### Terminal 2: Celery Worker
- Shows background task processing
- Displays task results

### Terminal 3: Redis Server
- Shows Redis message broker
- Displays connection info

### Terminal 4: System Stats
- Shows CPU, memory, disk usage
- Monitors service health

### Success criteria:
- All 4 terminals open automatically
- Each shows live output
- Services are actually running (not just fake output)

---

## Requirements File (`requirements.txt`)

### Job Description:
Define ALL Python packages needed to run ZoolZ with EXACT versions.

### Critical version locks:
- **numpy<2.0** - Required for opencv, trimesh, shapely compatibility
- **opencv-python** - Version must have wheel for Mac architecture
- **Flask==3.0.0** - Web framework
- **pymeshlab** - Must be version that exists (2023.12.post1, not post3)

### Package categories:
1. **Web framework**: Flask, Werkzeug, Jinja2
2. **Background tasks**: Celery, Redis
3. **3D processing**: trimesh, pymeshlab, shapely, rtree
4. **Image processing**: opencv-python, Pillow
5. **ML/AI**: spacy, transformers (for future features)
6. **Utilities**: python-dotenv, requests

---

## Future Integration Goals

### 3D Printer (Ender 3 V2)
- Connect to Mac server via USB or network
- Send G-code directly from Modeling program
- Create custom slicer application

### AI Orchestration (JEFF)
- Multi-AI system: LLM + Vision + ML + Randomizers
- Integrate with all 4 programs
- Server coordinates AI tasks

### TI-Nspire Calculator
- Explore using as computation brain
- Research connectivity options

---

## Deployment Checklist

### On Mac Server:
1. ✅ Python 3.12.12 installed
2. ✅ `~/Desktop/SERVER` marker file exists
3. ✅ Router forwards port 5001 to Mac
4. ✅ Mac has static local IP (or DHCP reservation)

### Setup Steps:
1. AirDrop ZoolZ folder to `~/Desktop/ZoolZ/`
2. Open Terminal on Mac
3. Run setup command:
   ```bash
   cd ~/Desktop/ZoolZ && touch ~/Desktop/SERVER && chmod +x zoolz/server/*.sh && ./zoolz/server/setup_server_FINAL.sh
   ```
4. Wait for setup to complete (all tests pass)
5. Start Flask:
   ```bash
   source venv/bin/activate && python3 app.py
   ```
6. Test from laptop: `http://71.60.55.85:5001`

### Success indicators:
- ✅ Setup script shows all green checkmarks
- ✅ Flask shows server IP (not localhost)
- ✅ Can access from laptop browser
- ✅ Can log in (Zay / 442767)
- ✅ Modeling program loads
- ✅ Can generate cookie cutter

---

## What NOT to Do

### ❌ Don't run program on laptop
- Laptop is for development only
- Use laptop to sync code to server
- Access via browser, don't run locally

### ❌ Don't auto-start services
- Setup script should NOT launch Flask
- User decides when to start services
- Just show the commands to run

### ❌ Don't fake success messages
- If import fails, REPORT IT
- Don't hide errors with grep -v
- Actually verify functionality

### ❌ Don't over-engineer
- Hard-code Mac-specific stuff if needed
- Don't add "future features" that aren't used
- Keep it simple and functional

### ❌ Don't install system-wide
- Use virtual environment
- Avoids permission issues on Catalina
- Easier to troubleshoot

---

## Troubleshooting

### Setup script fails on OpenCV:
1. Check which versions have wheels: `pip index versions opencv-python`
2. Manually install highest available: `pip install opencv-python==X.Y.Z`
3. Update `requirements.txt` to match

### Flask shows localhost instead of server IP:
1. Check `start_zoolz_multi_terminal.sh` for IP detection
2. Verify `ipconfig getifaddr en0` returns Mac's IP
3. Flask must bind to `0.0.0.0`, not `127.0.0.1`

### Can't access from laptop:
1. Check Mac firewall settings (allow port 5001)
2. Verify router port forwarding (external 5001 → Mac local IP 5001)
3. Confirm Flask is running: `ps aux | grep "python3 app.py"`

### Import errors on startup:
1. Activate venv: `source venv/bin/activate`
2. Test imports: `python3 -c "from app import app"`
3. Check logs for specific error
4. Reinstall failing package

---

## Summary

**Goal**: Get ZoolZ running 100% on Mac server, accessible from laptop browser, with all features working.

**Non-negotiable**:
- Must run on Mac server (not laptop)
- Must be accessible via network (external IP)
- Must have working cookie cutter generation
- No fake success messages
- Everything in one folder

**Priority**:
1. Get setup script working (installs everything correctly)
2. Get Flask starting (no import errors)
3. Get Modeling program working (cookie cutter generation)
4. Get monitoring working (multi-terminal view)
5. Future: 3D printer integration, AI orchestration
