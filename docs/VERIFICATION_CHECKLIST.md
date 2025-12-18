# ZoolZ Deployment Verification Checklist

## PRE-DEPLOYMENT (On Laptop - Before AirDrop)

### ✅ Verify Files Ready:
```bash
cd ~/Desktop/ZoolZ
ls -la
```

Should see:
- ✅ app.py
- ✅ tasks.py
- ✅ requirements.txt
- ✅ programs/ folder (with Modeling, PeopleFinder, ParametricCAD, DigitalFootprint)
- ✅ zoolz/ folder
- ✅ static/ folder
- ✅ templates/ folder
- ✅ .env.example
- ✅ AIR_DROP_NOW.txt
- ✅ OBJECTIVES_AND_RULES.md
- ✅ DEPLOYMENT_SUMMARY_DEC15.md
- ✅ start_zoolz_multi_terminal.sh

### ✅ Check Flask Configuration:
```bash
grep "app.run" app.py
```

Should show:
```
app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=port)
```

✅ **CORRECT** - `host='0.0.0.0'` means it accepts connections from network

---

## DEPLOYMENT (On Mac Server)

### Step 1: AirDrop Files
- [ ] AirDrop ZoolZ folder from laptop to Mac Desktop
- [ ] Verify folder landed at `~/Desktop/ZoolZ/` on Mac

### Step 2: Run Setup Script

**ON MAC TERMINAL:**
```bash
cd ~/Desktop/ZoolZ && touch ~/Desktop/SERVER && chmod +x zoolz/server/*.sh && ./zoolz/server/setup_server_FINAL.sh
```

**WHAT TO WATCH FOR:**
- [ ] ✅ Python 3.12 detected or installed
- [ ] ✅ Redis installed and started
- [ ] ✅ Virtual environment created at ~/Desktop/ZoolZ/venv/
- [ ] ✅ NumPy 1.x installed (NOT 2.x)
- [ ] ✅ OpenCV installed (watch for which version it chose!)
- [ ] ✅ trimesh, shapely installed
- [ ] ✅ Flask 3.0 installed
- [ ] ✅ All import tests pass
- [ ] ✅ Shape generation test passes (cube + sphere)
- [ ] ✅ app.py loads successfully
- [ ] ✅ .env file created

**IF IT SUCCEEDS, YOU'LL SEE:**
```
╔════════════════════════════════════════════════════════════╗
║              ✅ SETUP COMPLETE - SUCCESS! ✅               ║
╚════════════════════════════════════════════════════════════╝
```

**IF IT FAILS:**
- [ ] Read error message carefully
- [ ] Check setup.log file: `cat setup.log | tail -50`
- [ ] Try troubleshooting steps below

---

## POST-SETUP VERIFICATION (On Mac Server)

### Step 3: Verify Mac Network Info

