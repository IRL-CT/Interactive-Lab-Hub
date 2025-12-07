# 🎶 LumiTune — Interactive Time-Machine Music Box

LumiTune is an interactive music box that blends physical sensing, gesture control, MQTT messaging, and a modern web interface. Inspired by traditional mechanical music boxes, LumiTune lets users explore music across decades while the environment sets the mood.

---

## 📌 Overview

LumiTune combines:

- **Decade selection** (1950s–2020s)
- **Environment-based genre detection** using a color + brightness sensor
- **Gesture controls** for playback
- **Rotary encoder movement modes**
- **A web controller** built with React + MQTT over WebSockets

It runs on a Raspberry Pi and supports custom MP3 files grouped by decade and genre.

---

## ✨ Features

### 🕰 1. Time-Machine Decade Selector
Users choose a decade (e.g., 1980s or 2000s). The backend selects a random track from that decade + genre.

### 🌈 2. Environment-Based Genre Detection
Ambient light determines the genre:

| Lighting Condition                        | Genre |
|-------------------------------------------|-------|
| Very dim light                            | Chill |
| Extremely bright lighting                 | Party |
| Moderate light + warm color temperature   | Warm |
| Moderate light + neutral/cool tone        | Energetic |

Switching occurs only when the environment remains stable for several seconds.

### ✋ 3. Gesture Playback Control
Using APDS9960:

| Gesture | Action |
|---------|--------|
| Up      | Volume up |
| Down    | Volume down |
| Left    | Previous track |
| Right   | Next track |
| Hold hand still | Pause/Play |

### 🎛 4. Rotary Encoder Movement Modes
Controls the decorative music box figurine:

- SPIN LEFT
- SPIN RIGHT  

### 📱 5. Web Controller (React + MQTT)
Users can remotely control:

- Decade
- Genre (override)
- Volume
- Playback requests

The UI communicates with the Pi via MQTT over WebSockets.

---

## 🗂 Project Structure

```
Project/
│
├── backend/
│ ├── mqtt_musicbox.py # Handles MQTT messages + decade/genre playback
│ ├── sensor_musicbox.py # Handles environment detection, gestures, servo
│ ├── init.py
│ └── requirements.txt
│
├── LumiTune-webpage/ # React/Vite frontend controller
│ ├── src/
│ │ ├── App.tsx
│ │ ├── main.tsx
│ ├── public/
│ │ ├── config.js # Defines PI_IP + WS_PORT
│ └── package.json
│
├── music/ # MP3 files (named by decade + genre)
│
└── README.md
```

---

## 🛠 Setup Instructions

### 1. Install system dependencies (audio + MQTT + TTS)
```bash
sudo apt update
sudo apt install mpg123 espeak mosquitto
```

### 2. Install Python dependencies

Backend (MQTT only):
```
pip install -r backend/requirements.txt
```
Sensor dependencies:
```
pip install pygame adafruit-blinka adafruit-circuitpython-apds9960 adafruit-circuitpython-seesaw adafruit-circuitpython-servokit
```

### 3. Start MQTT broker
```
sudo systemctl start mosquitto
```

## ▶️ Running the Backend

### **A. MQTT Controller**
Handles decade/genre playback requests.

```bash
python3 backend/mqtt_musicbox.py
```

### **B. Sensor Controller**

Handles gestures, light sensing, playlist switching, and servo movement.

```bash
python3 backend/sensor_musicbox.py
```

## 🌐 Running the Web Controller

### Navigate into the frontend folder:

```bash
cd LumiTune-webpage
npm i
npm run dev -- --host
```

Access the UI from any device on the same network:

```
http://<pi-ip>:3000/
```

Ensure the WebSocket config is correct in public/config.js:

```javascript
window.MUSICBOX_CONFIG = {
  PI_IP: "10.xx.xx.xx",
  WS_PORT: 9001
};
```

