#!/bin/bash
# Quick network readiness check for ZoolZ on macOS

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }

echo "━━━ ZoolZ Network Check ━━━"

mac_ip=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "unknown")
if [ "$mac_ip" = "unknown" ]; then
    warn "Could not detect LAN IP (en0/en1). Check Wi‑Fi/Ethernet is connected."
else
    pass "LAN IP: $mac_ip"
fi

# Verify port availability
if lsof -i :5001 >/dev/null 2>&1; then
    warn "Port 5001 already in use. Identify process with: lsof -i :5001"
else
    pass "Port 5001 is free"
fi

# Quick curl to local endpoint if running
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/health >/dev/null 2>&1; then
    pass "ZoolZ health endpoint responding locally"
else
    warn "Health endpoint not reachable locally (start ZoolZ or check firewall)"
fi

echo ""
echo "If you need external access, forward external port 5001 → ${mac_ip:-<your_mac_ip>}:5001 on your router."
