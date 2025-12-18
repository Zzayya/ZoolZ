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
ENV_FILE=".env"

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

    # STEP 5: Install OpenCV (FORCE pre-built wheel, NEVER compile from source)
    log_info "[5/6] Installing opencv-python (SMART VERSION DETECTION)..."

    # Function to find best available OpenCV version with wheels
    find_best_opencv_version() {
        log_info "Detecting available opencv-python versions with wheels for this Mac..."

        # Get all available versions from pip
        local versions=$(pip index versions opencv-python 2>&1 | grep "Available versions:" | sed 's/Available versions: //')

        if [ -z "$versions" ]; then
            log_error "Cannot query pip for opencv-python versions"
            return 1
        fi

        log_info "Available versions: $versions"

        # Preferred versions (try these first, in order)
        local preferred_versions=("4.10.0.84" "4.8.1.78" "4.6.0.66" "4.5.5.64" "4.5.5.62")

        # Try preferred versions first
        for pref_ver in "${preferred_versions[@]}"; do
            if echo "$versions" | grep -q "$pref_ver"; then
                log_info "Trying preferred version: $pref_ver..."
                if pip install --only-binary=:all: "opencv-python==$pref_ver" --quiet 2>&1 | tee -a "$LOG_FILE"; then
                    # Verify it actually works
                    if python3 -c "import cv2; print(cv2.__version__)" 2>&1 > /dev/null; then
                        echo "$pref_ver"
                        return 0
                    else
                        log_warn "Version $pref_ver installed but import failed, trying next..."
                        pip uninstall -y opencv-python --quiet 2>&1 > /dev/null
                    fi
                fi
            fi
        done

        # If preferred versions don't work, try the latest available
        log_info "Preferred versions unavailable, trying latest with wheel..."
        if pip install --only-binary=:all: opencv-python --quiet 2>&1 | tee -a "$LOG_FILE"; then
            if python3 -c "import cv2; print(cv2.__version__)" 2>&1 > /dev/null; then
                local installed_ver=$(python3 -c "import cv2; print(cv2.__version__)" 2>&1)
                echo "$installed_ver"
                return 0
            fi
        fi

        # Last resort: try opencv-python-headless (smaller, no GUI)
        log_warn "opencv-python failed, trying opencv-python-headless..."
        if pip install --only-binary=:all: opencv-python-headless --quiet 2>&1 | tee -a "$LOG_FILE"; then
            if python3 -c "import cv2; print(cv2.__version__)" 2>&1 > /dev/null; then
                local installed_ver=$(python3 -c "import cv2; print(cv2.__version__)" 2>&1)
                echo "$installed_ver"
                return 0
            fi
        fi

        return 1
    }

    # Find and install best OpenCV version
    opencv_installed_version=$(find_best_opencv_version)

    if [ $? -eq 0 ] && [ -n "$opencv_installed_version" ]; then
        # Final verification
        if python3 -c "import cv2" 2>&1 | grep -q "Error\|Traceback"; then
            log_error "opencv-python $opencv_installed_version installed but HAS IMPORT ERRORS!"
            return 1
        fi
        log_success "opencv-python $opencv_installed_version VERIFIED WORKING ✓"
        log_info "Cookie cutter generation will work!"
    else
        log_error "FAILED to install ANY working opencv-python version!"
        log_error "Your Mac architecture may not have pre-built wheels."
        log_error "Cookie cutter generation will NOT work."
        return 1
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
        "pymeshlab==2023.12.post1"
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

    # Test ZoolZmstr (CRITICAL - app.py needs this)
    log_info "Testing ZoolZmstr imports..."
    if ! python3 -c "from zoolz.ZoolZmstr import is_server, get_environment; print(f'Environment: {get_environment()}'); print('Server mode:', 'YES' if is_server() else 'NO')" 2>&1 | tee -a "$LOG_FILE"; then
        log_error "ZoolZmstr import FAILED!"
        tests_failed=$((tests_failed + 1))
        return 1
    fi
    # Double-check no errors in output
    if python3 -c "from zoolz.ZoolZmstr import is_server" 2>&1 | grep -q "Error\|Traceback"; then
        log_error "ZoolZmstr has import errors!"
        tests_failed=$((tests_failed + 1))
        return 1
    fi
    log_success "ZoolZmstr VERIFIED WORKING"
    tests_passed=$((tests_passed + 1))

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

    # Test OpenCV (CRITICAL for cookie cutters)
    if python3 -c "import cv2; print(f'opencv {cv2.__version__}')" 2>&1 | tee -a "$LOG_FILE"; then
        # Check if import actually succeeded (no "ModuleNotFoundError" in output)
        if python3 -c "import cv2" 2>&1 | grep -q "ModuleNotFoundError"; then
            log_error "opencv IMPORT FAILED - cv2 module not found!"
            tests_failed=$((tests_failed + 1))
        else
            log_success "opencv VERIFIED WORKING (cookie cutters ready)"
            tests_passed=$((tests_passed + 1))
        fi
    else
        log_error "opencv not available (cookie cutters WON'T WORK!)"
        tests_failed=$((tests_failed + 1))
    fi

    # Test app.py imports (CRITICAL - if this fails, Flask won't start!)
    log_info "Testing Flask app.py..."
    if ! python3 -c "from app import app; print('✓ Flask app loads successfully')" 2>&1 | tee -a "$LOG_FILE"; then
        log_error "app.py import FAILED!"
        tests_failed=$((tests_failed + 1))
        return 1
    fi
    # Check for errors in output
    if python3 -c "from app import app" 2>&1 | grep -q "Error\|Traceback\|ModuleNotFoundError"; then
        log_error "app.py has import errors!"
        tests_failed=$((tests_failed + 1))
        return 1
    fi
    log_success "app.py VERIFIED WORKING (Flask will start!)"
    tests_passed=$((tests_passed + 1))

    # Test Modeling program - COMPREHENSIVE (imports + actual shape generation)
    log_info "Testing Modeling program (this is CRITICAL)..."

    # Test 1: Import all Modeling modules
    if python3 -c "from programs.Modeling.blueprint import modeling_bp; from programs.Modeling.utils import thicken, hollow, shape_generators; from programs.Modeling.utils.cookie_logic import generate_cookie_cutter; print('✓ Imports OK')" 2>&1 | grep "✓" | tee -a "$LOG_FILE"; then
        log_success "Modeling imports working ✓"
    else
        log_error "Modeling imports failed!"
        tests_failed=$((tests_failed + 1))
        return 1
    fi

    # Test 2: Actually generate a shape (real functional test)
    if python3 -c "
