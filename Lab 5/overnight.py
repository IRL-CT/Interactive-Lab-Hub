"""
Part H: the night shift. Log the interpreter's readings all night, headless.
It only senses and logs; the reasoning waits for the morning (morning.py).

    python overnight.py                  # one look every 5 s until Ctrl-C
    python overnight.py --interval 30    # look less often
    python overnight.py --all            # log the other objects too, not only people (see Part E)
    python overnight.py --no-snaps       # words only: do not keep a photo when someone gets up

Fake a night first: run it for thirty seconds while you walk around, Ctrl-C, then run morning.py.

Writes night_log.jsonl (one JSON object per line): words, plus one photo in snaps/ each time
the reading turns "upright" (switch that off with --no-snaps). Nothing is photographed while the
person lies down. Tell the people you live with, keep snaps/ out of git, and delete it after the demo.
A reading is logged once it has been seen --confirm looks in a row, so one blurry frame
does not make an entry. Writes an "alive" line every 10 minutes so you can tell a quiet
night from a crashed one.
Start it in tmux or with nohup so it survives the ssh disconnect (see the README).
"""
import argparse
import datetime
import json
import pathlib
import time

import cv2

from screen import Screen
from yolo_to_qwen import interpret, model      # the interpreter you tuned in Part E

parser = argparse.ArgumentParser()
parser.add_argument("--interval", type=float, default=5, help="seconds between looks")
parser.add_argument("--all", action="store_true", help="detect all 80 classes, not only people")
parser.add_argument("--snaps", action=argparse.BooleanOptionalAction, default=True,
                    help="keep a photo each time someone gets up (default on; --no-snaps for words only)")
parser.add_argument("--conf", type=float, default=0.3, help="minimum confidence; lower than by day because the room is dark")
parser.add_argument("--confirm", type=int, default=2, help="looks in a row before a new reading is logged")
args = parser.parse_args()
classes = None if args.all else [0]        # class 0 is "person", as in yolo_to_qwen.py

screen = Screen()          # the Mini PiTFT stays dark all night (stop piscreen.service first, see screen.py)
screen.off()
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if args.snaps:
    pathlib.Path("snaps").mkdir(exist_ok=True)
log = open("night_log.jsonl", "a")
last, last_beat = None, 0.0
candidate, seen_in_a_row = None, 0


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
        r = model.predict(frame, imgsz=320, conf=args.conf, classes=classes, verbose=False)[0]
        reading = interpret(r)
        now = datetime.datetime.now()
        ts = now.isoformat(timespec="seconds")
        seen_in_a_row = seen_in_a_row + 1 if reading == candidate else 1
        candidate = reading
        if seen_in_a_row >= args.confirm and reading != last:
            write({"t": ts, "reading": reading})
            if args.snaps and "upright" in reading and "upright" not in (last or ""):
                cv2.imwrite(f"snaps/{now:%Y%m%d-%H%M%S}.jpg", frame)       # a photo as the person gets up
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
screen.text("Good morning", "Run morning.py", color="#FFFF00")
print("night shift stopped", flush=True)
