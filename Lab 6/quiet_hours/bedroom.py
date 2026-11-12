"""
Bedroom Pi (mine): decides whether I'm asleep and tells the other two Pis.

    python bedroom.py              # MPR121 pad 0 + PiTFT
    python bedroom.py --camera     # also watch the bed with YOLO and wake up the house when I get up
    python bedroom.py --fake       # no hardware: Enter = tap, screen goes to the terminal

Input:  a tap on the touch pad by the bed means "going to sleep" (or, in the morning, "I'm up").
        With --camera, if YOLO sees nobody in bed for --away minutes while I'm "asleep",
        the Pi decides I got up and switches to awake by itself, so I can't forget to tap.
Output: publishes IDD/quiethours/bedroom/state (retained) for the other Pis.
        While I'm asleep the screen stays black and just counts knocks and loud moments.
        When I switch to awake it shows what happened overnight.
"""
import argparse
import threading
import time

import common

parser = argparse.ArgumentParser()
parser.add_argument("--fake", action="store_true", help="no hardware; Enter = tap")
parser.add_argument("--camera", action="store_true", help="watch the bed with YOLO")
parser.add_argument("--model", default="../../Lab 5/yolo26n_ncnn_model", help="the Lab 5 YOLO export")
parser.add_argument("--conf", type=float, default=0.5, help="person confidence (0.5 worked on my bed in Lab 5)")
parser.add_argument("--away", type=float, default=3, help="minutes out of bed before I count as awake")
args = parser.parse_args()

screen = common.Screen(fake=args.fake)
state = "awake"
since = common.now()
knocks, louds = [], []          # what happened while I was asleep


def draw():
    if state == "asleep":
        screen.show("", "", bg=(0, 0, 0))
    else:
        screen.show("Awake", "Tap the pad when\nyou go to sleep", bg=(0, 90, 40))


def on_message(topic, msg):
    global state, since
    if topic == common.STATE:
        # Retained copy from before a restart: pick up where we left off.
        if msg.get("state") in ("asleep", "awake") and msg.get("since"):
            state, since = msg["state"], msg["since"]
            draw()
        return
    if state == "asleep":
        if topic == common.KNOCK:
            knocks.append(msg.get("t", common.now()))
        elif topic == common.LOUD:
            louds.append(msg.get("t", common.now()))
        return                  # don't light up the screen at night
    if topic == common.KNOCK:
        screen.show("Door", "Someone knocked", bg=(0, 60, 140))
        threading.Timer(4, draw).start()     # don't block the MQTT thread


client = common.connect("bedroom", on_message, subscribe=[common.STATE, common.KNOCK, common.LOUD])
time.sleep(1.5)                 # let the retained state arrive first
client.unsubscribe(common.STATE)  # after that, this Pi is the only one who sets it


def set_state(new, source):
    global state, since
    if new == state:
        return
    state, since = new, common.now()
    common.send(client, common.STATE, {"state": state, "since": since, "source": source}, retain=True)
    print(f"{since}  {state} ({source})")
    if state == "asleep":
        knocks.clear()
        louds.clear()
        screen.show("Goodnight", "Quiet hours are on", bg=(40, 0, 60))
        time.sleep(3)
        draw()
    else:
        last = f", last {knocks[-1][11:16]}" if knocks else ""
        screen.show("Morning", f"{len(knocks)} knock(s){last}\n{len(louds)} loud moment(s)", bg=(140, 90, 0))
        time.sleep(10)
        draw()


common.touch_pad(lambda: set_state("awake" if state == "asleep" else "asleep", "tap"), fake=args.fake)
draw()


def watch_bed():
    """Switch to awake once nobody has been in bed for --away minutes."""
    import cv2
    from ultralytics import YOLO
    model = YOLO(args.model)
    cap = cv2.VideoCapture(0)
    last_seen = time.time()
    while True:
        ok, frame = cap.read()
        if ok and state == "asleep":
            r = model.predict(frame, imgsz=320, conf=args.conf, classes=[0], verbose=False)[0]
            if len(r.boxes):
                last_seen = time.time()
            elif time.time() - last_seen > args.away * 60:
                set_state("awake", "camera")
        if state == "awake":
            last_seen = time.time()   # the clock only runs while I'm asleep
        time.sleep(5)


try:
    if args.camera:
        watch_bed()
    else:
        while True:
            time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    common.goodbye(client, "bedroom")
