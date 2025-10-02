from flask import Flask, Response, render_template
from flask_socketio import SocketIO, send, emit
from subprocess import Popen, call
import threading
import time
import board
import busio
import json
import socket

import signal
import sys
from queue import Queue

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
hardware = 'plughw:2,0'

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
audio_stream = Popen("/usr/bin/cvlc alsa://"+hardware+" --sout='#transcode{vcodec=none,acodec=mp3,ab=256,channels=2,samplerate=44100,scodec=none}:http{mux=mp3,dst=:8080/}' --no-sout-all --sout-keep", shell=True)

@socketio.on('speak')
def handel_speak(val):
    call(f"espeak '{val}'", shell=True)

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
    audio_stream.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)


