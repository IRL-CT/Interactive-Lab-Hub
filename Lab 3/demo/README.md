# 🧙‍♂️ Magic 8 Ball - Wizard of Oz Interface

This is a **Wizard of Oz interactive system** where you (the wizard) control a Magic 8 Ball experience. The user thinks they're interacting with a magical device, but you're secretly controlling all the responses!

<img src='https://images-na.ssl-images-amazon.com/images/I/71729uRDw2L._AC_SY606_.jpg' width=200>

## 🚀 Quick Start (Automated Setup)

**New! Use our automated scripts for easy setup:**

```bash
# One command to set up and run everything
./setup_and_run_3las.sh

# To stop all services
./stop_3las.sh
```

For manual setup instructions, see the [Manual Setup](#manual-setup) section below.

## 🔧 Hardware Setup

You'll need:
* **Raspberry Pi** (Pi 5 recommended) 
* **Qwiic/Stemma Cable**
* **Display** (for Qwiic/StemmaQT port)
* **Accelerometer**: LSM6DS3 (Pi 5+) or MSA311/MPU6050 (older)
* **Bluetooth Speaker** (paired with Pi)
* **USB Microphone** (for eavesdropping - Bluetooth speakers typically don't have mics)

**Hardware Compatibility by Class Year:**
- **Fall 2026+**: Pi 5, Bluetooth speakers, LSM6DS3 accelerometer
- **Fall 2025**: USB webcam with microphone, LSM6DS3 accelerometer  
- **Earlier years**: USB webcam with microphone, MSA311 or MPU6050 accelerometer

<p float="left">
<img src="https://cdn-learn.adafruit.com/assets/assets/000/082/842/large1024/adafruit_products_4393_iso_ORIG_2019_10.jpg" height="200" />
<img src="https://github.com/adafruit/Adafruit_MPU6050/raw/master/assets/board.jpg?raw=true" height="200" />
</p>

**Connection Steps:**
1. Plug the display into your Pi
2. Connect the accelerometer to the port underneath with your Qwiic cable
3. Plug the USB microphone into the Pi
4. Ensure Bluetooth speaker is paired

## ⚡ Audio Options Available

### 1. **Standard Audio Streaming**
- ~2-3 second delay
- Works in any browser
- More compatible but higher latency

### 2. **Ultra-Low Latency (3LAS)**
- <50ms delay for real-time audio
- Requires Chrome browser
- Uses WebRTC for instant streaming

## 🎭 Wizard Interface Features

### **Side-by-Side Sensor Monitoring**
- **📊 Accelerometer Data**: Watch for device shaking
- **🎵 Live Audio Waveform**: Real-time microphone visualization

### **🧙‍♂️ Wizard Control Panel**
- Type responses for the Magic 8 Ball to "say"
- Send audio directly to user's speakers
- Built-in tips for classic Magic 8 Ball responses
![interface](<interface-8ball.png>)
### **🎧 Eavesdropping Options**
- Choose your preferred audio streaming method
- Monitor what the user is saying in real-time
![eavesdropping options](<eavesdropping.png>)
## 📋 Requirements Installation

### Automated Method (Recommended)
The setup script handles **everything automatically**:
- ✅ Creates Python virtual environment (`.venv`)
- ✅ Installs all Python requirements from `requirements.txt`
- ✅ Initializes 3LAS git submodule
- ✅ Installs Node.js dependencies
- ✅ Checks and installs system tools (parecord, netcat)

```bash
./setup_and_run_3las.sh
```

**No manual setup required!** The script will create the virtual environment and install all dependencies automatically.

### Manual Method (If Needed)
If you prefer manual setup or the script doesn't work:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv pulseaudio-utils netcat nodejs npm

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python requirements
pip install -r requirements.txt

# Initialize 3LAS submodule (if not done automatically)
git submodule add https://github.com/JoJoBond/3LAS.git 3LAS
git submodule update --init --recursive

# Install Node.js dependencies for 3LAS
cd 3LAS/example/server
npm install
```

## 🏃‍♂️ Running the System

### Option 1: Automated (Recommended)
```bash
./setup_and_run_3las.sh
```

### Option 2: Manual
```bash
# Terminal 1: Start 3LAS server with audio
cd 3LAS/example/server
parecord --channels=1 --rate=22050 --format=s16le --raw | node 3las.server.js -port 8080 -channels 1 -samplerate 22050

# Terminal 2: Start Flask app
source .venv/bin/activate
python app.py
```

## 🌐 Access URLs

- **Wizard Interface**: http://localhost:5001 (or http://yourHostname.local:5001)
- **Ultra-Low Latency Audio**: http://localhost:5001/3las

## 🎪 How to Use as Wizard

1. **👂 Start Eavesdropping**: Click "Standard Audio Stream" to hear the user
2. **👀 Monitor Sensors**: Watch accelerometer for shaking, audio for speaking  
3. **🎭 Wait for Interaction**: User asks question and shakes device
4. **💬 Respond**: Type Magic 8 Ball response in control panel
5. **📤 Send**: Click "Send Audio Response" - user hears it as the Magic 8 Ball!

## 🎱 Classic Magic 8 Ball Responses

**Positive**: "Yes, definitely", "It is certain", "Without a doubt"  
**Negative**: "Don't count on it", "My sources say no", "Very doubtful"  
**Neutral**: "Ask again later", "Reply hazy, try again", "Cannot predict now"

## 🛠️ Manual Setup

If you prefer to set up everything manually or the automated script doesn't work:

### System Dependencies
```bash
sudo apt-get update
sudo apt-get install pulseaudio-utils netcat nodejs npm git
```

### Audio Configuration
```bash
# Configure audio output (if needed)
sudo raspi-config
# Navigate to: System Options > Audio > Select your audio output
```

### Python Environment
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3LAS Submodule Setup
```bash
# Initialize 3LAS submodule (if not already done)
git submodule add https://github.com/JoJoBond/3LAS.git 3LAS
git submodule update --init --recursive

# Install Node.js dependencies
cd 3LAS/example/server
npm install ws wrtc node-pre-gyp
cd ../../..
```

### Manual Start Services
```bash
# Terminal 1: 3LAS Server with Audio Pipeline
cd 3LAS/example/server
parecord --channels=1 --rate=22050 --format=s16le --raw | node 3las.server.js -port 8080 -channels 1 -samplerate 22050

# Terminal 2: Flask Application
source .venv/bin/activate
python app.py
```

## 🔧 Troubleshooting

### Common Issues

**"3LAS submodule not found"**
```bash
git submodule update --init --recursive
```

**"parecord command not found"** 
```bash
sudo apt-get install pulseaudio-utils
```

**"Node.js dependencies missing"**
```bash
cd 3LAS/example/server
npm install
```

**"Permission denied on scripts"**
```bash
chmod +x setup_and_run_3las.sh stop_3las.sh
```

### Check Service Status
```bash
# Check if services are running
ps aux | grep -E "(node|python)" | grep -v grep

# Check port usage
sudo lsof -i :5001  # Flask app
sudo lsof -i :8080  # 3LAS server
```

### View Logs
```bash
# Service logs (when using automated scripts)
cat /tmp/3las_complete.log    # 3LAS server and audio
cat /tmp/flask_app.log        # Flask application
```

## 📚 Additional Documentation

- **[3LAS Scripts Guide](3LAS_SCRIPTS_README.md)**: Detailed script documentation
- **[Wizard Guide](WIZARD_OF_OZ_GUIDE.md)**: Complete wizard operation manual
- **[Interface Improvements](INTERFACE_IMPROVEMENTS.md)**: Latest UI changes and features

## 🎯 Pro Tips

- **Timing**: Wait for natural pauses after shaking before responding
- **Variety**: Mix positive, negative, and neutral responses
- **Chrome Browser**: Use Chrome for best 3LAS performance
- **Audio Quality**: USB microphones work better than built-in mics

---

**Remember**: The user doesn't know you exist! Make the magic believable! 🪄

