#!/bin/bash
# Server Dashboard - Shows running services and access info

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

clear

# HACKERMAN ASCII BORDER
echo -e "${PURPLE}${BOLD}"
cat << "EOF"
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  ███████╗ ██████╗  ██████╗ ██╗     ███████╗                   ║
║  ╚══███╔╝██╔═══██╗██╔═══██╗██║     ╚══███╔╝                   ║
║    ███╔╝ ██║   ██║██║   ██║██║       ███╔╝                    ║
║   ███╔╝  ██║   ██║██║   ██║██║      ███╔╝                     ║
║  ███████╗╚██████╔╝╚██████╔╝███████╗███████╗                   ║
║  ╚══════╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝                   ║
║                                                                ║
║               🧙‍♂️  SERVER CONTROL DASHBOARD  ⚡                 ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# System Info
echo -e "${CYAN}${BOLD}[SYSTEM INFO]${NC}"
echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Hostname:${NC}      $(hostname)"
echo -e "${CYAN}Computer:${NC}      $(scutil --get ComputerName 2>/dev/null || echo "Unknown")"
echo -e "${CYAN}macOS:${NC}         $(sw_vers -productVersion)"
echo -e "${CYAN}Python:${NC}        $(python3 --version 2>&1 | cut -d' ' -f2)"
echo -e "${CYAN}Local IP:${NC}      $(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "Not connected")"
echo -e "${CYAN}Uptime:${NC}        $(uptime | awk '{print $3,$4}' | sed 's/,//')"
echo ""

# Service Status
echo -e "${GREEN}${BOLD}[SERVICES STATUS]${NC}"
echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check Flask
if pgrep -f "python.*app.py" > /dev/null; then
    FLASK_PID=$(pgrep -f "python.*app.py")
    echo -e "${GREEN}[●]${NC} Flask App        ${GREEN}RUNNING${NC}  (PID: $FLASK_PID)"
else
    echo -e "${RED}[○]${NC} Flask App        ${RED}STOPPED${NC}"
fi

# Check Redis
if pgrep redis-server > /dev/null; then
    REDIS_PID=$(pgrep redis-server)
    echo -e "${GREEN}[●]${NC} Redis Server     ${GREEN}RUNNING${NC}  (PID: $REDIS_PID)"
else
    echo -e "${YELLOW}[○]${NC} Redis Server     ${YELLOW}STOPPED${NC}"
fi

# Check Celery
if pgrep -f "celery.*worker" > /dev/null; then
    CELERY_PID=$(pgrep -f "celery.*worker")
    echo -e "${GREEN}[●]${NC} Celery Worker    ${GREEN}RUNNING${NC}  (PID: $CELERY_PID)"
else
    echo -e "${YELLOW}[○]${NC} Celery Worker    ${YELLOW}STOPPED${NC}"
fi

# Check SSH
if systemsetup -getremotelogin 2>/dev/null | grep -q "On"; then
    echo -e "${GREEN}[●]${NC} SSH (rsync)      ${GREEN}ENABLED${NC}"
else
    echo -e "${YELLOW}[○]${NC} SSH (rsync)      ${YELLOW}DISABLED${NC}"
fi

echo ""

# Access Info
echo -e "${PURPLE}${BOLD}[ACCESS INFORMATION]${NC}"
echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Local URL:${NC}     ${BOLD}http://localhost:5001${NC}"
echo -e "${CYAN}Network URL:${NC}   ${BOLD}http://$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "0.0.0.0"):5001${NC}"
echo ""
echo -e "${CYAN}Login:${NC}         ${BOLD}Zay${NC}"
echo -e "${CYAN}Password:${NC}      ${BOLD}442767${NC}"
echo ""

# Programs
echo -e "${YELLOW}${BOLD}[AVAILABLE PROGRAMS]${NC}"
echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}[✓]${NC} 3D Modeling       - Parametric shape generator + STL tools"
echo -e "${GREEN}[✓]${NC} Parametric CAD    - Advanced 3D design workspace"
echo -e "${GREEN}[✓]${NC} PeopleFinder      - NLP-powered contact search"
echo -e "${GREEN}[✓]${NC} Digital Footprint - Social media analyzer"
echo ""

# Quick Commands
echo -e "${BLUE}${BOLD}[QUICK COMMANDS]${NC}"
echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Restart:${NC}       ${DIM}./start_zoolz.sh${NC}"
echo -e "${CYAN}Stop:${NC}          ${DIM}pkill -f 'python.*app.py'${NC}"
echo -e "${CYAN}View logs:${NC}     ${DIM}tail -f celery.log${NC}"
echo -e "${CYAN}Dashboard:${NC}     ${DIM}./show_server_dashboard.sh${NC}"
echo ""

# Footer
echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}        ✨ Server is ready! Open browser and login ✨${NC}"
echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