**GET MAC'S LOCAL IP:**
```bash
ipconfig getifaddr en0
```
**Expected:** `10.0.0.11` (your Mac's local network IP)

**CHECK PORT 5001 NOT IN USE:**
```bash
lsof -i :5001
```
**Expected:** Empty output (nothing using port 5001 yet)

**VERIFY SERVER MARKER EXISTS:**
```bash
ls -la ~/Desktop/SERVER
```
**Expected:** File exists

### Step 4: Verify Python Environment

**ACTIVATE VENV:**
```bash
cd ~/Desktop/ZoolZ
source venv/bin/activate
```

**CHECK PYTHON VERSION:**
```bash
python3 --version
```
**Expected:** Python 3.12.x

**CHECK CRITICAL PACKAGES:**
```bash
python3 -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
python3 -c "import trimesh; print(f'trimesh: {trimesh.__version__}')"
python3 -c "import flask; print(f'Flask: {flask.__version__}')"
python3 -c "import numpy; print(f'NumPy: {numpy.__version__}')"
```

**Expected:**
- OpenCV: 4.x.x (any version that worked)
- trimesh: 4.0.5
- Flask: 3.0.0
- NumPy: 1.x.x (MUST be 1.x, NOT 2.x!)

**TEST ZOOLZMSTR:**
```bash
python3 -c "from zoolz.ZoolZmstr import is_server, get_environment; print(f'Environment: {get_environment()}'); print(f'Is server: {is_server()}')"
```

**Expected:**
```
Environment: server
Is server: True
```

**TEST APP.PY LOADS:**
```bash
python3 -c "from app import app; print('✅ Flask app loads successfully')"
```

**Expected:** `✅ Flask app loads successfully` (no errors)

**TEST MODELING SHAPE GENERATION:**
```bash
python3 -c "
from programs.Modeling.utils.shape_generators import generate_shape
result = generate_shape('cube', {'size': 10})
mesh = result['mesh']
print(f'✅ Cube: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces')
"
```

**Expected:** `✅ Cube: 8 vertices, 12 faces`

### Step 5: Verify Redis

**CHECK REDIS RUNNING:**
```bash
redis-cli ping
```
**Expected:** `PONG`

**IF NOT RUNNING:**
```bash
brew services start redis
```

---

## STARTING ZOOLZ (On Mac Server)

### Option 1: Flask Only (Simple)

```bash
cd ~/Desktop/ZoolZ
source venv/bin/activate
python3 app.py
```

**WHAT TO WATCH FOR IN OUTPUT:**
- [ ] ` * Running on http://0.0.0.0:5001` (confirms binding to all interfaces)
- [ ] `🖥️  ZOOLZ RUNNING ON SERVER` (confirms server mode)
- [ ] No import errors
- [ ] No "ModuleNotFoundError"

**LEAVE THIS TERMINAL OPEN** - Flask is running in foreground

### Option 2: Multi-Terminal Mode (Recommended)

```bash
cd ~/Desktop/ZoolZ
./start_zoolz_multi_terminal.sh
```

**WHAT TO WATCH FOR:**
- [ ] 4 Terminal windows open
- [ ] Terminal 1: Flask server output
- [ ] Terminal 2: Celery worker output
- [ ] Terminal 3: Redis monitor
- [ ] Terminal 4: System stats

---

## NETWORK ACCESS VERIFICATION (From Laptop)

### Step 6: Check Mac Firewall

**ON MAC:**
```
System Preferences → Security & Privacy → Firewall
```

- [ ] Firewall is ON
- [ ] Python is allowed to accept incoming connections

**IF PYTHON NOT LISTED:**
- Try connecting from laptop first, Mac will prompt to allow

### Step 7: Test Local Network Access

**ON LAPTOP, OPEN BROWSER:**

**Test 1: Local IP (same network)**
```
http://10.0.0.11:5001
```

- [ ] Login page loads
- [ ] Can login with Zay / 442767
- [ ] Hub shows 4 program bubbles

**Test 2: External IP (through router)**
```
http://71.60.55.85:5001
```

- [ ] Login page loads (same as local)
- [ ] Everything works identically

**IF IT DOESN'T LOAD:**
1. Check Flask is actually running on Mac (see Step 5)
2. Check Mac firewall allows Python (Step 6)
3. Check router port forwarding:
   - External port 5001 → 10.0.0.11 port 5001

---

## MODELING PROGRAM VERIFICATION (From Laptop Browser)

### Step 8: Test Cookie Cutter Generation

1. [ ] Access ZoolZ: `http://71.60.55.85:5001`
2. [ ] Login: Zay / 442767
3. [ ] Click "Modeling" bubble
4. [ ] Click "Cookie Cutter" tool
5. [ ] Upload test image (any PNG or JPG)
6. [ ] Click "Generate"
7. [ ] 3D preview appears
8. [ ] Can download STL file
9. [ ] STL file opens in slicer (Cura, PrusaSlicer, etc.)

**IF COOKIE CUTTER FAILS:**
- Check Flask terminal for error messages
- Check OpenCV is installed: `python3 -c "import cv2; print(cv2.__version__)"`

### Step 9: Test Shape Generators

1. [ ] In Modeling program, click "Shapes" tool
2. [ ] Select "Cube"
3. [ ] Set size to 10mm
4. [ ] Click "Generate"
5. [ ] 3D preview appears
6. [ ] Can download STL

**REPEAT FOR:**
- [ ] Sphere
- [ ] Cylinder
- [ ] Cone
- [ ] Torus

### Step 10: Test Boolean Operations

1. [ ] Generate a cube (10mm)
2. [ ] Generate a sphere (6mm)
3. [ ] Select both shapes
4. [ ] Click "Union" (combine)
5. [ ] New merged shape appears
6. [ ] Can download STL

---

## ZOOLZDATA FOLDER VERIFICATION (On Mac Server)

### Step 11: Check Folder Creation

**ON MAC, AFTER FLASK HAS STARTED:**
```bash
ls -la ~/Desktop/ZoolZData/
```

**Expected folders:**
- [ ] database/
- [ ] uploads/
- [ ] outputs/
- [ ] logs/
- [ ] temp/
- [ ] cache/

**IF FOLDER DOESN'T EXIST:**
```bash
python3 -c "from zoolz.ZoolZmstr import setup_server_folders; setup_server_folders(verbose=True)"
```

---

## TROUBLESHOOTING SCENARIOS

### Scenario 1: Setup Script Fails on OpenCV

**SYMPTOMS:**
```
ERROR: Could not find a version that satisfies the requirement opencv-python
```

**FIX:**
```bash
source venv/bin/activate

# Check what versions are available
pip index versions opencv-python

# Try installing highest available manually
pip install --only-binary=:all: opencv-python==4.6.0.66

# If that fails, try headless
pip install --only-binary=:all: opencv-python-headless

# Test it works
python3 -c "import cv2; print(cv2.__version__)"
```

### Scenario 2: Flask Shows ModuleNotFoundError

**SYMPTOMS:**
```
ModuleNotFoundError: No module named 'cv2'
```

**FIX:**
```bash
# Make sure you're in venv
source venv/bin/activate

# Check if opencv installed
pip list | grep opencv

# If not, install it
pip install --only-binary=:all: opencv-python-headless

# Test app.py loads
python3 -c "from app import app; print('OK')"
```

### Scenario 3: Can't Access from Laptop

**SYMPTOMS:**
- Browser shows "This site can't be reached"

**FIX:**
1. **Verify Flask is running on Mac:**
   ```bash
   ps aux | grep "python.*app.py"
   ```

2. **Check Mac's IP hasn't changed:**
   ```bash
   ipconfig getifaddr en0
   ```
   Should be `10.0.0.11`

3. **Test from Mac browser first:**
   Open Safari on Mac, go to `http://localhost:5001`
   - If this works, problem is network/firewall
   - If this doesn't work, problem is Flask

4. **Check Mac firewall:**
   ```
   System Preferences → Security & Privacy → Firewall → Firewall Options
   ```
   Add Python to allow incoming connections

5. **Check router port forwarding:**
   - Log into router admin (usually 192.168.1.1 or 10.0.0.1)
   - Verify: External port 5001 → 10.0.0.11:5001

### Scenario 4: Cookie Cutter Generation Fails

**SYMPTOMS:**
- Upload image, click generate, nothing happens or error

**FIX:**
1. **Check Flask terminal for error**

2. **Verify OpenCV works:**
   ```bash
   python3 -c "
   import cv2
   import numpy as np
   img = np.zeros((100, 100, 3), dtype=np.uint8)
   gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
   print('OpenCV OK')
   "
   ```

3. **Test cookie_logic imports:**
   ```bash
   python3 -c "from programs.Modeling.utils.cookie_logic import generate_cookie_cutter; print('OK')"
   ```

4. **Check Celery is running** (if using multi-terminal mode)

### Scenario 5: NumPy 2.x Installed (Everything Breaks)

**SYMPTOMS:**
```
AttributeError: module 'numpy' has no attribute 'X'
```

**FIX:**
```bash
source venv/bin/activate

# Check NumPy version
python3 -c "import numpy; print(numpy.__version__)"

# If 2.x, force reinstall 1.x
pip uninstall -y numpy
pip install "numpy>=1.24.0,<2.0"

# Reinstall packages that depend on NumPy
pip install --force-reinstall --no-cache-dir opencv-python trimesh shapely
```

---

## SUCCESS INDICATORS

### ✅ SETUP SUCCESSFUL IF:
1. Setup script shows "✅ SETUP COMPLETE - SUCCESS! ✅"
2. All import tests passed
3. Shape generation test passed
4. app.py loads without errors

### ✅ FLASK RUNNING SUCCESSFULLY IF:
1. Terminal shows `* Running on http://0.0.0.0:5001`
2. No ModuleNotFoundError messages
3. Shows "🖥️  ZOOLZ RUNNING ON SERVER"
4. ZoolZData folder created at ~/Desktop/ZoolZData/

### ✅ NETWORK ACCESS WORKING IF:
1. Can access from laptop: `http://71.60.55.85:5001`
2. Login page loads
3. Can login with Zay / 442767
4. Hub shows 4 program bubbles
5. Each program loads when clicked

### ✅ MODELING WORKING IF:
1. Cookie cutter: Upload image → generates 3D model → downloads STL
2. Shape generators: Cube, sphere, cylinder all generate
3. Boolean operations: Union combines shapes
4. Download STL files open in slicer software

---

## COMMANDS REFERENCE

### Start Flask (Simple):
```bash
cd ~/Desktop/ZoolZ
source venv/bin/activate
python3 app.py
```

### Start Multi-Terminal Mode:
```bash
cd ~/Desktop/ZoolZ
./start_zoolz_multi_terminal.sh
```

### Stop Flask:
- If running in foreground: Press `Ctrl+C`
- If running in background: `pkill -f "python.*app.py"`

### Stop Everything:
```bash
pkill -f "python.*app.py"
pkill -f celery
brew services stop redis
```

### Check What's Running:
```bash
ps aux | grep python
ps aux | grep celery
ps aux | grep redis
lsof -i :5001  # Check port 5001
```

### View Logs:
```bash
cat setup.log  # Setup script output
cat ~/Desktop/ZoolZData/logs/*.log  # Application logs
```

### Re-run Setup (Safe - Idempotent):
```bash
cd ~/Desktop/ZoolZ
./zoolz/server/setup_server_FINAL.sh
```

---

## FINAL CHECKLIST

### Before Deployment:
- [ ] All files on laptop at ~/Desktop/ZoolZ
- [ ] OBJECTIVES_AND_RULES.md exists
- [ ] DEPLOYMENT_SUMMARY_DEC15.md exists
- [ ] AIR_DROP_NOW.txt updated
- [ ] requirements.txt has flexible OpenCV (>=4.5.0)
- [ ] setup_server_FINAL.sh has smart OpenCV installer

### During Setup (On Mac):
- [ ] Python 3.12 installed
- [ ] Redis installed and running
- [ ] Virtual environment created
- [ ] ALL packages installed (especially OpenCV!)
- [ ] All import tests pass
- [ ] Shape generation test passes
- [ ] app.py loads successfully
- [ ] .env file created

### After Setup (On Mac):
- [ ] Flask starts without errors
- [ ] Terminal shows "Running on http://0.0.0.0:5001"
- [ ] ZoolZData folder created
- [ ] Can access from Mac browser: http://localhost:5001

### Network Access (From Laptop):
- [ ] Can access: http://71.60.55.85:5001
- [ ] Login works (Zay / 442767)
- [ ] Hub loads with 4 bubbles
- [ ] Modeling program loads

### Modeling Tests (From Laptop Browser):
- [ ] Cookie cutter: Upload image → generates STL
- [ ] Cube generates and downloads
- [ ] Sphere generates and downloads
- [ ] Boolean union works

### ✅ DEPLOYMENT COMPLETE!

If all checkboxes checked, ZoolZ is **100% OPERATIONAL** on your Mac server! 🚀
