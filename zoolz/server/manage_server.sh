#!/bin/bash
# ZoolZ Server Management Script
# Control the server remotely from your laptop

# CONFIGURATION - UPDATE THESE FOR YOUR SERVER
SERVER_USER="isaiahmiro"  # iMac username
SERVER_IP="10.0.0.11"   # iMac's local IP
SERVER_ZOOLZ_PATH="~/Desktop/ZoolZ"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

show_menu() {
    clear
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           ZOOLZ SERVER REMOTE MANAGEMENT                   ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  Server: $SERVER_USER@$SERVER_IP"
    echo ""
    echo "  1. Start ZoolZ"
    echo "  2. Stop ZoolZ"
    echo "  3. Restart ZoolZ"
    echo "  4. Check Status"
    echo "  5. View Logs (last 20 lines)"
    echo "  6. Sync Code from Laptop"
    echo "  7. Open SSH Session"
    echo "  Q. Quit"
    echo ""
}

start_server() {
    echo -e "${BLUE}🚀 Starting ZoolZ on server...${NC}"
    ssh "$SERVER_USER@$SERVER_IP" "cd $SERVER_ZOOLZ_PATH && ./start_zoolz.sh > /dev/null 2>&1 &"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ZoolZ started${NC}"
        echo "   Access at: http://$SERVER_IP:5001"
    else
        echo -e "${RED}❌ Failed to start${NC}"
    fi
}

stop_server() {
    echo -e "${YELLOW}🛑 Stopping ZoolZ on server...${NC}"
    ssh "$SERVER_USER@$SERVER_IP" "pkill -f 'python.*app.py'; pkill -f 'celery.*worker'; pkill -f 'redis-server.*6379'"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ZoolZ stopped${NC}"
    else
        echo -e "${RED}❌ Failed to stop${NC}"
    fi
}

restart_server() {
    echo -e "${YELLOW}🔄 Restarting ZoolZ...${NC}"
    stop_server
    sleep 2
    start_server
}

check_status() {
    echo -e "${BLUE}📊 Checking server status...${NC}"
    echo ""
    ssh "$SERVER_USER@$SERVER_IP" "cd $SERVER_ZOOLZ_PATH && pgrep -fl 'python.*app.py|redis-server|celery.*worker' || echo 'ZoolZ not running'"
}

view_logs() {
    echo -e "${BLUE}📄 Server logs (last 20 lines):${NC}"
    echo ""
    echo "--- Flask Log ---"
    ssh "$SERVER_USER@$SERVER_IP" "cd $SERVER_ZOOLZ_PATH && tail -20 app.log 2>/dev/null || echo 'No Flask log found'"
    echo ""
    echo "--- Celery Log ---"
    ssh "$SERVER_USER@$SERVER_IP" "cd $SERVER_ZOOLZ_PATH && tail -20 celery.log 2>/dev/null || echo 'No Celery log found'"
}

sync_code() {
    echo -e "${BLUE}🔄 Running sync script...${NC}"
    ./sync_to_server.sh
}

open_ssh() {
    echo -e "${BLUE}🔐 Opening SSH session to server...${NC}"
    echo "   (type 'exit' to return to management menu)"
    echo ""
    ssh "$SERVER_USER@$SERVER_IP" "cd $SERVER_ZOOLZ_PATH && exec bash"
}

# Main loop
while true; do
    show_menu
    read -p "Select option: " -n 1 choice
    echo ""
    echo ""

    case $choice in
        1)
            start_server
            ;;
        2)
            stop_server
            ;;
        3)
            restart_server
            ;;
        4)
            check_status
            ;;
        5)
            view_logs
            ;;
        6)
            sync_code
            ;;
        7)
            open_ssh
            ;;
        q|Q)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac

    echo ""
    read -p "Press ENTER to continue..."
done
