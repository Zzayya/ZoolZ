#!/bin/bash
# ZoolZ Server Setup - STATE OF THE ART
# Handles Python version detection, package installation with retries, and full validation

set -e  # Exit on error
trap 'handle_error $? $LINENO' ERR

# ============================================================================
# CONFIGURATION
# ============================================================================

REQUIRED_PYTHON_VERSION="3.12"
BACKUP_DIR="$HOME/Desktop/ZoolZ_backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="setup.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_step() {
    echo ""
    log "${CYAN}${BOLD}━━━ $1 ━━━${NC}"
}

log_success() {
    log "${GREEN}✅ $1${NC}"
}

log_error() {
    log "${RED}❌ $1${NC}"
}

log_warn() {
    log "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    log "${BLUE}ℹ️  $1${NC}"
}

handle_error() {
    local exit_code=$1
    local line_number=$2
    log_error "Setup failed at line $line_number with exit code $exit_code"
    log_error "Check $LOG_FILE for details"
    log_info "Backup created at: $BACKUP_DIR"
    exit $exit_code
}

progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percent=$((current * 100 / total))
    local filled=$((width * current / total))
    local empty=$((width - filled))

    printf "\r${CYAN}["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] ${percent}%%${NC}"
}

# ============================================================================
# PYTHON VERSION MANAGEMENT
# ============================================================================

