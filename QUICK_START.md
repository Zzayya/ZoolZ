# ZoolZ Quick Start Guide

## 🚀 First Time Setup

### 1. Install/Update All Requirements

```bash
# Option A: Use the automated script (RECOMMENDED)
./install_requirements.sh

# Option B: Manual install/update
source venv/bin/activate  # or: source .venv/bin/activate
pip install --upgrade -r requirements.txt
python -m spacy download en_core_web_lg
```

**The script will:**
- Create venv if needed
- Upgrade pip/setuptools
- Install OR update ALL packages
- Download AI models
- Verify everything works

### 2. Start Redis (for background tasks)

```bash
redis-server
```

### 3. Start Celery Worker (in new terminal)

```bash
source venv/bin/activate
celery -A tasks worker --loglevel=info
```

### 4. Start ZoolZ

```bash
source venv/bin/activate
python app.py
```

### 5. Login

```
URL: http://localhost:5001
Username: Zay
Password: 442767
```

---

## 📦 Requirements Management

### Install/Update Everything

```bash
# This installs NEW packages AND upgrades existing ones
pip install --upgrade -r requirements.txt
```

### Add New Package

```bash
pip install package-name
pip freeze > requirements.txt  # Update requirements file
```

### Check What's Installed

```bash
pip list
```

---

## 🛠️ Your Programs

| Program | URL | Description |
|---------|-----|-------------|
| **Hub** | http://localhost:5001/hub | Main navigation |
| **Modeling** | http://localhost:5001/modeling | Cookie cutters, STL editing |
| **Parametric CAD** | http://localhost:5001/parametric | Programmatic 3D modeling |
| **People Finder** | http://localhost:5001/people_finder | Background checks |
| **Digital Footprint** | http://localhost:5001/footprint | Online presence analysis |

---

## 🎮 Your Login Details

**Username:** Zay  
**User Number:** #100001 (Player 1!)  
**Password:** 442767  
**Email:** Isaiahjmiro@gmail.com  
**Role:** Admin (full control)

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5001
lsof -ti:5001 | xargs kill -9
```

### Redis Not Running
```bash
# Start Redis
redis-server

# Or install if needed:
brew install redis  # macOS
```

### Celery Issues
```bash
# Restart Celery worker
pkill -9 celery
celery -A tasks worker --loglevel=info
```

### venv Not Activating
```bash
# Recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
./install_requirements.sh
```

---

## 📝 Notes

- **Background tasks** require Redis + Celery
- **Email system** ready (activates on server deployment)
- **ML models** download on first run (~1.5GB total)
- **Modeling** program is production-ready for Etsy!

---

*Built by Isaiah "Zay" Miro | December 2025*
