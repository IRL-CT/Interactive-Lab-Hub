#!/usr/bin/env python3
"""Pretend three Pis are online, from this one machine.

    python mood_ring_sim.py

Each name is a separate device on the mood ring. Their colors drift a
little so the average on the server visibly changes. Ctrl+C stops all
three; the server drops them a few seconds later.
"""

import json
import math
import signal
import time
import uuid

import paho.mqtt.client as mqtt

from mood_ring_common import (
    COLOR_TOPIC,
    MQTT_BROKER,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_USERNAME,
)

# name -> base RGB. Phases are spread out so they don't fade in unison.
DEVICES = (
    ('rose', (220, 40, 70), 0.0),
    ('amber', (240, 150, 30), 2.1),
    ('ocean', (30, 70, 220), 4.2),
)


def drifted(base, phase, now):
    wave = 0.65 + 0.35 * math.sin(now * 0.7 + phase)
    return tuple(max(0, min(255, int(channel * wave))) for channel in base)


def main():
    client = mqtt.Client(str(uuid.uuid1()))
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'[OK] connected to {MQTT_BROKER}')
            print(f'Publishing {len(DEVICES)} fake Pis on {COLOR_TOPIC}')
        else:
            print(f'[ERROR] connection failed: {rc}')

    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    deadline = time.time() + 5
    while not client.is_connected() and time.time() < deadline:
        time.sleep(0.1)

    def stop(signum, frame):
        client.loop_stop()
        client.disconnect()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, stop)
    print('Press Ctrl+C to stop the fake Pis')

    while True:
        now = time.time()
        for name, base, phase in DEVICES:
            red, green, blue = drifted(base, phase, now)
            payload = json.dumps({
                'id': name,
                'r': red,
                'g': green,
                'b': blue,
                'timestamp': int(now),
            })
            client.publish(COLOR_TOPIC, payload)
            print(f'[OK] {name:5s} RGB({red:3d},{green:3d},{blue:3d})')
        time.sleep(0.5)


if __name__ == '__main__':
    main()
