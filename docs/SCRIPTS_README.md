# ZoolZ Scripts Guide

## Main Folder Scripts (~/Desktop/ZoolZ/)

### `start_zoolz.sh`
**Purpose:** Start Flask server in simple mode (one terminal)
**When to use:** Quick testing, simple deployment
**How to use:**
```bash
./start_zoolz.sh
```

### `start_zoolz_multi_terminal.sh`
**Purpose:** Start Flask with 4 separate Terminal windows for monitoring
**When to use:** Production deployment, when you want live output from Flask, Celery, Redis, and system stats
**How to use:**
```bash
./start_zoolz_multi_terminal.sh
```
**Opens:**
- Terminal 1: Flask server (live output)
- Terminal 2: Celery worker (background tasks)
- Terminal 3: Redis monitor (message broker)
- Terminal 4: System stats (CPU, RAM, disk)

---

## Server Scripts (~/Desktop/ZoolZ/zoolz/server/)

### `setup_server_FINAL.sh` ⭐ MAIN SCRIPT
**Purpose:** Complete Mac server setup - installs everything, creates venv, tests all packages
**When to use:** First time deploying to Mac server, or after major updates
**How to use:**
```bash
cd ~/Desktop/ZoolZ
touch ~/Desktop/SERVER
chmod +x zoolz/server/*.sh
./zoolz/server/setup_server_FINAL.sh
```
**What it does:**
- Installs Python 3.12 (if needed)
- Installs Redis via Homebrew
- Creates virtual environment at ~/Desktop/ZoolZ/venv/
- Installs ALL packages (smart OpenCV installer!)
- Tests all imports and functionality
- Creates .env file with production settings
- Shows network configuration
- Tests cookie cutter pipeline

### `health_check.sh`
**Purpose:** Check if ZoolZ server is running correctly
**When to use:** Troubleshooting, monitoring
**How to use:**
```bash
./zoolz/server/health_check.sh
```
**Checks:**
- Flask running?
- Celery running?
- Redis running?
- All imports working?
- Disk space available?

### `backup_models.sh`
**Purpose:** Backup saved models and user data
**When to use:** Before major updates, periodic backups
**How to use:**
```bash
./zoolz/server/backup_models.sh
```

---

## Archived Scripts (Not Used)

### `scripts/archive/`
- `run_dev.sh` - Old duplicate of start_zoolz.sh
- `verify_before_deploy.sh` - Replaced by better verification in setup_server_FINAL.sh
- `zoolz_push.sh` - Not used (using AirDrop instead)

### `zoolz/server/archive/`
- `setup_server.sh` - Old version (superseded by setup_server_FINAL.sh)
- `setup_server_v2.sh` - Old version
- `install_requirements.sh` - Incorporated into setup_server_FINAL.sh
- `sync_to_server.sh` - Not needed (using AirDrop)
- `manage_server.sh` - Not actively used
- `monitor_server.sh` - Not actively used
- `show_server_dashboard.sh` - Not actively used

---

## Quick Reference

### First Time Setup on Mac Server:
```bash
cd ~/Desktop/ZoolZ && touch ~/Desktop/SERVER && chmod +x zoolz/server/*.sh && ./zoolz/server/setup_server_FINAL.sh
```

### Start Flask (Simple):
```bash
./start_zoolz.sh
```

### Start Flask (Multi-Terminal):
```bash
./start_zoolz_multi_terminal.sh
```

### Check Health:
```bash
./zoolz/server/health_check.sh
```

### Stop Everything:
```bash
pkill -f "python.*app.py"
pkill -f celery
brew services stop redis
```

---

## Why This Organization?

**Main folder scripts** = User-facing commands you run regularly
- Starting Flask
- Launching multi-terminal mode

**zoolz/server/ scripts** = Server administration/setup
- Initial setup (run once)
- Health monitoring
- Backups

**Archived scripts** = Old versions kept for reference
- Don't use these
- Can be deleted if you want
