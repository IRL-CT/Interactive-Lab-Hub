#!/usr/bin/env python3
"""
Publish this Pi's self-description as a retained MQTT message.

    python describe.py bathroom.json          # announce
    python describe.py bathroom.json --remove # take the description down

The broker keeps the last retained message on a topic and hands it to anyone
who subscribes later, so other devices can discover this one at any time.
"""

import json
import sys

from common import connect

path = sys.argv[1]
with open(path) as f:
    desc = json.load(f)

topic = f"IDD/{desc['team']}/devices/{desc['name']}"
payload = '' if '--remove' in sys.argv else json.dumps(desc)

client = connect()
client.loop_start()
client.publish(topic, payload, qos=1, retain=True).wait_for_publish()
client.loop_stop()
client.disconnect()
print(('Removed ' if not payload else 'Published ') + topic)
