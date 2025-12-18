#!/bin/bash
# ZoolZ Sync Script - Push updates from laptop to Mac server
# Run this from your LAPTOP after making changes

# ============================================================================
# CONFIGURATION
# ============================================================================

# Your Mac server's LOCAL IP (on your home network)
SERVER_IP="10.0.0.11"

# Your Mac server's username (run 'whoami' on Mac to check)
SERVER_USER="isaiahmiro"

# Path on server where ZoolZ lives
SERVER_PATH="~/Desktop/ZoolZ"

# ============================================================================
# SCRIPT
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           ZOOLZ SYNC - LAPTOP → SERVER                     ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}From:${NC} $PROJECT_ROOT"
echo -e "${YELLOW}To:${NC}   $SERVER_USER@$SERVER_IP:$SERVER_PATH"
echo ""

# Test connection
echo "Testing connection..."
if ! ping -c 1 -W 2 "$SERVER_IP" &> /dev/null; then
    echo -e "${RED}✗ Cannot reach $SERVER_IP${NC}"
    echo ""
    echo "Make sure:"
    echo "  1. Mac server is ON and connected to WiFi"
    echo "  2. You're on the SAME network"
    echo "  3. IP is correct (on Mac run: ipconfig getifaddr en0)"
    exit 1
fi
echo -e "${GREEN}✓ Server reachable${NC}"

# Test SSH
echo "Testing SSH..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$SERVER_USER@$SERVER_IP" "echo ok" &> /dev/null; then
    echo -e "${RED}✗ SSH connection failed${NC}"
    echo ""
    echo "On your Mac server, enable Remote Login:"
    echo "  System Preferences → Sharing → Remote Login (check it)"
    echo ""
    echo "Then from this laptop, set up SSH key:"
    echo "  ssh-copy-id $SERVER_USER@$SERVER_IP"
    exit 1
fi
echo -e "${GREEN}✓ SSH works${NC}"
echo ""

# Confirm
echo -e "${YELLOW}This will sync all code changes to the server.${NC}"
echo "Excluded: venv, .env, uploads, outputs, databases, logs"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${CYAN}Syncing...${NC}"

# Rsync
rsync -avz --progress \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='.env' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    --exclude='.tmp.*' \
    --exclude='outputs/*' \
    --exclude='uploads/*' \
    --exclude='database/*.db' \
    --exclude='database/*.db-journal' \
    --exclude='.claude/' \
    --exclude='.pytest_cache/' \
    "$PROJECT_ROOT/" "$SERVER_USER@$SERVER_IP:$SERVER_PATH/"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ SYNC COMPLETE${NC}"
    echo ""
    echo -e "${YELLOW}Now restart ZoolZ on the server:${NC}"
    echo ""
    echo "  Option 1 - From this laptop:"
    echo "    ssh $SERVER_USER@$SERVER_IP 'cd ~/Desktop/ZoolZ && pkill -f python.*app.py; ./start_zoolz.sh'"
    echo ""
    echo "  Option 2 - On the Mac server terminal:"
    echo "    cd ~/Desktop/ZoolZ"
    echo "    pkill -f 'python.*app.py'"
    echo "    ./start_zoolz.sh"
    echo ""
else
    echo -e "${RED}✗ Sync failed${NC}"
    exit 1
fi
