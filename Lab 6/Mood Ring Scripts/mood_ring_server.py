#!/usr/bin/env python3
"""Mood ring server.

Each Pi publishes a color. This averages every Pi that has checked in
recently and shows the blend at http://<this-machine>:5002

    python mood_ring_server.py
"""

import json
import threading
import time
import uuid

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO

from mood_ring_common import (
    COLOR_TOPIC,
    MQTT_BROKER,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_USERNAME,
)

# A Pi that stops publishing drops out of the average after this long.
STALE_SECONDS = 5

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mood-ring'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

devices = {}
lock = threading.Lock()


def snapshot():
    """Average the Pis that published within STALE_SECONDS."""
    now = time.time()
    with lock:
        stale = [key for key, value in devices.items() if now - value['seen'] > STALE_SECONDS]
        for key in stale:
            del devices[key]
        live = [
            {'id': key, 'r': value['r'], 'g': value['g'], 'b': value['b']}
            for key, value in sorted(devices.items())
        ]

    if not live:
        return {'count': 0, 'average': None, 'devices': []}

    count = len(live)
    average = [
        sum(item['r'] for item in live) // count,
        sum(item['g'] for item in live) // count,
        sum(item['b'] for item in live) // count,
    ]
    return {'count': count, 'average': average, 'devices': live}


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f'[OK] MQTT connected, listening on {COLOR_TOPIC}')
        client.subscribe(COLOR_TOPIC)
    else:
        print(f'[ERROR] MQTT connection failed: {rc}')


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        device_id = str(data.get('id') or data.get('mac') or 'unknown')
        red = max(0, min(255, int(data.get('r', 0))))
        green = max(0, min(255, int(data.get('g', 0))))
        blue = max(0, min(255, int(data.get('b', 0))))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f'[WARN] ignored message: {exc}')
        return

    with lock:
        devices[device_id] = {'r': red, 'g': green, 'b': blue, 'seen': time.time()}

    state = snapshot()
    print(
        f"[OK] {device_id} RGB({red:3d},{green:3d},{blue:3d}) "
        f"-> average {state['average']} from {state['count']} Pi(s)"
    )
    socketio.emit('mood', state)


@app.route('/')
def index():
    return render_template('mood_ring.html')


@app.route('/state')
def state():
    return jsonify(snapshot())


def start_mqtt():
    client = mqtt.Client(str(uuid.uuid1()))
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client


if __name__ == '__main__':
    print('=' * 50)
    print('  Mood Ring')
    print(f'  Open http://0.0.0.0:5002')
    print(f'  Topic {COLOR_TOPIC}')
    print('=' * 50)
    start_mqtt()
    socketio.run(app, host='0.0.0.0', port=5002, debug=False, allow_unsafe_werkzeug=True)
