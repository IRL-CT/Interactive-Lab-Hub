from flask import Flask, Response, render_template
from flask_socketio import SocketIO, send, emit
from subprocess import Popen, call, PIPE
import threading
import time
import board
import busio
import json
import socket
import struct
import signal
import sys

# Sensor imports - uncomment the one you're using
# For Fall 2025+ (Pi 5 compatible):
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
# For earlier years:
# from adafruit_msa3xx import MSA311
# import adafruit_mpu6050

i2c = board.I2C()  # Pi 5 compatible
# i2c = busio.I2C(board.SCL, board.SDA)  # Alternative for older setups

# Initialize sensor - uncomment the one you're using
sensor = LSM6DS3(i2c)  # Fall 2025+
# sensor = MSA311(i2c)  # Earlier years
# sensor = adafruit_mpu6050.MPU6050(i2c)  # MPU6050 users

hostname = socket.gethostname()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Audio streaming - simple approach using parecord
audio_streaming = False
audio_thread = None

def stream_audio():
    """Stream audio data in real-time using parecord"""
    global audio_streaming
    
    # Use parecord (PulseAudio) to capture audio in small chunks
    # Format: 16-bit mono, 22050 Hz, capture 0.1 second chunks
    cmd = ['parecord', '--format=s16le', '--rate=22050', '--channels=1', '--raw']
    
    try:
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        print("Audio streaming: Started parecord for real-time audio capture")
        
        chunk_size = 2205  # 0.1 seconds at 22050 Hz, 16-bit samples
        
        while audio_streaming:
            # Read audio chunk
            audio_data = process.stdout.read(chunk_size * 2)  # 2 bytes per sample
            
            if len(audio_data) == chunk_size * 2:
                # Convert to integers for visualization
                audio_samples = struct.unpack(f'{chunk_size}h', audio_data)
                # Send a subset for visualization (every 10th sample to reduce data)
                audio_viz = audio_samples[::10]
                socketio.emit('audio-data', list(audio_viz))
            
            time.sleep(0.05)  # Small delay to prevent overwhelming
            
    except Exception as e:
        print(f"Audio streaming error: {e}")
    finally:
        if 'process' in locals():
            process.terminate()
        print("Audio streaming stopped")

@socketio.on('speak')
def handel_speak(val):
    # Use pulseaudio for Bluetooth speaker output
    call(f"espeak '{val}' --stdout | paplay", shell=True)

@socketio.on('start-audio')
def start_audio():
    global audio_streaming, audio_thread
    if not audio_streaming:
        audio_streaming = True
        audio_thread = threading.Thread(target=stream_audio)
        audio_thread.daemon = True
        audio_thread.start()
        emit('audio-status', {'status': 'started'})
        print("Audio streaming started")

@socketio.on('stop-audio')
def stop_audio():
    global audio_streaming
    audio_streaming = False
    emit('audio-status', {'status': 'stopped'})
    print("Audio streaming stopped")

@socketio.on('connect')
def test_connect():
    print('connected')
    emit('after connect',  {'data':'Lets dance'})

@socketio.on('ping-gps')
def handle_message(val):
    # Get acceleration data (works for LSM6DS3, MSA311, and MPU6050)
    accel_data = sensor.acceleration
    emit('pong-gps', accel_data) 



@app.route('/')
def index():
    return render_template('index.html', hostname=hostname)

def signal_handler(sig, frame):
    print('Closing Gracefully')
    global audio_streaming
    audio_streaming = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5001)


