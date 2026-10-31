#!/usr/bin/env python3
"""
Run a rule from rule.json over MQTT. No language model involved.

    python run_rule.py [rule.json]
"""

import json
import sys
import time

from common import connect

with open(sys.argv[1] if len(sys.argv) > 1 else 'rule.json') as f:
    rule = json.load(f)

when, then = rule['when'], rule['then']
cooldown = rule.get('cooldown_seconds') or 0
last_fired = 0.0


def on_message(client, userdata, msg):
    global last_fired
    value = msg.payload.decode(errors='replace')
    if when.get('equals') is not None and value != str(when['equals']):
        return
    if time.time() - last_fired < cooldown:
        return
    last_fired = time.time()
    client.publish(then['topic'], then['message'])
    print(f"{time.strftime('%H:%M:%S')}  {msg.topic}={value!r}  ->  {then['topic']}={then['message']!r}")


client = connect()
client.on_message = on_message
client.subscribe(when['topic'])
print('Running: ' + rule.get('explanation', ''))
client.loop_forever()
