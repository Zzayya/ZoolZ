#!/bin/bash
# ZoolZ Pre-Flight Check Script
# Run this AFTER setup to verify everything is ready

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           ZOOLZ PRE-FLIGHT CHECK                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "${YELLOW}⚠${NC} $1"; WARNINGS=$((WARNINGS + 1)); }

# ============================================================================
# ENVIRONMENT CHECKS
# ============================================================================
echo "━━━ Environment ━━━"

# Check server marker
if [ -f "$HOME/Desktop/SERVER" ]; then
    pass "Server marker exists (~/Desktop/SERVER)"
else
    warn "Server marker NOT found - create with: touch ~/Desktop/SERVER"
fi

# Check we're in ZoolZ directory
if [ -f "app.py" ] && [ -f "requirements.txt" ]; then
    pass "In ZoolZ directory"
else
    fail "Not in ZoolZ directory!"
    exit 1
fi

# Check venv exists
if [ -d "venv" ]; then
    pass "Virtual environment exists"
else
    fail "Virtual environment not found - run setup_server_FINAL.sh first"
fi

echo ""

# ============================================================================
# PYTHON CHECKS
# ============================================================================
echo "━━━ Python ━━━"

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
if [[ "$PYTHON_VERSION" == "3.12" ]] || [[ "$PYTHON_VERSION" == "3.11" ]] || [[ "$PYTHON_VERSION" == "3.10" ]]; then
    pass "Python $PYTHON_VERSION"
else
    fail "Python version $PYTHON_VERSION (need 3.10-3.12)"
fi

# Check critical imports
echo ""
echo "━━━ Python Packages ━━━"

python3 -c "import flask" 2>/dev/null && pass "Flask" || fail "Flask not installed"
python3 -c "import celery" 2>/dev/null && pass "Celery" || fail "Celery not installed"
python3 -c "import redis" 2>/dev/null && pass "Redis" || fail "Redis not installed"
python3 -c "import psutil" 2>/dev/null && pass "psutil" || fail "psutil not installed"
python3 -c "import numpy" 2>/dev/null && pass "NumPy" || fail "NumPy not installed"
python3 -c "import trimesh" 2>/dev/null && pass "trimesh" || warn "trimesh not installed (Modeling won't work)"
python3 -c "import cv2" 2>/dev/null && pass "OpenCV" || warn "OpenCV not installed (cookie cutters won't work)"
python3 -c "import shapely" 2>/dev/null && pass "shapely" || warn "shapely not installed"

# Check NumPy version (must be <2.0)
NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null)
if [[ "$NUMPY_VERSION" == 1.* ]]; then
    pass "NumPy version $NUMPY_VERSION (1.x required)"
else
    fail "NumPy version $NUMPY_VERSION - MUST be <2.0!"
fi

echo ""

# ============================================================================
# APP CHECKS
# ============================================================================
echo "━━━ Application ━━━"

# Test app.py imports
if python3 -c "from app import app" 2>/dev/null; then
    pass "app.py loads successfully"
else
    fail "app.py fails to load!"
fi

# Test ZoolZmstr
if python3 -c "from zoolz.ZoolZmstr import is_server, get_environment" 2>/dev/null; then
    pass "ZoolZmstr module works"
else
    fail "ZoolZmstr module broken!"
fi

# Test all blueprints
python3 -c "from programs.Modeling.blueprint import modeling_bp" 2>/dev/null && pass "Modeling blueprint" || fail "Modeling blueprint broken"
python3 -c "from programs.ParametricCAD.blueprint import parametric_bp" 2>/dev/null && pass "ParametricCAD blueprint" || fail "ParametricCAD blueprint broken"
python3 -c "from programs.PeopleFinder.blueprint import people_finder_bp" 2>/dev/null && pass "PeopleFinder blueprint" || warn "PeopleFinder blueprint broken"
python3 -c "from programs.DigitalFootprint.blueprint import digital_footprint_bp" 2>/dev/null && pass "DigitalFootprint blueprint" || warn "DigitalFootprint blueprint broken"

echo ""

# ============================================================================
# REDIS CHECKS
# ============================================================================
echo "━━━ Redis ━━━"

if command -v redis-server &> /dev/null; then
    pass "Redis installed"
    if redis-cli ping 2>/dev/null | grep -q "PONG"; then
        pass "Redis is running"
    else
        warn "Redis installed but not running (start with: brew services start redis)"
    fi
else
    warn "Redis not installed (background tasks won't work)"
fi

echo ""

# ============================================================================
# FILE CHECKS
# ============================================================================
echo "━━━ Critical Files ━━━"

[ -f "app.py" ] && pass "app.py" || fail "app.py missing"
[ -f "config.py" ] && pass "config.py" || fail "config.py missing"
[ -f "tasks.py" ] && pass "tasks.py" || fail "tasks.py missing"
[ -f "decorators.py" ] && pass "decorators.py" || fail "decorators.py missing"
[ -f "requirements.txt" ] && pass "requirements.txt" || fail "requirements.txt missing"
[ -f "start_zoolz.sh" ] && pass "start_zoolz.sh" || fail "start_zoolz.sh missing"
[ -f ".env" ] && pass ".env file" || warn ".env file missing (will be created by setup)"

echo ""

# ============================================================================
# TEMPLATE CHECKS
# ============================================================================
echo "━━━ Templates ━━━"

[ -f "templates/login.html" ] && pass "login.html" || fail "login.html missing"
[ -f "templates/hub.html" ] && pass "hub.html" || fail "hub.html missing"
[ -f "programs/Modeling/templates/modeling.html" ] && pass "modeling.html" || fail "modeling.html missing"

echo ""

# ============================================================================
# NETWORK CHECKS
# ============================================================================
echo "━━━ Network ━━━"

# Get IP
MAC_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "unknown")
if [ "$MAC_IP" != "unknown" ]; then
    pass "Mac IP: $MAC_IP"
else
    warn "Could not detect IP address"
fi

# Check port 5001
if lsof -i :5001 &> /dev/null; then
    warn "Port 5001 is already in use!"
else
    pass "Port 5001 is available"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "╔════════════════════════════════════════════════════════════╗"
if [ $ERRORS -eq 0 ]; then
    echo -e "║  ${GREEN}✓ PRE-FLIGHT CHECK PASSED${NC}                               ║"
else
    echo -e "║  ${RED}✗ PRE-FLIGHT CHECK FAILED ($ERRORS errors)${NC}                    ║"
fi
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}Warnings: $WARNINGS${NC} (non-critical, some features may not work)"
fi

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}Errors: $ERRORS${NC} - FIX THESE BEFORE STARTING!"
    echo ""
    echo "Run the setup script to fix issues:"
    echo "  ./zoolz/server/setup_server_FINAL.sh"
    exit 1
fi

echo ""
echo "Ready to start ZoolZ:"
echo "  ./start_zoolz.sh"
echo ""
echo "Access at: http://$MAC_IP:5001"
echo "Login: Zay / 442767"
echo ""
