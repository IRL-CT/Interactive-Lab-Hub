#!/bin/bash

# 3LAS Ultra-Low Latency Audio Setup and Run Script
# This script sets up and runs the complete 3LAS audio streaming system

set -e  # Exit on any error

echo "🎵 3LAS Ultra-Low Latency Audio Setup & Run Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$SCRIPT_DIR"
THREELAS_DIR="$DEMO_DIR/3LAS"
SERVER_DIR="$THREELAS_DIR/example/server"

print_status "Working directory: $DEMO_DIR"

# Step 1: Check and initialize 3LAS submodule
print_status "Step 1: Checking 3LAS submodule..."
if [ ! -d "$THREELAS_DIR" ] || [ ! -f "$THREELAS_DIR/README.md" ]; then
    print_warning "3LAS submodule not found or incomplete. Initializing..."
    cd "$DEMO_DIR"
    git submodule add https://github.com/JoJoBond/3LAS.git 3LAS || true
    git submodule update --init --recursive
    print_success "3LAS submodule initialized"
else
    print_success "3LAS submodule already exists"
fi

# Step 2: Install Node.js dependencies
print_status "Step 2: Installing Node.js dependencies..."
cd "$SERVER_DIR"

if [ ! -f "package.json" ]; then
    print_status "Creating package.json..."
    cat > package.json << 'EOF'
{
  "dependencies": {
    "node-pre-gyp": "^0.17.0",
    "wrtc": "^0.4.7",
    "ws": "^8.18.3"
  }
}
EOF
fi

if [ ! -d "node_modules" ]; then
    print_status "Installing npm dependencies..."
    npm install
    print_success "Node.js dependencies installed"
else
    print_success "Node.js dependencies already installed"
fi

# Step 3: Check for required audio tools
print_status "Step 3: Checking audio tools..."
if ! command -v parecord &> /dev/null; then
    print_error "parecord not found. Installing pulseaudio-utils..."
    sudo apt-get update
    sudo apt-get install -y pulseaudio-utils
fi

if ! command -v nc &> /dev/null; then
    print_error "netcat not found. Installing netcat..."
    sudo apt-get install -y netcat
fi

print_success "Audio tools ready"

# Step 4: Kill any existing processes
print_status "Step 4: Cleaning up existing processes..."
sudo pkill -f "3las.server.js" || true
sudo pkill -f "parecord.*nc.*8080" || true
sudo lsof -ti:8080 | xargs -r sudo kill -9 || true
sudo lsof -ti:5001 | xargs -r sudo kill -9 || true
sleep 2
print_success "Cleaned up existing processes"

# Step 5: Start 3LAS server
print_status "Step 5: Starting 3LAS Node.js server..."
cd "$SERVER_DIR"

# Start 3LAS server in background
nohup node 3las.server.js -port 8080 -channels 1 -samplerate 22050 > /tmp/3las_server.log 2>&1 &
THREELAS_PID=$!
sleep 2

# Check if server started successfully
if kill -0 $THREELAS_PID 2>/dev/null; then
    print_success "3LAS server started (PID: $THREELAS_PID)"
    echo $THREELAS_PID > /tmp/3las_server.pid
else
    print_error "Failed to start 3LAS server"
    cat /tmp/3las_server.log
    exit 1
fi

# Step 6: Start 3LAS server with audio pipeline
print_status "Step 6: Starting 3LAS server with audio pipeline..."

# Kill the previous server that was started without audio
kill $THREELAS_PID 2>/dev/null || true
rm -f /tmp/3las_server.pid

# Start 3LAS server with audio pipeline directly
nohup bash -c "parecord --channels=1 --rate=22050 --format=s16le --raw | node 3las.server.js -port 8080 -channels 1 -samplerate 22050" > /tmp/3las_complete.log 2>&1 &
THREELAS_AUDIO_PID=$!
sleep 3

# Check if the combined server+audio started successfully
if kill -0 $THREELAS_AUDIO_PID 2>/dev/null; then
    print_success "3LAS server with audio pipeline started (PID: $THREELAS_AUDIO_PID)"
    echo $THREELAS_AUDIO_PID > /tmp/3las_complete.pid
else
    print_error "Failed to start 3LAS server with audio pipeline"
    cat /tmp/3las_complete.log
    exit 1
fi

# Step 7: Start Flask app
print_status "Step 7: Starting Flask Magic 8 Ball app..."
cd "$DEMO_DIR"

# Activate virtual environment and start Flask
nohup bash -c "source .venv/bin/activate && python app.py" > /tmp/flask_app.log 2>&1 &
FLASK_PID=$!
sleep 3

# Check if Flask started successfully
if kill -0 $FLASK_PID 2>/dev/null; then
    print_success "Flask app started (PID: $FLASK_PID)"
    echo $FLASK_PID > /tmp/flask_app.pid
else
    print_error "Failed to start Flask app"
    cat /tmp/flask_app.log
    exit 1
fi

# Step 8: Display status and URLs
print_success "🎉 All services started successfully!"
echo ""
echo "📱 Access URLs:"
echo "   Main Magic 8 Ball:     http://localhost:5001"
echo "   3LAS Ultra-Low Latency: http://localhost:5001/3las"
echo ""
echo "🔧 Service Information:"
echo "   3LAS Server+Audio PID: $THREELAS_AUDIO_PID (Port 8080)"
echo "   Flask App PID:    $FLASK_PID (Port 5001)"
echo ""
echo "📋 Log Files:"
echo "   3LAS Complete:  /tmp/3las_complete.log"
echo "   Flask App:     /tmp/flask_app.log"
echo ""
echo "🛑 To stop all services, run:"
echo "   ./stop_3las.sh"
echo ""
print_success "Setup complete! Try the 3LAS client in Chrome at: http://localhost:5001/3las"