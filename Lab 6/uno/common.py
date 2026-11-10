"""MQTT settings shared by the referee and the players"""

import re
import uuid

import paho.mqtt.client as mqtt

MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'


def valid_name(name):
    """Names end up in topics, so no spaces or MQTT wildcards"""
    return re.fullmatch(r'[A-Za-z0-9_-]{1,10}', name) is not None


class Topics:
    def __init__(self, team):
        self.root = f'IDD/{team}/uno'
        self.join = f'{self.root}/join'
        self.state = f'{self.root}/state'

    def hand(self, name):
        return f'{self.root}/hand/{name}'

    def action(self, name):
        return f'{self.root}/action/{name}'

    def notice(self, name):
        return f'{self.root}/notice/{name}'


def connect(on_message, subscriptions):
    """Connect in the background. Subscribes again by itself after a reconnect."""
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'[OK] MQTT connected to {MQTT_BROKER}:{MQTT_PORT}')
            for topic in subscriptions:
                client.subscribe(topic, qos=1)
        else:
            print(f'[ERROR] MQTT connection failed: {rc}')

    client = mqtt.Client(str(uuid.uuid1()))
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=30)
    client.loop_start()
    return client
