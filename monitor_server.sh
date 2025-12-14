#!/bin/bash
# ZoolZ Server Monitoring Dashboard
# Run this separately from start_zoolz.sh to monitor server processes

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           ZOOLZ SERVER MONITORING DASHBOARD                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to get process status
get_process_status() {
    local process_name=$1
    local pid=$(pgrep -f "$process_name")

    if [ -z "$pid" ]; then
        echo "❌ NOT RUNNING"
        return 1
    else
        echo "✅ RUNNING (PID: $pid)"
        return 0
    fi
}

# Function to get memory usage
get_memory_usage() {
    local process_name=$1
    local pid=$(pgrep -f "$process_name")

    if [ -z "$pid" ]; then
        echo "N/A"
    else
        ps -p $pid -o rss= | awk '{printf "%.1f MB", $1/1024}'
    fi
}

# Function to refresh dashboard
show_dashboard() {
    clear

    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           ZOOLZ SERVER MONITORING DASHBOARD                ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 SYSTEM STATUS - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Check environment
    local env_marker=""
    if [ -f "$HOME/Desktop/SERVER" ]; then
        env_marker="🖥️  SERVER MODE"
    else
        env_marker="💻 LAPTOP MODE"
    fi

    # Check if ZoolZ is actually running
    local flask_running=$(get_process_status 'python.*app.py' | grep -q "RUNNING" && echo "✅" || echo "⚠️  NOT RUNNING")

    echo "Environment: $env_marker"
    echo "ZoolZ:       $flask_running"
    echo ""

    # Flask Status
    echo "🌐 FLASK WEB SERVER"
    echo "   Status: $(get_process_status 'python.*app.py')"
    echo "   Memory: $(get_memory_usage 'python.*app.py')"
    echo "   Port:   5001"
    echo ""

    # Redis Status
    echo "📦 REDIS (Cache & Queue)"
    echo "   Status: $(get_process_status 'redis-server.*6379')"
    echo "   Memory: $(get_memory_usage 'redis-server.*6379')"
    echo "   Port:   6379"

    # Test Redis connection
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            echo "   Ping:   ✅ PONG"
        else
            echo "   Ping:   ❌ NO RESPONSE"
        fi
    fi
    echo ""

    # Celery Status
    echo "⚙️  CELERY WORKER (Background Tasks)"
    echo "   Status: $(get_process_status 'celery.*worker')"
    echo "   Memory: $(get_memory_usage 'celery.*worker')"

    # Check celery queue
    if [ -f "celery.log" ]; then
        local last_line=$(tail -1 celery.log 2>/dev/null)
        echo "   Last:   ${last_line:0:60}..."
    fi
    echo ""

    # System Resources
    echo "💾 SYSTEM RESOURCES"

    # CPU Usage (macOS)
    cpu_usage=$(ps -A -o %cpu | awk '{s+=$1} END {printf "%.1f%%", s}')
    echo "   CPU:    $cpu_usage"

    # Memory Usage (macOS)
    mem_total=$(sysctl -n hw.memsize | awk '{printf "%.0f", $1/1024/1024/1024}')
    mem_used=$(vm_stat | awk '/Pages active/ {active=$3} /Pages wired/ {wired=$4} END {printf "%.1f", (active+wired)*4096/1024/1024/1024}')
    echo "   RAM:    ${mem_used}GB / ${mem_total}GB"

    # Disk Usage
    disk_usage=$(df -h . | awk 'NR==2 {print $5}')
    disk_avail=$(df -h . | awk 'NR==2 {print $4}')
    echo "   Disk:   $disk_usage used, $disk_avail available"
    echo ""

    # Network Info
    echo "🌐 NETWORK ACCESS"
    local local_ip=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    if [ ! -z "$local_ip" ]; then
        echo "   Local:  http://${local_ip}:5001"
    fi
    echo "   Port:   5001"
    echo ""

    # Active Programs
    echo "📱 ZOOLZ PROGRAMS"
    local modeling_active=$(pgrep -f "modeling" > /dev/null && echo "✅" || echo "⚪")
    local people_finder_active=$(pgrep -f "people_finder" > /dev/null && echo "✅" || echo "⚪")
    echo "   ${modeling_active} Modeling"
    echo "   ${people_finder_active} PeopleFinder"
    echo "   ⚪ ParametricCAD"
    echo "   ⚪ DigitalFootprint"
    echo ""

    # Log Files
    echo "📄 LOG FILES"
    if [ -f "celery.log" ]; then
        local celery_size=$(ls -lh celery.log | awk '{print $5}')
        echo "   celery.log:  $celery_size"
    fi
    if [ -f "app.log" ]; then
        local app_size=$(ls -lh app.log | awk '{print $5}')
        echo "   app.log:     $app_size"
    fi
    echo ""

    # Quick Actions
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⌨️  QUICK ACTIONS:"
    echo "   R - Refresh now"
    echo "   L - View logs"
    echo "   Q - Quit monitor"
    echo ""
    echo "Auto-refreshing in 5 seconds..."
}

# Function to view logs
view_logs() {
    clear
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                    ZOOLZ LOG VIEWER                        ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "1. Celery Log (last 20 lines)"
    echo "2. Flask App Log (if exists)"
    echo "3. Back to dashboard"
    echo ""
    read -p "Select: " -n 1 log_choice
    echo ""

    case $log_choice in
        1)
            if [ -f "celery.log" ]; then
                echo "--- CELERY LOG (last 20 lines) ---"
                tail -20 celery.log
            else
                echo "No celery.log found"
            fi
            ;;
        2)
            if [ -f "app.log" ]; then
                echo "--- FLASK APP LOG (last 20 lines) ---"
                tail -20 app.log
            else
                echo "No app.log found"
            fi
            ;;
        *)
            return
            ;;
    esac

    echo ""
    read -p "Press ENTER to return to dashboard..."
}

# Main monitoring loop
main() {
    # Check if running from ZoolZ directory
    if [ ! -f "app.py" ]; then
        echo "❌ Error: Not in ZoolZ directory"
        echo "Please run this from the ZoolZ folder"
        exit 1
    fi

    while true; do
        show_dashboard

        # Wait for user input or timeout
        read -t 5 -n 1 action

        case $action in
            r|R)
                # Refresh immediately
                continue
                ;;
            l|L)
                view_logs
                ;;
            q|Q)
                clear
                echo "👋 Stopping monitor..."
                exit 0
                ;;
            *)
                # Timeout or other key - just refresh
                continue
                ;;
        esac
    done
}

# Run main loop
main