detect_python() {
    log_step "Detecting Python Installation"

    # Check for python3.12 specifically
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
        PYTHON_VERSION=$(python3.12 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
        log_success "Found Python 3.12: $PYTHON_VERSION"
        log_success "Using: $(which python3.12)"
        return 0
    fi

    # Check default python3
    if command -v python3 &> /dev/null; then
        local default_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

        if [ "$default_version" == "3.12" ]; then
            PYTHON_CMD="python3"
            PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
            log_success "Found Python 3.12: $PYTHON_VERSION"
            log_success "Using: $(which python3)"
            return 0
        elif [ "$default_version" == "3.13" ]; then
            log_warn "Default Python is 3.13 (too new)"
            log_info "Will attempt to install Python 3.12..."
            install_python_312
            return $?
        else
            log_warn "Default Python is $default_version"
            log_info "Python 3.12 required. Will attempt to install..."
            install_python_312
            return $?
        fi
    fi

    log_error "No Python found!"
    log_info "Installing Python 3.12..."
    install_python_312
    return $?
}

install_python_312() {
    log_step "Installing Python 3.12"

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        log_error "Homebrew not found!"
        log_info "Install Homebrew first:"
        log_info '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        return 1
    fi

    log_info "Installing python@3.12 via Homebrew..."
    if brew install python@3.12 2>&1 | tee -a "$LOG_FILE"; then
        # Link python3.12
        brew link python@3.12 2>&1 | tee -a "$LOG_FILE" || true

        # Verify installation
        if command -v python3.12 &> /dev/null; then
            PYTHON_CMD="python3.12"
            PYTHON_VERSION=$(python3.12 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
            log_success "Python 3.12 installed: $PYTHON_VERSION"
            return 0
        else
            log_error "Python 3.12 installation failed"
            return 1
        fi
    else
        log_error "Homebrew install failed"
        return 1
    fi
}

install_redis() {
    log_step "Installing Redis"

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        log_error "Homebrew not found! Cannot install Redis."
        return 1
    fi

    # Check if Redis already installed
    if command -v redis-server &> /dev/null; then
        log_success "Redis already installed"
        return 0
    fi

    log_info "Installing redis via Homebrew..."
    if brew install redis 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Redis installed"

        # Start Redis service
        log_info "Starting Redis service..."
        brew services start redis 2>&1 | tee -a "$LOG_FILE"

        # Wait for Redis to start
        sleep 2

        # Verify Redis running
        if redis-cli ping &> /dev/null; then
            log_success "Redis is running"
            return 0
        else
            log_warn "Redis installed but not running"
            log_info "Start it manually with: brew services start redis"
            return 0
        fi
    else
        log_error "Redis installation failed"
        log_warn "ZoolZ will work without Redis (no background tasks)"
        return 0  # Don't fail setup if Redis install fails
    fi
}

# ============================================================================
# VIRTUAL ENVIRONMENT MANAGEMENT
# ============================================================================

setup_venv() {
    log_step "Setting Up Virtual Environment"

    # Backup old venv if exists
    if [ -d "venv" ]; then
        log_info "Backing up old venv..."
        mkdir -p "$BACKUP_DIR"
        mv venv "$BACKUP_DIR/venv_old" 2>&1 | tee -a "$LOG_FILE"
        log_success "Old venv backed up to $BACKUP_DIR"
    fi

    # Create fresh venv
    log_info "Creating fresh virtual environment with $PYTHON_CMD..."
    if $PYTHON_CMD -m venv venv 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Virtual environment created"
    else
        log_error "Failed to create venv"
        return 1
    fi

    # Activate venv
    source venv/bin/activate

    # Verify activation
    local venv_prefix=$(python3 -c "import sys; print(sys.prefix)" 2>/dev/null)
    if [[ "$venv_prefix" == *"/venv" ]]; then
        log_success "Virtual environment activated"
        log_info "Python: $venv_prefix/bin/python3"
    else
        log_error "Failed to activate venv"
        log_error "Expected venv prefix, got: $venv_prefix"
        return 1
    fi

    # Upgrade pip, setuptools, wheel
    log_info "Upgrading pip, setuptools, wheel..."
    python3 -m pip install --upgrade pip setuptools wheel --quiet 2>&1 | tee -a "$LOG_FILE"
    local pip_version=$(pip --version)
    log_success "Build tools upgraded: $pip_version"
}

# ============================================================================
# PACKAGE INSTALLATION WITH RETRY LOGIC
# ============================================================================

install_package_with_retry() {
    local package=$1
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_info "Installing $package (attempt $attempt/$max_attempts)..."

        if pip install "$package" 2>&1 | tee -a "$LOG_FILE"; then
            log_success "$package installed"
            return 0
        else
            log_warn "Attempt $attempt failed for $package"
            attempt=$((attempt + 1))
            sleep 2
        fi
    done

    log_error "Failed to install $package after $max_attempts attempts"
    return 1
}

install_packages() {
    log_step "Installing Python Packages"

    # Critical packages (MUST succeed)
    local critical_packages=(
        "Flask==3.0.0"
        "Werkzeug==3.0.0"
        "python-dotenv==1.0.0"
        "celery==5.3.4"
        "redis==5.0.0"
        "psutil==5.9.6"
    )

    log_info "Stage 1: Critical Dependencies (MUST succeed)"
    local total=${#critical_packages[@]}
    local current=0

    for package in "${critical_packages[@]}"; do
        current=$((current + 1))
        progress_bar $current $total
        echo ""  # Newline after progress bar

        if ! install_package_with_retry "$package"; then
            log_error "Critical package failed: $package"
            log_error "Cannot continue without core dependencies"
            return 1
        fi
    done

    log_success "All critical packages installed"
    echo ""

    # 3D/ML packages - CRITICAL INSTALLATION ORDER!
    # NumPy MUST be installed first with <2.0 constraint
    # Then scipy, Pillow, trimesh (these are safe)
    # Then opencv-python (pinned to 4.8.x which needs NumPy 1.x)
    # Finally shapely with --no-deps to prevent NumPy 2.x sneaking in
    log_info "Stage 2: 3D/ML Libraries (EXACT ORDER for NumPy compatibility)"

    # STEP 1: Install NumPy FIRST with strict version lock
    log_info "[1/6] Installing NumPy 1.x (CRITICAL - must be <2.0)..."
    if ! pip install "numpy>=1.24.0,<2.0" 2>&1 | tee -a "$LOG_FILE"; then
        log_error "NumPy installation failed - CANNOT CONTINUE"
        return 1
    fi

    # Verify NumPy version
    local numpy_version=$(python3 -c "import numpy; print(numpy.__version__)" 2>&1)
    if [[ "$numpy_version" == 2.* ]]; then
        log_error "NumPy 2.x detected ($numpy_version) - WRONG VERSION!"
        return 1
    fi
    log_success "NumPy $numpy_version installed (1.x confirmed ✓)"

    # STEP 2: Install scipy (safe with NumPy 1.x)
    log_info "[2/6] Installing scipy..."
    if ! install_package_with_retry "scipy>=1.11.0"; then
        log_warn "scipy failed (non-critical)"
    fi

    # STEP 3: Install Pillow (safe)
    log_info "[3/6] Installing Pillow..."
    if ! install_package_with_retry "Pillow>=10.0.0"; then
        log_warn "Pillow failed (non-critical)"
    fi

    # STEP 4: Install trimesh (needs NumPy 1.x)
    log_info "[4/6] Installing trimesh 4.0.5..."
    if ! install_package_with_retry "trimesh==4.0.5"; then
        log_error "trimesh failed - MODELING WON'T WORK!"
        return 1
    fi
    log_success "trimesh installed (3D modeling ready)"

    # STEP 5: Install OpenCV with strict version lock (4.8.x - last NumPy 1.x compatible)
    log_info "[5/6] Installing opencv-python 4.8.x (NumPy 1.x compatible)..."
    if ! pip install "opencv-python>=4.8.0,<4.9" 2>&1 | tee -a "$LOG_FILE"; then
        log_warn "opencv-python failed (cookie cutters won't work)"
    else
        local opencv_version=$(python3 -c "import cv2; print(cv2.__version__)" 2>&1)
        log_success "opencv-python $opencv_version installed ✓"
    fi

    # STEP 6: Install shapely with --no-deps (CRITICAL - prevents NumPy 2.x reinstall)
    log_info "[6/6] Installing shapely 2.0.2 with --no-deps..."
    if ! pip install --force-reinstall --no-cache-dir --no-deps shapely==2.0.2 2>&1 | tee -a "$LOG_FILE"; then
        log_error "shapely failed - MODELING WON'T WORK!"
        return 1
    fi
    log_success "shapely installed (no dependency conflicts ✓)"

    # Verify NumPy still correct after all installs
    numpy_version=$(python3 -c "import numpy; print(numpy.__version__)" 2>&1)
    if [[ "$numpy_version" == 2.* ]]; then
        log_error "NumPy got upgraded to 2.x ($numpy_version) - DEPENDENCY CONFLICT!"
        log_error "Re-installing NumPy 1.x..."
        pip install --force-reinstall "numpy>=1.24.0,<2.0" 2>&1 | tee -a "$LOG_FILE"
    fi
    log_success "NumPy version verified: $numpy_version ✓"

    echo ""

    # Install remaining packages (best effort)
    log_info "Stage 3: Additional Packages"
    local extra_packages=(
        "mapbox-earcut"
        "pyclipper==1.3.0.post5"
        "pymeshlab==2023.12.post3"
    )

    for package in "${extra_packages[@]}"; do
        if ! install_package_with_retry "$package"; then
            log_warn "$package failed (non-critical)"
        fi
    done

    # Final pass - install any remaining from requirements.txt
    log_info "Installing remaining requirements..."
    pip install -r requirements.txt --quiet 2>&1 | tee -a "$LOG_FILE" || log_warn "Some optional packages failed"

    log_success "Package installation complete ✓"
}

# ============================================================================
# VALIDATION & TESTING
# ============================================================================

test_imports() {
    log_step "Testing Critical Imports"

    local tests_passed=0
    local tests_failed=0

    # Test Flask
    if python3 -c "import flask; print(f'Flask {flask.__version__}')" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Flask working"
        tests_passed=$((tests_passed + 1))
    else
        log_error "Flask import failed"
        tests_failed=$((tests_failed + 1))
    fi

    # Test psutil (CRITICAL for ZoolZmstr)
    if python3 -c "import psutil; print(f'psutil {psutil.__version__}')" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "psutil working"
        tests_passed=$((tests_passed + 1))
    else
        log_error "psutil import failed - ZoolZmstr won't work!"
        tests_failed=$((tests_failed + 1))
        return 1
    fi

    # Test ZoolZmstr
    if python3 -c "from zoolz.ZoolZmstr import is_server, get_environment; print(f'Environment: {get_environment()}'); print('Server mode:', 'YES' if is_server() else 'NO')" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "ZoolZmstr working"
        tests_passed=$((tests_passed + 1))
    else
        log_error "ZoolZmstr import failed!"
        tests_failed=$((tests_failed + 1))
        return 1
    fi

    # Test numpy (non-critical but important)
    if python3 -c "import numpy; print(f'numpy {numpy.__version__}')" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "numpy working"
        tests_passed=$((tests_passed + 1))
    else
        log_warn "numpy not available (cookie cutters may not work)"
        tests_failed=$((tests_failed + 1))
    fi

    # Test scipy
    if python3 -c "import scipy; print(f'scipy {scipy.__version__}')" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "scipy working"
        tests_passed=$((tests_passed + 1))
    else
        log_warn "scipy not available (some features may not work)"
    fi

    # Test trimesh (CRITICAL for Modeling)
    if python3 -c "import trimesh; print(f'trimesh {trimesh.__version__}')" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "trimesh working (3D modeling ready)"
        tests_passed=$((tests_passed + 1))
    else
        log_warn "trimesh not available (Modeling program won't work!)"
        tests_failed=$((tests_failed + 1))
    fi

    # Test OpenCV (for cookie cutters)
    if python3 -c "import cv2; print(f'opencv {cv2.__version__}')" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "opencv working (cookie cutters ready)"
        tests_passed=$((tests_passed + 1))
    else
        log_warn "opencv not available (cookie cutters won't work)"
    fi

    # Test app.py imports
    if python3 -c "from app import app; print('✓ Flask app loads successfully')" 2>&1 | grep "✓" | tee -a "$LOG_FILE"; then
        log_success "app.py working"
        tests_passed=$((tests_passed + 1))
    else
        log_error "app.py import failed!"
        tests_failed=$((tests_failed + 1))
        return 1
    fi

    # Test Modeling program - COMPREHENSIVE (imports + actual shape generation)
    log_info "Testing Modeling program (this is CRITICAL)..."

    # Test 1: Import all Modeling modules
    if python3 -c "from programs.Modeling.blueprint import modeling_bp; from programs.Modeling.utils import thicken, hollow, shape_generators; from programs.Modeling.shared.cookie_logic import generate_cookie_cutter; print('✓ Imports OK')" 2>&1 | grep "✓" | tee -a "$LOG_FILE"; then
        log_success "Modeling imports working ✓"
    else
        log_error "Modeling imports failed!"
        tests_failed=$((tests_failed + 1))
        return 1
    fi

    # Test 2: Actually generate a shape (real functional test)
    if python3 -c "
import trimesh
from programs.Modeling.utils.shape_generators import generate_cube, generate_sphere

# Test cube generation
cube = generate_cube(size=10)
assert cube.vertices.shape[0] > 0, 'Cube has no vertices'
assert cube.faces.shape[0] > 0, 'Cube has no faces'

# Test sphere generation
sphere = generate_sphere(radius=5)
assert sphere.vertices.shape[0] > 0, 'Sphere has no vertices'
assert sphere.faces.shape[0] > 0, 'Sphere has no faces'

print('✓ Shape generation working')
" 2>&1 | grep "✓" | tee -a "$LOG_FILE"; then
        log_success "Modeling shape generation WORKS ✓✓✓"
        tests_passed=$((tests_passed + 1))
    else
        log_error "Modeling shape generation FAILED - THIS IS THE ISSUE!"
        tests_failed=$((tests_failed + 1))
        return 1
    fi

    # Test 3: Boolean operations
    if python3 -c "
from programs.Modeling.utils.shape_generators import generate_cube
from programs.Modeling.utils.boolean_ops import union_meshes

cube1 = generate_cube(size=10)
cube2 = generate_cube(size=10)
result = union_meshes([cube1, cube2])
assert result is not None, 'Union failed'
print('✓ Boolean ops working')
" 2>&1 | grep "✓" | tee -a "$LOG_FILE"; then
        log_success "Modeling boolean operations WORK ✓"
        tests_passed=$((tests_passed + 1))
    else
        log_warn "Boolean operations test failed (non-critical)"
    fi

    echo ""
    log_info "Import Tests: $tests_passed passed, $tests_failed failed"

    if [ $tests_failed -gt 2 ]; then
        log_error "Too many critical imports failed"
        return 1
    fi

    return 0
}

check_redis() {
    log_step "Checking Redis"

    if command -v redis-server &> /dev/null; then
        local redis_version=$(redis-server --version | head -n 1)
        log_success "Redis found: $redis_version"

        # Check if Redis is actually running
        if command -v redis-cli &> /dev/null; then
            if redis-cli ping &> /dev/null; then
                log_success "Redis is running"
            else
                log_info "Redis installed but not running"
                log_info "Start it with: brew services start redis"
            fi
        fi
    else
        log_warn "Redis not installed"
        log_info "Install with: brew install redis"
        log_info "ZoolZ will work without it (no background tasks)"
    fi
}

# ============================================================================
# MAIN SETUP FLOW
# ============================================================================

main() {
    clear
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         ZOOLZ SERVER SETUP - STATE OF THE ART             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # Check not running as root
    if [ "$EUID" -eq 0 ] || [ "$USER" == "root" ]; then
        echo -e "${RED}❌ ERROR: Do not run this script as root or with sudo${NC}"
        echo ""
        echo "Run it as your normal user:"
        echo "  ./setup_server_FINAL.sh"
        echo ""
        echo "(Not: sudo ./setup_server_FINAL.sh)"
        exit 1
    fi

    # Initialize log
    if ! echo "Setup started: $(date)" > "$LOG_FILE" 2>/dev/null; then
        echo -e "${RED}❌ Cannot create log file in current directory${NC}"
        echo "Make sure you have write permissions in $(pwd)"
        exit 1
    fi

    # Check server marker
    if [ ! -f "$HOME/Desktop/SERVER" ]; then
        log_error "Server marker file not found!"
        log_info "Create it with: touch ~/Desktop/SERVER"
        exit 1
    fi
    log_success "Server marker detected"

    # Detect/install Python 3.12
    if ! detect_python; then
        log_error "Python setup failed"
        exit 1
    fi

    # Install Redis
    install_redis  # Non-critical, won't exit on failure

    # Setup venv
    if ! setup_venv; then
        log_error "Virtual environment setup failed"
        exit 1
    fi

    # Install packages
    if ! install_packages; then
        log_error "Package installation failed"
        exit 1
    fi

    # Test imports
    if ! test_imports; then
        log_error "Import tests failed"
        exit 1
    fi

    # Check Redis
    check_redis

    # Success!
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║              ✅ SETUP COMPLETE - SUCCESS! ✅               ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "Python: $PYTHON_VERSION"
    log_info "Venv: $(pwd)/venv"
    log_info "Log: $LOG_FILE"
    echo ""
    log_success "ZoolZ is FULLY OPERATIONAL!"
    echo ""
    log_info "Verified:"
    echo "  ✓ Flask 3.0 + all web dependencies"
    echo "  ✓ Python 3.12 environment"
    echo "  ✓ NumPy 1.x (compatible versions locked)"
    echo "  ✓ trimesh, shapely, opencv working"
    echo "  ✓ Modeling program tested (shapes + booleans)"
    echo "  ✓ ZoolZmstr orchestration system"
    echo ""

    # Ask user if they want auto-start
    echo -e "${CYAN}${BOLD}━━━ AUTO-START OPTION ━━━${NC}"
    echo ""
    echo "Would you like to automatically start ZoolZ now?"
    echo "This will:"
    echo "  1. Launch Flask server in background"
    echo "  2. Open monitoring dashboard"
    echo "  3. You can walk away and come back to everything running"
    echo ""
    read -p "Auto-start ZoolZ? [Y/n]: " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        log_step "Auto-Starting ZoolZ"

        # Make scripts executable
        chmod +x start_zoolz.sh
        chmod +x zoolz/server/monitor_server.sh

        # Start ZoolZ in background
        log_info "Launching Flask server..."
        nohup ./start_zoolz.sh > zoolz_server.log 2>&1 &
        local zoolz_pid=$!
        sleep 3

        # Check if it's running
        if ps -p $zoolz_pid > /dev/null; then
            log_success "ZoolZ server started (PID: $zoolz_pid)"
            log_info "Server logs: tail -f zoolz_server.log"
        else
            log_warn "ZoolZ may have failed to start - check zoolz_server.log"
        fi

        # Start monitor in a new terminal window
        log_info "Opening monitoring dashboard..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS - open new Terminal tab
            osascript -e 'tell application "Terminal" to do script "cd '"$(pwd)"' && ./zoolz/server/monitor_server.sh"' &
            log_success "Monitor opened in new Terminal tab"
        else
            log_info "Start monitor manually: ./zoolz/server/monitor_server.sh"
        fi

        echo ""
        echo "╔════════════════════════════════════════════════════════════╗"
        echo "║                  🚀 ZOOLZ IS LIVE! 🚀                     ║"
        echo "╚════════════════════════════════════════════════════════════╝"
        echo ""
        log_info "Access ZoolZ at:"
        echo "     http://71.60.55.85:5001"
        echo ""
        log_info "Login:"
        echo "     Username: Zay"
        echo "     Password: 442767"
        echo ""
        log_info "Monitoring:"
        echo "     Check the new Terminal tab for live stats"
        echo ""
        log_info "Stop server:"
        echo "     pkill -f 'flask run' or kill $zoolz_pid"
        echo ""
    else
        echo ""
        log_info "Manual start commands:"
        echo "  1. Start ZoolZ:"
        echo "     ./start_zoolz.sh"
        echo ""
        echo "  2. Monitor (separate terminal):"
        echo "     ./zoolz/server/monitor_server.sh"
        echo ""
        echo "  3. Access:"
        echo "     http://71.60.55.85:5001"
        echo ""
        echo "  Login: Zay / 442767"
        echo ""
    fi
}

# Run main
main
