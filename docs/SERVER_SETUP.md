# Server Setup Guide

## Step 1: Transfer Files to Mac Server

**Option A: AirDrop (easier for first time)**
1. Select the entire `ZoolZ` folder on your laptop
2. AirDrop it to your Mac server
3. Move it to `Desktop/ZoolZ`

**Option B: rsync (for future updates)**
```bash
# From laptop:
rsync -av ~/Desktop/ZoolZ/ server:~/Desktop/ZoolZ/ \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '.git/'
```

---

## Step 2: Run Setup Script

**On the Mac server:**

```bash
cd ~/Desktop/ZoolZ
chmod +x setup_server.sh
./setup_server.sh
```

**What this does automatically:**
- ✅ Creates server marker file (`~/Desktop/Zoolzmstr/.IM_THE_SERVER`)
- ✅ Checks Python version (needs 3.7+)
- ✅ Creates virtual environment
- ✅ Installs ALL requirements (psutil, spacy, trimesh, etc.)
- ✅ Downloads spaCy language model (560MB)
- ✅ Checks if Redis is installed
- ✅ Tests that ZoolZmstr works
- ✅ Tests that config works

**If it asks about Redis:**
- Redis is needed for Modeling program background tasks
- Install with: `brew install redis`
- Or continue without it (Modeling will just run synchronously)

---

## Step 3: Start Zoolz

```bash
./start_zoolz.sh
```

**You should see:**
```
🖥️  ZOOLZ RUNNING ON SERVER
============================================================
🏗️  Setting up ZoolZData folder structure...
  ✓ Created: /Users/isaiahmiro/Desktop/ZoolZData/database
  ✓ Created: /Users/isaiahmiro/Desktop/ZoolZData/uploads
  ✓ Created: /Users/isaiahmiro/Desktop/ZoolZData/outputs
  ✓ Created: /Users/isaiahmiro/Desktop/ZoolZData/ModelingSaves
  ✓ Created: /Users/isaiahmiro/Desktop/ZoolZData/logs
  ✓ Created: /Users/isaiahmiro/Desktop/ZoolZData/temp
  ✓ Created: /Users/isaiahmiro/Desktop/ZoolZData/cache
✅ Server folders ready!

📍 Environment: server
📂 Data root: /Users/isaiahmiro/Desktop/ZoolZData/database

🌐 Starting Flask web server...
   🎨 ZoolZ Studio
   URL: http://localhost:5001
```

---

## Step 4: Test Locally

Open browser on the Mac server:
```
http://localhost:5001
```

Login:
- Username: `Zay`
- Password: `442767`

---

## Step 5: Port Forward (when ready)

**On your router:**
1. Find Mac server's local IP (System Preferences → Network)
2. Forward port `5001` → Mac server's IP
3. Allow port 5001 in Mac firewall (System Preferences → Security → Firewall)

**Test externally:**
```
http://your-public-ip:5001
```

Get your public IP from: https://whatismyip.com

---

## Requirements Summary

**Everything you need is in requirements.txt:**
- ✅ Flask (web framework)
- ✅ psutil (process management - NEW!)
- ✅ trimesh (3D modeling)
- ✅ opencv-python (image processing)
- ✅ spacy (AI/ML for PeopleFinder)
- ✅ celery + redis (background tasks)
- ✅ And 40+ more packages

**The setup script installs ALL of them automatically.**

---

## What psutil Does

`psutil` is a Python library that lets ZoolZmstr:
- Track running processes (Redis, Celery, etc.)
- Get process PIDs (process IDs)
- Start/stop processes intelligently
- Check if a process is running
- Monitor resource usage

**Example:**
```python
# ZoolZmstr uses psutil to track Redis:
process = psutil.Process(redis_pid)
if process.is_running():
    print("Redis is running!")
```

It's lightweight and required for the smart process management you wanted.

---

## Troubleshooting

### "Python version too old"
- Catalina 10.15.7 should have Python 3.7+
- Check with: `python3 --version`
- If too old, install from python.org

### "pip install failed"
```bash
# Try upgrading pip first:
pip install --upgrade pip setuptools wheel

# Then try again:
pip install -r requirements.txt
```

### "spaCy model download failed"
```bash
# Try manual download:
python3 -m spacy download en_core_web_lg --user
```

### "Redis not found"
```bash
# Install with Homebrew:
brew install redis

# Or skip it - Modeling will work without background tasks
```

### "Permission denied"
```bash
chmod +x setup_server.sh
chmod +x start_zoolz.sh
```

---

## Files You Need to Transfer

**Minimum required:**
- Entire `ZoolZ` folder from laptop
- That's it! (includes code, templates, static files, everything)

**NOT needed:**
- `venv/` - Will be created fresh on server
- `__pycache__/` - Will regenerate
- `.git/` - Don't need version history on server
- Old data folders - Server creates fresh ones

---

## After First Setup

For future updates, just rsync the code:
```bash
# From laptop:
rsync -av ~/Desktop/ZoolZ/ server:~/Desktop/ZoolZ/ \
    --exclude 'venv/' \
    --exclude 'ZoolZData/' \
    --exclude '__pycache__/'
```

Your data stays safe in `~/Desktop/ZoolZData/` (not synced).

---

## Quick Reference

**Start Zoolz:**
```bash
cd ~/Desktop/ZoolZ
./start_zoolz.sh
```

**Stop Zoolz:**
- Press `Ctrl+C`

**Check if running as server:**
```bash
python3 -c "from ZoolZmstr import is_server; print('Server:', is_server())"
```

**Check folder setup:**
```bash
ls -la ~/Desktop/ZoolZData/
```

---

**Ready to go! Just AirDrop the folder and run `./setup_server.sh`** 🚀
