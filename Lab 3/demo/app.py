import eventlet
eventlet.monkey_patch()

from flask import Flask, Response, render_template
from flask_socketio import SocketIO, send, emit
from subprocess import Popen, call

import time
import json
import socket
import signal
import sys
from queue import Queue

import qwiic_joystick 

joystick = qwiic_joystick.QwiicJoystick()
if not joystick.connected:
    print("Joystick not connected! Please check wiring (SDA/SCL).")
else:
    joystick.begin()
    print("Joystick connected successfully.")


hostname = socket.gethostname()
hardware = 'plughw:2,0'

app = Flask(__name__)
socketio = SocketIO(app)

audio_stream = Popen(
    f"/usr/bin/cvlc alsa://{hardware} "
    "--sout='#transcode{vcodec=none,acodec=mp3,ab=256,channels=2,"
    "samplerate=44100,scodec=none}:http{mux=mp3,dst=:8080/}' "
    "--no-sout-all --sout-keep",
    shell=True
)


@socketio.on('speak')
def handle_speak(val):
    print(f"Speaking: {val}")
    call(f"espeak '{val}'", shell=True)


@socketio.on('connect')
def test_connect():
    print('Client connected')
    emit('after connect', {'data': 'Joystick ready!'})


@socketio.on('ping-gps')
def handle_message(val):
    joystick.horizontal
    joystick.vertical
    joystick.button

    data = {
        'horizontal': joystick.horizontal,
        'vertical': joystick.vertical,
        'button': joystick.button
    }

    emit('pong-gps', data)

@app.route('/')
def index():
    return render_template('index.html', hostname=hostname)


def signal_handler(sig, frame):
    print('Closing Gracefully')
    audio_stream.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    print("Starting Flask + Joystick server at port 5000...")
    socketio.run(app, host='0.0.0.0', port=5000)

