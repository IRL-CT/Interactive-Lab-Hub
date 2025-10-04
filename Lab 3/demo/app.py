import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from subprocess import call

import socket
import signal
import sys

import qwiic_joystick 

joystick = qwiic_joystick.QwiicJoystick()
if not joystick.connected:
    print("Joystick not connected! Please check wiring (SDA/SCL).")
else:
    joystick.begin()
    print("Joystick connected successfully.")

hostname = socket.gethostname()

# Flask + SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

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
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    print("Starting Flask + Joystick server at port 5000...")
    socketio.run(app, host='0.0.0.0', port=5000)
