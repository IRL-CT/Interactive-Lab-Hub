# 3LAS Ultra-Low Latency Audio Scripts

This directory contains automated scripts to set up and run the 3LAS (Low Latency Live Audio Streaming) system with the Magic 8 Ball demo.

## Quick Start

### 🚀 **Start Everything**
```bash
./setup_and_run_3las.sh
```

### 🛑 **Stop Everything**
```bash
./stop_3las.sh
```

## What the Scripts Do

### `setup_and_run_3las.sh`
- Initializes 3LAS git submodule
- Installs Node.js dependencies (ws, wrtc)
- Checks for required audio tools (parecord, netcat)
- Starts 3LAS server with direct audio pipeline
- Starts Flask Magic 8 Ball application
- Provides complete status and access URLs

### `stop_3las.sh`
- Gracefully stops all running services
- Cleans up process IDs and log files
- Kills any remaining processes on ports 5001 and 8080

## Access URLs

After running the setup script:

- **Main Magic 8 Ball**: http://localhost:5001
- **3LAS Ultra-Low Latency**: http://localhost:5001/3las

## Features

✅ **Automated Setup**: One command sets up everything  
✅ **Pi 5 Compatible**: Works with LSM6DS3 sensor and Bluetooth audio  
✅ **Dual Audio Options**: Regular delayed + Ultra-low latency streaming  
✅ **Error Handling**: Comprehensive error checking and logging  
✅ **Clean Shutdown**: Proper process cleanup  

## Audio Pipeline

The script sets up this audio flow:
```
Microphone → parecord → 3LAS Node.js Server → WebSocket/WebRTC → Browser
```

## Troubleshooting

### Check Logs
```bash
# 3LAS server and audio pipeline
cat /tmp/3las_complete.log

# Flask application  
cat /tmp/flask_app.log
```

### Manual Process Check
```bash
ps aux | grep -E "(node|python|parecord)" | grep -v grep
```

### Port Usage
```bash
sudo lsof -i :5001  # Flask app
sudo lsof -i :8080  # 3LAS server
```

## Requirements

- Node.js (for 3LAS server)
- Python virtual environment (for Flask app)
- PulseAudio utilities (parecord)
- Netcat (nc)
- Git (for submodules)

The setup script will automatically install missing dependencies where possible.