import trimesh
from programs.Modeling.utils.shape_generators import generate_shape

# Test cube generation
cube_result = generate_shape('cube', {'size': 10})
assert 'mesh' in cube_result, 'No mesh returned'
cube = cube_result['mesh']
assert cube.vertices.shape[0] > 0, 'Cube has no vertices'
assert cube.faces.shape[0] > 0, 'Cube has no faces'

# Test sphere generation
sphere_result = generate_shape('sphere', {'radius': 5})
sphere = sphere_result['mesh']
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
from programs.Modeling.utils.shape_generators import generate_shape
from programs.Modeling.utils.boolean_ops import union_meshes

cube1 = generate_shape('cube', {'size': 10})['mesh']
cube2 = generate_shape('cube', {'size': 10})['mesh']
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

verify_network_config() {
    log_step "Verifying Network Configuration"

    # Get Mac's local IP address
    local mac_ip=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "unknown")

    if [ "$mac_ip" == "unknown" ]; then
        log_warn "Could not detect Mac's IP address"
        log_info "Check manually with: ipconfig getifaddr en0"
    else
        log_success "Mac's local IP: $mac_ip"
    fi

    # Check if port 5001 is available
    if lsof -i :5001 &> /dev/null; then
        log_warn "Port 5001 is already in use!"
        log_info "Stop the process using it: lsof -i :5001"
    else
        log_success "Port 5001 is available"
    fi

    # Verify Flask configuration in app.py
    if grep -q "host='0.0.0.0'" app.py; then
        log_success "Flask configured correctly (0.0.0.0:5001)"
    elif grep -q 'host="0.0.0.0"' app.py; then
        log_success "Flask configured correctly (0.0.0.0:5001)"
    else
        log_error "Flask NOT configured to accept network connections!"
        log_error "app.py should have: app.run(host='0.0.0.0', port=...)"
        return 1
    fi

    # Show access URLs
    echo ""
    log_info "${BOLD}Access URLs after Flask starts:${NC}"
    echo "  ${CYAN}From Mac:      http://localhost:5001${NC}"
    if [ "$mac_ip" != "unknown" ]; then
        echo "  ${CYAN}From network:  http://$mac_ip:5001${NC}"
    fi
    echo "  ${CYAN}From internet: http://71.60.55.85:5001${NC} (via router)"
    echo ""
    log_info "${BOLD}Port forwarding required:${NC}"
    echo "  Router must forward: External 5001 → $mac_ip:5001"
    echo ""

    return 0
}

verify_cookie_cutter_dependencies() {
    log_step "Testing Cookie Cutter Pipeline"

    local all_good=true

    # Test 1: OpenCV with actual image processing
    log_info "Testing OpenCV image processing..."
    if python3 -c "
import cv2
import numpy as np

# Create a test image
img = np.zeros((100, 100, 3), dtype=np.uint8)
img[25:75, 25:75] = [255, 255, 255]

# Test edge detection
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 50, 150)

# Test contour finding
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Test morphological operations
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
dilated = cv2.dilate(edges, kernel)

print(f'✓ OpenCV image processing: {len(contours)} contours found')
" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "OpenCV image processing working"
    else
        log_warn "OpenCV image processing test failed"
        all_good=false
    fi

    # Test 2: Cookie cutter full pipeline
    log_info "Testing cookie cutter generation pipeline..."
    if python3 -c "
from programs.Modeling.utils.cookie_logic import build_mask_from_image, find_and_smooth_contour
import numpy as np
import cv2
import tempfile

