#!/bin/bash
# ZoolZ Server Setup Script - BULLETPROOF VERSION
# Handles Python 3.13, retries, proper error handling

set -e  # Exit on any error

echo "=========================================="
echo "   ZOOLZ SERVER SETUP - v2"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're on the server
if [ ! -f "$HOME/Desktop/SERVER" ]; then
    echo -e "${YELLOW}⚠️  Server marker file not found!${NC}"
    echo ""
    echo "IMPORTANT: You need to create a marker file first!"
    echo "Run this command:"
    echo "  touch ~/Desktop/SERVER"
    echo ""
    read -p "Press Enter after creating the file, or Ctrl+C to exit..."
    echo ""

    # Check again
    if [ ! -f "$HOME/Desktop/SERVER" ]; then
        echo -e "${RED}❌ Marker file still not found. Exiting.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Server marker file detected${NC}"
echo ""

# Check Python version
echo -e "${BLUE}🔍 Checking Python version...${NC}"
python3 --version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

echo "Python version: $PYTHON_VERSION"

# Warn if Python 3.13 (numpy issues)
if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
    echo -e "${YELLOW}⚠️  Warning: Python 3.13 detected${NC}"
    echo "   Some packages may have compatibility issues"
    echo "   We'll handle this with flexible version ranges"
fi

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 7) else 1)'; then
    echo -e "${RED}❌ Python 3.7+ required! Current version: $PYTHON_VERSION${NC}"
    echo "Please install Python 3.9-3.12 from python.org (avoid 3.13 for now)"
    exit 1
fi
echo -e "${GREEN}✅ Python version OK${NC}"
echo ""

# Remove old/broken venv if it exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}🗑️  Removing old virtual environment...${NC}"
    rm -rf venv
    echo -e "${GREEN}✅ Old venv removed${NC}"
fi

# Create fresh virtual environment
echo -e "${BLUE}📦 Creating fresh virtual environment...${NC}"
python3 -m venv venv

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Virtual environment created successfully${NC}"
else
    echo -e "${RED}❌ Failed to create virtual environment${NC}"
    exit 1
fi
echo ""

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate
echo ""

# Upgrade pip
echo -e "${BLUE}⬆️  Upgrading pip, setuptools, wheel...${NC}"
pip install --upgrade pip setuptools wheel --quiet
echo -e "${GREEN}✅ Build tools upgraded${NC}"
echo ""

# Install packages with retry logic
echo -e "${BLUE}📥 Installing Python packages...${NC}"
echo "This might take 5-10 minutes..."
echo ""

# Install in stages with proper error handling
install_package() {
    local package=$1
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo -e "${BLUE}Installing $package (attempt $attempt/$max_attempts)...${NC}"

        if pip install "$package" --quiet; then
            echo -e "${GREEN}✅ $package installed${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Attempt $attempt failed${NC}"
            attempt=$((attempt + 1))
            sleep 2
        fi
    done

    echo -e "${RED}❌ Failed to install $package after $max_attempts attempts${NC}"
    return 1
}

# Stage 1: Core dependencies (must succeed)
echo -e "${BLUE}━━━ Stage 1: Core Dependencies ━━━${NC}"
CORE_DEPS=(
    "Flask==3.0.0"
    "Werkzeug==3.0.0"
    "python-dotenv==1.0.0"
    "celery==5.3.4"
    "redis==5.0.0"
    "psutil==5.9.6"
)

for dep in "${CORE_DEPS[@]}"; do
    if ! install_package "$dep"; then
        echo -e "${RED}❌ Core dependency failed: $dep${NC}"
        echo "Cannot continue without core dependencies"
        exit 1
    fi
done
echo ""

# Stage 2: Python 3.13 compatible packages
echo -e "${BLUE}━━━ Stage 2: 3D/ML Libraries ━━━${NC}"

# Install numpy without version pin (gets latest compatible)
echo -e "${BLUE}Installing numpy (auto-detecting compatible version)...${NC}"
pip install "numpy>=1.24.0" --quiet && echo -e "${GREEN}✅ numpy installed${NC}" || echo -e "${YELLOW}⚠️  numpy failed (non-critical)${NC}"

# Try opencv with fallback
echo -e "${BLUE}Installing opencv-python...${NC}"
if ! pip install "opencv-python==4.6.0.66" --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  opencv 4.6 failed, trying latest...${NC}"
    pip install "opencv-python" --quiet && echo -e "${GREEN}✅ opencv installed (latest)${NC}" || echo -e "${YELLOW}⚠️  opencv failed (non-critical)${NC}"
else
    echo -e "${GREEN}✅ opencv-python==4.6.0.66 installed${NC}"
fi

# Install remaining packages
ML_DEPS=(
    "Pillow>=10.0.0"
    "scipy>=1.11.0"
    "trimesh==4.0.5"
    "shapely==2.0.2"
    "mapbox-earcut"
    "pyclipper==1.3.0.post5"
)

for dep in "${ML_DEPS[@]}"; do
    install_package "$dep" || echo -e "${YELLOW}⚠️  $dep failed (non-critical)${NC}"
done
echo ""

# Stage 3: Remaining dependencies
echo -e "${BLUE}━━━ Stage 3: Remaining Packages ━━━${NC}"
pip install -r requirements.txt --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  Some optional packages failed${NC}"
echo ""

echo -e "${GREEN}✅ Package installation complete!${NC}"
echo ""

# Test imports
echo -e "${BLUE}🧪 Testing critical imports...${NC}"

# Test Flask
if python3 -c "import flask; print(f'Flask {flask.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✅ Flask working${NC}"
else
    echo -e "${RED}❌ Flask import failed${NC}"
    exit 1
fi

# Test psutil (critical for ZoolZmstr)
if python3 -c "import psutil; print(f'psutil {psutil.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✅ psutil working${NC}"
else
    echo -e "${RED}❌ psutil import failed - ZoolZmstr won't work${NC}"
    exit 1
fi

# Test ZoolZmstr
echo -e "${BLUE}🧪 Testing ZoolZmstr...${NC}"
if python3 -c "from ZoolZmstr import is_server, get_environment; print(f'Environment: {get_environment()}'); print('Server mode: {}'.format('YES ✅' if is_server() else 'NO ❌'))" 2>/dev/null; then
    echo -e "${GREEN}✅ ZoolZmstr working${NC}"
else
    echo -e "${RED}❌ ZoolZmstr test failed!${NC}"
    echo "Trying to diagnose..."
    python3 -c "from ZoolZmstr import is_server" 2>&1 | head -20
    exit 1
fi

# Test numpy (non-critical)
if python3 -c "import numpy; print(f'numpy {numpy.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✅ numpy working${NC}"
else
    echo -e "${YELLOW}⚠️  numpy not available (cookie cutters may not work)${NC}"
fi

echo ""

# Check if Redis is installed
echo -e "${BLUE}🔍 Checking if Redis is installed...${NC}"
if command -v redis-server &> /dev/null; then
    REDIS_VERSION=$(redis-server --version | head -n 1)
    echo -e "${GREEN}✅ Redis found: $REDIS_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  Redis not installed${NC}"
    echo "   Install with: brew install redis"
    echo "   ZoolZ will work without it (no background tasks)"
fi
echo ""

# All done!
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 SETUP COMPLETE!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Next steps:"
echo "  1. Start ZoolZ:"
echo "     ./start_zoolz.sh"
echo ""
echo "  2. Monitor server (in separate terminal):"
echo "     ./monitor_server.sh"
echo ""
echo "  3. Access from browser:"
echo "     http://71.60.55.85:5001"
echo ""
echo "  Login: Zay / 442767"
echo ""
