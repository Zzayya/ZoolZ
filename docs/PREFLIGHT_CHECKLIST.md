# Pre-Flight Checklist ✈️

Before you AirDrop and launch, here's what's ready to go:

## ✅ Files Ready for ANY Mac Username

- [x] **detection.py** - Uses `Path.home()` (works for any user)
- [x] **folder_manager.py** - Uses `Path.home()` (works for any user)
- [x] **setup_server.sh** - Uses `$HOME` variable (works for any user)
- [x] All paths are dynamic - will work on iMac with different username

## ✅ Port Configuration

- [x] **Flask running on port 5001** (app.py line 332)
- [x] **Host: 0.0.0.0** (accepts external connections)
- [x] Ready for port forwarding

## ✅ Server Auto-Setup

When you run `./setup_server.sh` on the iMac, it will:

1. **Create marker file** → `~/Desktop/Zoolzmstr/.IM_THE_SERVER`
2. **Check Python** → Needs 3.7+ (you have this)
3. **Create venv** → Fresh virtual environment
4. **Install requirements** → All packages (opencv 4.6.0.66 for Catalina)
5. **Download spaCy model** → en_core_web_lg
6. **Test ZoolZmstr** → Verify server detection works
7. **Test config** → Verify paths work

## ✅ ZoolZmstr Logic

When you first run `./start_zoolz.sh`, Zoolz will:

1. **Detect it's on server** (checks for marker file)
2. **Create ZoolZData folders:**
   ```
   ~/Desktop/ZoolZData/
   ├── database/
   ├── uploads/
   ├── outputs/
   ├── ModelingSaves/
   ├── logs/
   ├── temp/
   └── cache/
   ```
3. **Smart process management:**
   - Hub only → Just Flask running
   - Open Modeling → Boots Redis + Celery
   - Close Modeling → Stops Redis + Celery

## ✅ Catalina Compatibility

- [x] **opencv-python** → Downgraded to 4.6.0.66 (Catalina-safe)
- [x] **numpy/scipy** → Trying current versions first
- [x] **All other packages** → Catalina-compatible
- [x] **Python 3.9** → You already have this

## ✅ Everything Self-Contained

The ZoolZ folder includes:
- ✅ All code
- ✅ All templates/static files
- ✅ requirements.txt (Catalina-ready)
- ✅ setup_server.sh (auto-installs everything)
- ✅ start_zoolz.sh (launches Zoolz)
- ✅ ZoolZmstr/ (server brain logic)

**You DON'T need to transfer separately:**
- ❌ venv/ (will be created fresh)
- ❌ database/ (will be created in ZoolZData)
- ❌ \_\_pycache\_\_/ (will regenerate)

## 🚀 Launch Sequence (On iMac)

```bash
# 1. Open Terminal, go to folder
cd ~/Desktop/ZoolZ

# 2. Run setup (ONCE)
./setup_server.sh

# 3. Start Zoolz
./start_zoolz.sh
```

**You should see:**
```
🖥️  ZOOLZ RUNNING ON SERVER
============================================================
🏗️  Setting up ZoolZData folder structure...
  ✓ Created: /Users/[your-imac-username]/Desktop/ZoolZData/database
  ✓ Created: /Users/[your-imac-username]/Desktop/ZoolZData/uploads
  ...
✅ Server folders ready!

📍 Environment: server
📂 Data root: /Users/[your-imac-username]/Desktop/ZoolZData/database

🌐 Starting Flask web server...
   URL: http://localhost:5001
```

## 🌐 Access from Laptop

**After port forwarding:**
```
http://your-public-ip:5001
```

**Login:**
- Username: `Zay`
- Password: `442767`

## 🔧 If Something Goes Wrong

**Python too old:**
```bash
python3 --version  # Check version
# Install Python 3.9 from python.org if needed
```

**Permission denied:**
```bash
chmod +x setup_server.sh
chmod +x start_zoolz.sh
```

**Package install fails:**
```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel
# Try again
pip install -r requirements.txt
```

**Can't find detection:**
```bash
# Check marker exists
ls -la ~/Desktop/Zoolzmstr/.IM_THE_SERVER
# Should show the file
```

## 📊 What Gets Created

**On your iMac Desktop:**
```
Desktop/
├── ZoolZ/              ← AirDropped code (stays clean)
├── Zoolzmstr/          ← Created by setup script
│   └── .IM_THE_SERVER  ← Server marker file
└── ZoolZData/          ← Created on first run
    ├── database/       ← All databases
    ├── uploads/        ← User uploads
    ├── outputs/        ← Generated files
    ├── ModelingSaves/  ← Customer orders
    ├── logs/           ← Server logs
    ├── temp/           ← Temp files
    └── cache/          ← Cache data
```

## 🎯 Final Checks Before AirDrop

- [ ] Port forwarding done (5001 → iMac)
- [ ] iMac has Python 3.7+ installed
- [ ] Ready to AirDrop entire ZoolZ folder
- [ ] Have Terminal open on iMac

---

**YOU'RE READY TO GO! 🚀**

Everything is username-agnostic, auto-detecting, and self-configuring.

Just AirDrop → Run setup → Start Zoolz → Done!
