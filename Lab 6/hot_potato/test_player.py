"""
Pretend to be one Pi from your laptop (no sensors needed).

    python test_player.py viktor            # join as "viktor" (any free seat)
    python test_player.py ana --seat 3      # ask for seat 3

Then type (and press Enter):
    l / f / r  or  left / forward / right  or the arrow keys  ->  throw
    c  or  catch  or the down arrow                        ->  catch
    s  start,  q  quit
It prints the state the server sends to this player, exactly what a Pi would receive.
Use it to check the server, and as a reference for the real Pi scripts.
"""

import argparse
import json
import os
import time
import uuid

import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_BROKER", "farlab.infosci.cornell.edu")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
BASE = os.environ.get("POTATO_TOPIC", "IDD/hotpotato").rstrip("/")

ap = argparse.ArgumentParser()
ap.add_argument("name", help="player name, e.g. viktor (no spaces or / + #)")
ap.add_argument("--seat", type=int, choices=[1, 2, 3, 4], default=None)
args = ap.parse_args()
NAME = args.name
ACTION_TOPIC = f"{BASE}/player/{NAME}/action"


def make_client():
    cid = f"potato-test-{NAME}-{uuid.uuid4().hex[:6]}"
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=cid)
    except AttributeError:
        return mqtt.Client(client_id=cid)


last = None
last_print = 0.0


def on_connect(client, userdata, flags, rc):
    client.subscribe(f"{BASE}/player/{NAME}/state")
    client.subscribe(f"{BASE}/player/{NAME}/error")
    join = {"action": "join", "input": "keyboard"}
    if args.seat:
        join["seat"] = args.seat
    send(join)


def on_message(client, userdata, msg):
    global last, last_print
    data = json.loads(msg.payload)
    if msg.topic.endswith("/error"):
        print(f"\n  !! rejected: {data['reason']}")
        return
    mode = data.get("mode")
    key = (mode, data.get("caught"), data.get("seat"))
    # print every change, but while holding only every 2 s so you can still type
    if key == last and (mode != "holding" or time.time() - last_print < 2):
        return
    last = key
    last_print = time.time()
    extra = ""
    if mode == "holding":
        extra = f"  heat={data['heat']:.2f}  {data['time_left']:.1f}s left  (round {data['round_left']:.0f}s)"
    elif mode == "incoming":
        extra = f"  from {data['incoming_from']} on your {data['incoming_dir']}" + \
                ("  - got it!" if data["caught"] else "  - press c to CATCH!")
    elif mode == "boom":
        extra = f"  ({data['boom_reason']})"
    print(f"\n  [{NAME} @ seat {data.get('seat')}] {str(mode).upper()}{extra}  "
          f"(booms {data.get('booms', 0)}/{data.get('max_booms', 3)})")


def send(msg):
    client.publish(ACTION_TOPIC, json.dumps(msg))


client = make_client()
client.username_pw_set(os.environ.get("MQTT_USER", "idd"), os.environ.get("MQTT_PASS", "device@theFarm"))
client.will_set(ACTION_TOPIC, json.dumps({"action": "leave"}))   # auto-leave if this script dies
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, keepalive=30)
client.loop_start()

THROW = {"l": "left", "left": "left", "\x1b[d": "left",
         "f": "forward", "forward": "forward", "u": "forward", "up": "forward", "\x1b[a": "forward",
         "r": "right", "right": "right", "\x1b[c": "right"}
CATCH = {"c", "catch", "\x1b[b", "down"}
print(f"{NAME} on {BROKER} -> {ACTION_TOPIC}")
print("throw: l / f / r (or arrows),  catch: c (or down arrow),  s = start,  q = quit  - then Enter")
while True:
    cmd = input("> ").strip().lower()
    if cmd.startswith("\x1b["):
        cmd = cmd[-3:]          # several arrows typed -> use the last one
    if cmd == "q":
        send({"action": "leave"})
        break
    if cmd == "s":
        send({"action": "start"})
    elif cmd in CATCH:
        send({"action": "catch"})
        print("  -> catch!")
    elif cmd in THROW:
        send({"action": "throw", "dir": THROW[cmd]})
        print(f"  -> throwing {THROW[cmd]}")
    elif cmd:
        print("  ?? use l / f / r to throw, c to catch")
client.loop_stop()
