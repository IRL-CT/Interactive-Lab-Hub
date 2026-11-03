"""Shared MQTT settings for the self-describing devices stretch exercise."""

import json
import time

import paho.mqtt.client as mqtt

MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'


def connect():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    return client


def read_descriptions(team, wait=2.0):
    """Collect every device description retained under IDD/<team>/devices/#."""
    found = {}

    def on_message(client, userdata, msg):
        if not msg.payload:  # an empty retained message means "removed"
            return
        try:
            found[msg.topic] = json.loads(msg.payload)
        except ValueError:
            print(f"Skipping {msg.topic}: not JSON")

    client = connect()
    client.on_message = on_message
    client.subscribe(f'IDD/{team}/devices/#')
    client.loop_start()
    time.sleep(wait)  # retained messages arrive right after subscribing
    client.loop_stop()
    client.disconnect()
    return list(found.values())
