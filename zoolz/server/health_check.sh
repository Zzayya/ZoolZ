#!/bin/bash
# ZoolZ Health Check - Comprehensive system verification
# Tests EVERYTHING to ensure ZoolZ is ready to rock

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Counters
TESTS_PASSED=0
TESTS_FAILED=0
WARNINGS=0

log_test() {
    echo -e "${CYAN}→ $1${NC}"
}

log_pass() {
    echo -e "${GREEN}  ✅ $1${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_fail() {
    echo -e "${RED}  ❌ $1${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

log_warn() {
    echo -e "${YELLOW}  ⚠️  $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

log_section() {
    echo ""
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ZOOLZ HEALTH CHECK & VERIFICATION             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# ENVIRONMENT CHECKS
# ============================================================================

log_section "Environment Checks"

log_test "Server marker file"
if [ -f "$HOME/Desktop/SERVER" ]; then
    log_pass "Server mode enabled"
else
    log_warn "No SERVER marker (running in laptop mode)"
fi

log_test "Virtual environment"
if [ -d "venv" ]; then
    log_pass "venv exists"

    # Check if activated
    if [[ "$VIRTUAL_ENV" == *"venv" ]]; then
        log_pass "venv is activated"
    else
        log_warn "venv not activated - run: source venv/bin/activate"
    fi
else
    log_fail "venv not found - run setup script first"
fi

log_test "Python version"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
    log_pass "Python $PYTHON_VERSION"
else
    log_fail "Python not found"
fi

# ============================================================================
# CORE DEPENDENCIES
# ============================================================================

log_section "Core Dependencies"

log_test "Flask"
if python3 -c "import flask; print(f'Flask {flask.__version__}')" &> /dev/null; then
    VERSION=$(python3 -c "import flask; print(flask.__version__)")
    log_pass "Flask $VERSION"
else
    log_fail "Flask not installed"
fi

log_test "psutil (ZoolZmstr dependency)"
if python3 -c "import psutil" &> /dev/null; then
    log_pass "psutil installed"
else
    log_fail "psutil missing - ZoolZmstr won't work!"
fi

log_test "Celery"
if python3 -c "import celery" &> /dev/null; then
    log_pass "Celery installed"
else
    log_warn "Celery missing - no background tasks"
fi

log_test "Redis (service)"
if command -v redis-server &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        log_pass "Redis running"
    else
        log_warn "Redis installed but not running"
    fi
else
    log_warn "Redis not installed - no background tasks"
fi

# ============================================================================
# 3D MODELING DEPENDENCIES
# ============================================================================

log_section "3D Modeling Dependencies"

log_test "NumPy"
if python3 -c "import numpy" &> /dev/null; then
    VERSION=$(python3 -c "import numpy; print(numpy.__version__)")
    log_pass "NumPy $VERSION"
else
    log_fail "NumPy missing - CRITICAL for Modeling"
fi

log_test "SciPy"
if python3 -c "import scipy" &> /dev/null; then
    VERSION=$(python3 -c "import scipy; print(scipy.__version__)")
    log_pass "SciPy $VERSION"
else
    log_warn "SciPy missing - some features won't work"
fi

log_test "trimesh"
if python3 -c "import trimesh" &> /dev/null; then
    VERSION=$(python3 -c "import trimesh; print(trimesh.__version__)")
    log_pass "trimesh $VERSION"
else
    log_fail "trimesh missing - Modeling won't work!"
fi

log_test "OpenCV"
if python3 -c "import cv2" &> /dev/null; then
    VERSION=$(python3 -c "import cv2; print(cv2.__version__)")
    log_pass "OpenCV $VERSION"
else
    log_fail "OpenCV missing - cookie cutters won't work!"
fi

log_test "Pillow"
if python3 -c "import PIL" &> /dev/null; then
    VERSION=$(python3 -c "import PIL; print(PIL.__version__)")
    log_pass "Pillow $VERSION"
else
    log_warn "Pillow missing - image processing limited"
fi

log_test "shapely"
if python3 -c "import shapely" &> /dev/null; then
    VERSION=$(python3 -c "import shapely; print(shapely.__version__)")
    log_pass "shapely $VERSION"
else
    log_warn "shapely missing - some operations won't work"
fi

# ============================================================================
# ZOOLZ CORE COMPONENTS
# ============================================================================

log_section "ZoolZ Core Components"

log_test "ZoolZmstr imports"
if python3 -c "from zoolz.ZoolZmstr import is_server, get_environment, process_manager, health_monitor" &> /dev/null; then
    log_pass "ZoolZmstr core working"
else
    log_fail "ZoolZmstr import failed!"
fi

log_test "Environment detection"
if python3 -c "from zoolz.ZoolZmstr import get_environment; env = get_environment(); print(f'Environment: {env}')" &> /dev/null; then
    ENV=$(python3 -c "from zoolz.ZoolZmstr import get_environment; print(get_environment())")
    log_pass "Environment: $ENV"
else
    log_fail "Environment detection failed"
fi

log_test "config.py"
if python3 -c "from config import config" &> /dev/null; then
    log_pass "Configuration loads successfully"
else
    log_fail "config.py import failed"
fi

log_test "app.py"
if python3 -c "from app import app" &> /dev/null 2>&1; then
    log_pass "Flask app initializes"
else
    log_fail "app.py import failed"
fi

# ============================================================================
# PROGRAM BLUEPRINTS
# ============================================================================

log_section "Program Blueprints"

log_test "Modeling blueprint"
if python3 -c "from programs.Modeling.blueprint import modeling_bp" &> /dev/null 2>&1; then
    log_pass "Modeling blueprint loads"
else
    log_fail "Modeling blueprint failed"
fi

log_test "PeopleFinder blueprint"
if python3 -c "from programs.PeopleFinder.blueprint import people_finder_bp" &> /dev/null 2>&1; then
    log_pass "PeopleFinder blueprint loads"
else
    log_fail "PeopleFinder blueprint failed"
fi

log_test "ParametricCAD blueprint"
if python3 -c "from programs.ParametricCAD.blueprint import parametric_bp" &> /dev/null 2>&1; then
    log_pass "ParametricCAD blueprint loads"
else
    log_fail "ParametricCAD blueprint failed"
fi

log_test "DigitalFootprint blueprint"
if python3 -c "from programs.DigitalFootprint.blueprint import digital_footprint_bp" &> /dev/null 2>&1; then
    log_pass "DigitalFootprint blueprint loads"
else
    log_fail "DigitalFootprint blueprint failed"
fi

# ============================================================================
# MODELING PROGRAM DEEP CHECK
# ============================================================================

log_section "Modeling Program Deep Check"

log_test "All Modeling utils"
if python3 -c "
from programs.Modeling.utils import thicken, hollow, repair, simplify, mirror
from programs.Modeling.utils import shape_generators, scale, cut, channels, bore_hole
from programs.Modeling.utils import fidget_generators, advanced_operations
" &> /dev/null 2>&1; then
    log_pass "All 12 utils modules load"
else
    log_fail "Some utils modules failed"
fi

log_test "Cookie cutter logic"
if python3 -c "from programs.Modeling.shared.cookie_logic import generate_cookie_cutter, extract_outline_data" &> /dev/null 2>&1; then
    log_pass "Cookie cutter logic working"
else
    log_fail "Cookie cutter logic failed"
fi

log_test "Stamp logic"
if python3 -c "from programs.Modeling.shared.stamp_logic import generate_stamp" &> /dev/null 2>&1; then
    log_pass "Stamp logic working"
else
    log_fail "Stamp logic failed"
fi

# ============================================================================
# FILE STRUCTURE
# ============================================================================

log_section "File Structure"

log_test "Database folder"
if [ -d "database" ]; then
    log_pass "database/ exists"
else
    log_warn "database/ not found"
fi

log_test "User accounts"
if [ -f "database/users.json" ]; then
    USER_COUNT=$(python3 -c "import json; data=json.load(open('database/users.json')); print(len(data['users']))")
    log_pass "$USER_COUNT user(s) configured"
else
    log_warn "No users.json found"
fi

log_test "Upload folder"
if [ -d "uploads" ]; then
    log_pass "uploads/ exists"
else
    log_warn "uploads/ not found"
fi

log_test "Templates"
if [ -d "templates" ]; then
    log_pass "templates/ exists"
else
    log_fail "templates/ not found"
fi

log_test "Static files"
if [ -d "static" ]; then
    log_pass "static/ exists"
else
    log_fail "static/ not found"
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    HEALTH CHECK RESULTS                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo -e "${GREEN}ZoolZ is 100% ready to rock! 🚀${NC}"
    echo ""
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS warnings (non-critical)${NC}"
        echo ""
    fi
    exit 0
else
    echo -e "${RED}${BOLD}❌ TESTS FAILED${NC}"
    echo ""
    echo -e "${RED}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    echo ""
    echo -e "${RED}Fix the errors above before starting ZoolZ${NC}"
    echo ""
    exit 1
fi
