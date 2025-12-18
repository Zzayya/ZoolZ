# ZoolZ Mac Server Setup Guide

Quick setup for Mac Server (Catalina 10.15.7)

## Prerequisites

Your Mac needs:
- Homebrew installed
- Internet connection for first setup

## Step 1: Create Server Marker

Before anything else, create the server marker file:

```bash
touch ~/Desktop/SERVER
```

This tells ZoolZ it's running on the server (not laptop).

## Step 2: Run Setup Script

```bash
cd ~/Desktop/ZoolZ
chmod +x zoolz/server/setup_server_FINAL.sh
./zoolz/server/setup_server_FINAL.sh
```

The setup script will:
- Install Python 3.12 via Homebrew (if needed)
- Install Redis (for background tasks)
- Create virtual environment
- Install all Python packages
- Test all imports
- Create .env file

## Step 3: Start ZoolZ

```bash
./start_zoolz.sh
```

Or for multi-terminal monitoring:
```bash
./scripts/start_zoolz_multi_terminal.sh
```

## Access

- **Local:** http://localhost:5001
- **Network:** http://YOUR_MAC_IP:5001
- **Login:** Zay / 442767

## Folder Structure After Setup

```
~/Desktop/
├── SERVER                  <- Marker file you created
├── ZoolZ/                  <- Program code (AirDropped)
│   ├── venv/              <- Created by setup script
│   └── ...
└── ZoolZData/             <- Created automatically on first run
    ├── database/
    ├── uploads/
    ├── outputs/
    └── logs/
```

## Stopping ZoolZ

Press `Ctrl+C` in the terminal, or:

```bash
pkill -f 'python.*app.py'
pkill -f celery
brew services stop redis
```

## Troubleshooting

### Port 5001 in use
```bash
lsof -i :5001
kill -9 <PID>
```

### Redis not running
```bash
brew services start redis
```

### Check server status
```bash
./zoolz/server/health_check.sh
```
