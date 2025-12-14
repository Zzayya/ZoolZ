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

    # 3D/ML packages (best effort)
    log_info "Stage 2: 3D/ML Libraries (best effort)"

    local ml_packages=(
        "numpy>=1.24.0"
        "scipy>=1.11.0"
        "Pillow>=10.0.0"
        "trimesh==4.0.5"
        "shapely==2.0.2"
        "mapbox-earcut"
        "pyclipper==1.3.0.post5"
    )

    total=${#ml_packages[@]}
    current=0

    for package in "${ml_packages[@]}"; do
        current=$((current + 1))
        progress_bar $current $total
        echo ""

        if ! install_package_with_retry "$package"; then
            log_warn "$package failed (non-critical, continuing...)"
        fi
    done

    echo ""

    # Try opencv
    log_info "Installing opencv-python..."
    if ! pip install "opencv-python>=4.6.0" --quiet 2>&1 | tee -a "$LOG_FILE"; then
        log_warn "opencv-python failed (non-critical)"
    else
        log_success "opencv-python installed"
    fi

    # Remaining packages (best effort)
    log_info "Stage 3: Remaining Packages (best effort)"
    pip install -r requirements.txt --quiet 2>&1 | tee -a "$LOG_FILE" || log_warn "Some optional packages failed"

    log_success "Package installation complete"
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
    if python3 -c "from ZoolZmstr import is_server, get_environment; print(f'Environment: {get_environment()}'); print('Server mode:', 'YES' if is_server() else 'NO')" 2>&1 | tee -a "$LOG_FILE"; then
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
    log_success "ZoolZ is ready to launch!"
    echo ""
    log_info "Next steps:"
    echo "  1. Start ZoolZ:"
    echo "     ./start_zoolz.sh"
    echo ""
    echo "  2. Monitor (separate terminal):"
    echo "     ./monitor_server.sh"
    echo ""
    echo "  3. Access:"
    echo "     http://71.60.55.85:5001"
    echo ""
    echo "  Login: Zay / 442767"
    echo ""
}

# Run main
main
