"""
Part H, my version of overnight.py: log where I am in bed every few seconds, all night.

    python restless_night.py                  # one look every 5 s until Ctrl-C
    python restless_night.py --interval 10    # look less often
    python restless_night.py --seconds 30     # fake night: stop by itself after 30 s
    python restless_night.py --no-wave        # start right away instead of waiting for a wave
    python restless_night.py --settle 10      # start watching 10 s after the wave instead of 2 min

The hand-off: the script waits until I wave at the camera (an open hand moving side to
side, using MediaPipe hands from Part C), says goodnight, and gives me --settle seconds
to get into bed. Otherwise walking to bed would be logged as restlessness.

overnight.py only logs when the reading changes, and the reading is "1 person(s), close"
all night when I am lying in bed, so it can't see me turning over. This logs the
person's box on every look instead, and restless_morning.py decides afterwards what
counts as a move. That way the threshold can be tuned on a real night without
running it again.

No snapshots are saved: the camera points at a bed, so only box coordinates
are kept. Writes restless_log.jsonl, one JSON object per look:
    {"t": "2026-10-27T01:12:05", "box": [x1, y1, x2, y2]}   # fractions of the frame, 0 to 1
    {"t": "2026-10-27T01:12:10", "box": null}               # nobody in view
    {"t": "2026-10-27T00:58:40", "handoff": "wave"}         # once, when I waved goodnight
"""
import argparse
import collections
import datetime
import json
import time

import cv2
import mediapipe as mp

from yolo_to_qwen import model      # the same NCNN YOLO as Part E

parser = argparse.ArgumentParser()
parser.add_argument("--interval", type=float, default=5, help="seconds between looks")
parser.add_argument("--seconds", type=float, default=None, help="stop after this long (fake nights)")
parser.add_argument("--out", default="restless_log.jsonl")
parser.add_argument("--no-wave", action="store_true", help="skip the wave hand-off")
parser.add_argument("--settle", type=float, default=120, help="seconds after the wave before watching starts")
args = parser.parse_args()

WAVE_SIZE = 0.08       # the wrist has to swing this far (fraction of the frame width) to count
WAVE_WINDOW = 3.0      # seconds; the swings have to happen within this long
WAVE_TURNS = 2         # direction changes: left-right-left is 2

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
log = open(args.out, "a")


def write(entry):
    log.write(json.dumps(entry) + "\n")
    log.flush()


def biggest_person(r):
    """The largest person box as fractions of the frame, or None. The biggest one is me in bed;
    anything smaller is a far-off false detection or someone in the doorway."""
    h, w = r.orig_shape
    best, best_area = None, 0
    for box in r.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        area = (x2 - x1) * (y2 - y1)
        if area > best_area:
            best, best_area = [round(x1 / w, 3), round(y1 / h, 3), round(x2 / w, 3), round(y2 / h, 3)], area
    return best


def turns(xs):
    """How many times the hand changed direction, ignoring wobbles smaller than WAVE_SIZE."""
    count, ref, direction = 0, xs[0], 0
    for x in xs:
        if (direction <= 0 and x > ref + WAVE_SIZE) or (direction >= 0 and x < ref - WAVE_SIZE):
            new = 1 if x > ref else -1
            if direction and new != direction:
                count += 1
            direction, ref = new, x
        elif (direction > 0 and x > ref) or (direction < 0 and x < ref):
            ref = x                 # still going the same way: follow the hand to its furthest point
    return count


def wait_for_wave():
    """Block until someone waves an open hand at the camera."""
    hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.6)
    xs = collections.deque()       # (time, wrist x) while an open hand is in view
    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        now = time.time()
        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark
            if all(lm[tip].y < lm[tip - 2].y for tip in (8, 12, 16, 20)):   # fingertips above their middle joints: open hand
                xs.append((now, lm[0].x))
        while xs and now - xs[0][0] > WAVE_WINDOW:
            xs.popleft()
        if xs and turns([x for _, x in xs]) >= WAVE_TURNS:
            hands.close()
            return


if not args.no_wave:
    print("wave at the camera to start the night", flush=True)
    wait_for_wave()
    write({"t": datetime.datetime.now().isoformat(timespec="seconds"), "handoff": "wave"})
    print(f"goodnight. watching in {args.settle:.0f} s, Ctrl-C in the morning", flush=True)
    time.sleep(args.settle)

t_end = time.time() + args.seconds if args.seconds else float("inf")
print(f"night shift started, writing {args.out}", flush=True)
while time.time() < t_end:
    try:
        for _ in range(4):          # the webcam buffers a few frames; skip the stale ones
            cap.grab()
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError("no frame")
        r = model.predict(frame, imgsz=320, conf=0.4, classes=[0], verbose=False)[0]
        write({"t": datetime.datetime.now().isoformat(timespec="seconds"), "box": biggest_person(r)})
        time.sleep(args.interval)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print("hiccup:", e, flush=True)
        time.sleep(args.interval)

cap.release()
print("night shift stopped", flush=True)
