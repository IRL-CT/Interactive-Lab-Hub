#!/bin/bash

# Stop 3LAS services script

echo "🛑 Stopping 3LAS services..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Stop services by PID if files exist
if [ -f /tmp/flask_app.pid ]; then
    FLASK_PID=$(cat /tmp/flask_app.pid)
    if kill -0 $FLASK_PID 2>/dev/null; then
        kill $FLASK_PID
        print_status "Stopped Flask app (PID: $FLASK_PID)"
    fi
    rm -f /tmp/flask_app.pid
fi

if [ -f /tmp/3las_complete.pid ]; then
    THREELAS_AUDIO_PID=$(cat /tmp/3las_complete.pid)
    if kill -0 $THREELAS_AUDIO_PID 2>/dev/null; then
        kill $THREELAS_AUDIO_PID
        print_status "Stopped 3LAS server+audio (PID: $THREELAS_AUDIO_PID)"
    fi
    rm -f /tmp/3las_complete.pid
fi

# Legacy cleanup
if [ -f /tmp/3las_audio.pid ]; then
    AUDIO_PID=$(cat /tmp/3las_audio.pid)
    if kill -0 $AUDIO_PID 2>/dev/null; then
        kill $AUDIO_PID
        print_status "Stopped audio pipeline (PID: $AUDIO_PID)"
    fi
    rm -f /tmp/3las_audio.pid
fi

if [ -f /tmp/3las_server.pid ]; then
    THREELAS_PID=$(cat /tmp/3las_server.pid)
    if kill -0 $THREELAS_PID 2>/dev/null; then
        kill $THREELAS_PID
        print_status "Stopped 3LAS server (PID: $THREELAS_PID)"
    fi
    rm -f /tmp/3las_server.pid
fi

# Forcefully kill any remaining processes
print_status "Cleaning up any remaining processes..."
sudo pkill -f "3las.server.js" || true
sudo pkill -f "parecord.*nc.*8080" || true
sudo pkill -f "app.py" || true

# Kill processes using the ports
sudo lsof -ti:8080 | xargs -r sudo kill -9 || true
sudo lsof -ti:5001 | xargs -r sudo kill -9 || true

# Clean up log files
rm -f /tmp/3las_server.log /tmp/3las_audio.log /tmp/3las_complete.log /tmp/flask_app.log

print_success "All 3LAS services stopped and cleaned up"