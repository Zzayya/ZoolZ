#!/bin/bash
# ZoolZ Code Sync Script
# Syncs code from laptop to server (excludes data/venv/logs)

# CONFIGURATION - UPDATE THESE FOR YOUR SERVER
SERVER_USER="isaiahmiro"  # iMac username
SERVER_IP="10.0.0.11"   # iMac's local IP
SERVER_PATH="~/Desktop/ZoolZ/"

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ZOOLZ CODE SYNC TO SERVER                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the ZoolZ directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Not in ZoolZ directory"
    echo "Please run this from the ZoolZ folder"
    exit 1
fi

# Confirm sync
echo -e "${YELLOW}This will sync code changes to the server:${NC}"
echo "  From: $(pwd)"
echo "  To:   $SERVER_USER@$SERVER_IP:$SERVER_PATH"
echo ""
echo -e "${YELLOW}Excluded (won't sync):${NC}"
echo "  • venv/"
echo "  • __pycache__/"
echo "  • database/"
echo "  • outputs/ (Modeling program)"
echo "  • *.pyc files"
echo "  • .DS_Store files"
echo "  • Log files"
echo ""
read -p "Continue with sync? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Sync cancelled"
    exit 0
fi

echo ""
echo "🚀 Starting sync..."
echo ""

# Rsync with exclusions
rsync -avz --progress \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    --exclude 'database/' \
    --exclude 'programs/Modeling/outputs/' \
    --exclude '*.log' \
    --exclude 'celery.log' \
    --exclude 'app.log' \
    ./ "$SERVER_USER@$SERVER_IP:$SERVER_PATH"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Sync complete!${NC}"
    echo ""
    echo "📝 Next steps:"
    echo "  1. SSH into server: ssh $SERVER_USER@$SERVER_IP"
    echo "  2. Restart ZoolZ (see manage_server.sh)"
    echo ""
else
    echo ""
    echo "❌ Sync failed"
    echo "Check that:"
    echo "  • Server IP is correct: $SERVER_IP"
    echo "  • Server username is correct: $SERVER_USER"
    echo "  • You can SSH to server: ssh $SERVER_USER@$SERVER_IP"
    exit 1
fi