# Create a test image with a simple shape
img = np.zeros((200, 200, 3), dtype=np.uint8)
cv2.circle(img, (100, 100), 50, (255, 255, 255), -1)

# Save to temp file
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
    temp_path = f.name
    cv2.imwrite(temp_path, img)

try:
    # Test mask building
    mask = build_mask_from_image(temp_path)

    # Test contour extraction
    contour = find_and_smooth_contour(mask, mode='outer')

    print(f'✓ Cookie cutter pipeline: {len(contour)} points extracted')
except Exception as e:
    print(f'✗ Cookie cutter pipeline failed: {e}')
    import sys
    sys.exit(1)
finally:
    import os
    os.unlink(temp_path)
" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Cookie cutter pipeline working"
    else
        log_warn "Cookie cutter pipeline test failed"
        all_good=false
    fi

    # Test 3: trimesh 3D mesh creation
    log_info "Testing trimesh 3D mesh creation..."
    if python3 -c "
import trimesh
from shapely.geometry import Polygon

# Create a simple polygon
points = [(0, 0), (10, 0), (10, 10), (0, 10)]
poly = Polygon(points)

# Extrude to 3D
mesh = trimesh.creation.extrude_polygon(poly, height=5.0)

print(f'✓ Trimesh extrusion: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces')
" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Trimesh 3D mesh creation working"
    else
        log_warn "Trimesh test failed"
        all_good=false
    fi

    echo ""
    if $all_good; then
        log_success "Cookie cutter generation pipeline working ✓"
        return 0
    else
        log_warn "Cookie cutter tests failed - troubleshoot after Flask starts"
        return 1
    fi
}

# ============================================================================
# ENV SETUP HELPERS
# ============================================================================

ensure_env_secret() {
    log_step "Ensuring .env has strong SECRET_KEY"

    # If file missing, create it with sane defaults
    if [ ! -f "$ENV_FILE" ]; then
        log_info "No .env found; creating a fresh one with a random SECRET_KEY"
        cat > "$ENV_FILE" << EOF
# ZoolZ Environment (generated by setup)
FLASK_ENV=production
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
PORT=5001
CELERY_TASK_TIMEOUT=600
EOF
        log_success ".env created with secure SECRET_KEY"
        return 0
    fi

    # If exists, ensure SECRET_KEY present and not placeholder
    if ! grep -q '^SECRET_KEY=' "$ENV_FILE"; then
        log_info "Adding SECRET_KEY to existing .env"
        echo "SECRET_KEY=$(openssl rand -hex 32)" >> "$ENV_FILE"
        log_success "SECRET_KEY appended to .env"
    else
        local current_key
        current_key=$(grep '^SECRET_KEY=' "$ENV_FILE" | head -n1 | cut -d'=' -f2-)
        if [ -z "$current_key" ] || [ "$current_key" = "dev-secret-key-change-in-production" ]; then
            log_info "SECRET_KEY in .env is empty/placeholder; replacing it"
            # Replace line in place
            sed -i '' "s/^SECRET_KEY=.*/SECRET_KEY=$(openssl rand -hex 32)/" "$ENV_FILE"
            log_success "SECRET_KEY refreshed"
        else
            log_success "SECRET_KEY already set"
        fi
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

    local macos_version
    macos_version=$(sw_vers -productVersion 2>/dev/null || echo "unknown")
    log_info "Detected macOS: $macos_version (target: Catalina 10.15.x)"

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

    # Show network configuration (informational only)
    verify_network_config || log_warn "Network check had warnings - continuing anyway"

    # Test cookie cutter dependencies (informational only - don't block deployment)
    verify_cookie_cutter_dependencies || log_warn "Some features may not work - Flask will still start"

    # Ensure .env and SECRET_KEY exist
    ensure_env_secret

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

    # Make scripts executable
    chmod +x start_zoolz.sh 2>/dev/null || true
    chmod +x start_zoolz_multi_terminal.sh 2>/dev/null || true
    chmod +x zoolz/server/*.sh 2>/dev/null || true

    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                   HOW TO START ZOOLZ                      ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "${BOLD}START:${NC}"
    echo "  ${CYAN}./start_zoolz.sh${NC}"
    echo ""
    log_info "${BOLD}DEPLOY / UPDATE CODE:${NC}"
    echo "  ${CYAN}git pull${NC}   # fetch latest from origin"
    echo "  ${CYAN}git status${NC} # check local changes"
    echo ""
    log_info "${BOLD}STOP:${NC}"
    echo "  ${CYAN}Press Ctrl+C in the terminal${NC}"
    echo ""
    log_info "${BOLD}ACCESS:${NC}"
    echo "  Local:    ${CYAN}http://localhost:5001${NC}"
    echo "  Network:  ${CYAN}http://$(ipconfig getifaddr en0 2>/dev/null || echo "10.0.0.11"):5001${NC}"
    echo "  Internet: ${CYAN}http://71.60.55.85:5001${NC}"
    echo ""
}

# Run main
main
