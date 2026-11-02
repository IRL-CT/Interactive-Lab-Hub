"""
Part H: the night shift. Log the interpreter's readings all night, headless.
It only senses and logs; the reasoning waits for the morning (morning.py).

    python overnight.py                  # one look every 5 s until Ctrl-C
    python overnight.py --interval 30    # look less often
    python overnight.py --all            # log the other objects too, not only people (see Part E)

Fake a night first: run it for thirty seconds while you walk around, Ctrl-C, then run morning.py.

Writes night_log.jsonl (one JSON object per line) and a snapshot in snaps/ whenever
the reading changes to something other than "nobody". Writes an "alive" line every
10 minutes so you can tell a quiet night from a crashed one.
Start it in tmux or with nohup so it survives the ssh disconnect (see the README).
"""
import argparse
import datetime
import json
import pathlib
import time

import cv2

from yolo_to_qwen import interpret, model      # the interpreter you tuned in Part E

parser = argparse.ArgumentParser()
parser.add_argument("--interval", type=float, default=5, help="seconds between looks")
parser.add_argument("--all", action="store_true", help="detect all 80 classes, not only people")
args = parser.parse_args()
classes = None if args.all else [0]        # class 0 is "person", as in yolo_to_qwen.py

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
pathlib.Path("snaps").mkdir(exist_ok=True)
log = open("night_log.jsonl", "a")
last, last_beat = None, 0.0


def write(entry):
    log.write(json.dumps(entry) + "\n")
    log.flush()


print("night shift started, Ctrl-C to stop", flush=True)
while True:
    try:
        for _ in range(4):          # the webcam buffers a few frames; skip the stale ones
            cap.grab()
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError("no frame")
        r = model.predict(frame, imgsz=320, conf=0.4, classes=classes, verbose=False)[0]
        reading = interpret(r)
        now = datetime.datetime.now()
        ts = now.isoformat(timespec="seconds")
        if reading != last:
            write({"t": ts, "reading": reading})
            if reading != "nobody":
                cv2.imwrite(f"snaps/{now:%Y%m%d-%H%M%S}.jpg", frame)
            last = reading
        if time.time() - last_beat > 600:
            write({"t": ts, "alive": True})
            last_beat = time.time()
        time.sleep(args.interval)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print("hiccup:", e, flush=True)
        time.sleep(args.interval)

cap.release()
print("night shift stopped", flush=True)
