# ZoolZ Setup Guide - Fresh Installation

Complete guide for setting up ZoolZ on a brand new computer.

## 📋 Prerequisites

- **Python 3.10+** (3.12 recommended)
- **pip** (comes with Python)
- **Git** (optional, for cloning)

## 🚀 Fresh Installation Steps

### Step 1: Get the Code

```bash
# If using git
git clone <your-repo-url> ZoolZ
cd ZoolZ

# OR just download and extract the ZIP
cd ZoolZ
```

### Step 2: Create Virtual Environment

```bash
# Mac/Linux
python3 -m venv venv

# Windows
python -m venv venv
```

This creates an isolated Python environment in the `venv/` folder.

### Step 3: Activate Virtual Environment

**Mac/Linux:**
```bash
source venv/bin/activate
```

**Windows Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

**Windows PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install ALL Dependencies

```bash
pip install -r requirements.txt
```

This single command installs everything:
- Flask (web framework)
- OpenCV, Pillow (image processing)
- Trimesh, Shapely (3D mesh operations)
- PyMeshLab (mesh repair)
- aiohttp, BeautifulSoup (People Finder)
- NumPy, SciPy (math operations)
- All other dependencies

**Installation takes 2-5 minutes depending on your internet speed.**

### Step 5: Verify Installation

```bash
python -c "import flask, trimesh, cv2, shapely; print('✓ All core dependencies installed successfully!')"
```

### Step 6: Run the App

```bash
python app.py
```

**Or use the launcher scripts:**

```bash
# Mac/Linux
./scripts/START_ZOOLZ.command

# Windows
scripts\START_ZOOLZ.bat
```

The app will open at: **http://localhost:5001**

---

## 🔧 Troubleshooting

### Issue: `python3: command not found`

**Solution:** Install Python from https://python.org

### Issue: `pip: command not found`

**Solution:**
```bash
# Mac/Linux
python3 -m ensurepip --upgrade

# Windows
python -m ensurepip --upgrade
```

### Issue: Permission denied on Mac/Linux launcher

**Solution:**
```bash
chmod +x scripts/START_ZOOLZ.command
```

### Issue: Windows script execution policy error

**Solution:** Run PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: `ModuleNotFoundError` after installation

**Solution:** Make sure venv is activated (you should see `(venv)` in prompt)

### Issue: NumPy/OpenCV install fails on Mac M1/M2

**Solution:**
```bash
# Install Rosetta (if needed)
softwareupdate --install-rosetta

# Or use conda instead
conda create -n zoolz python=3.12
conda activate zoolz
pip install -r requirements.txt
```

---

## 🔄 Updating Dependencies

When requirements.txt changes:

```bash
# Activate venv first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Update all packages
pip install --upgrade -r requirements.txt
```

---

## 🧹 Clean Reinstall

If something breaks:

```bash
# 1. Deactivate venv
deactivate

# 2. Delete venv
rm -rf venv  # Mac/Linux
# rmdir /s venv  # Windows

# 3. Start fresh from Step 2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📦 What Gets Installed

### Core (Required)
- **Flask 3.0.0** - Web framework
- **Werkzeug 3.0.0** - WSGI utilities
- **NumPy 1.26.0** - Numerical computing
- **Trimesh 4.0.5** - 3D mesh processing
- **Shapely 2.0.2** - Geometric operations

### Cookie Cutter Mode
- **OpenCV 4.8.1** - Image processing
- **Pillow 10.1.0** - Image loading
- **PyMeshLab 2023.12** - Mesh repair
- **pyclipper 1.3.0** - 2D clipping
- **mapbox-earcut** - Polygon triangulation

### People Finder
- **aiohttp 3.9.1** - Async HTTP client
- **BeautifulSoup4 4.12.2** - HTML parsing
- **lxml 4.9.3** - XML/HTML parser
- **requests 2.32.2+** - HTTP requests
- **python-Levenshtein 0.23.0** - Fuzzy matching

### Math & Science
- **SciPy 1.11.4** - Scientific computing

**Total Size:** ~800MB (mostly NumPy, SciPy, OpenCV)

---

## 🎯 Quick Commands Reference

```bash
# Fresh setup
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt

# Run app
python app.py

# Run tests
python scripts/test_all_images.py

# Deactivate venv when done
deactivate
```

---

## 💡 Tips

1. **Always activate venv first** before running any commands
2. **Use the launcher scripts** for easiest startup
3. **Don't commit venv/** - it's in .gitignore
4. **Different computers = different venvs** - never copy venv between machines
5. **Port 5001** - if busy, edit `app.py` line 47

---

## 🔑 Optional: API Keys for People Finder

People Finder works without API keys, but enhanced with:

**Google Custom Search:**
```bash
export GOOGLE_API_KEY="your_key"
export GOOGLE_SEARCH_ENGINE_ID="your_cse_id"
```

**NumVerify Phone API:**
```bash
export NUMVERIFY_API_KEY="your_key"
```

Or use the **"G" button** in People Finder UI to set keys in browser.

---

**Need help?** Check [CLAUDE.md](CLAUDE.md) for full documentation.
