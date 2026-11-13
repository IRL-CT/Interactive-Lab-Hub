"""
bathroom_night.py: the bathroom-lights tracker (Lab 5, Part 2).

Watches the hallway after 9 pm, notices when someone comes out of a bathroom,
guesses who it was from their height in the frame, and checks a few seconds later
whether that bathroom's light was left on. The morning report tallies it up.

Setup, once (the camera must not move afterwards):
    python calibrate.py                                   # draw door zones + light strips -> zones.json
    python bathroom_night.py --learn Viktor --door near   # stand at the near door for ~10 s
    python bathroom_night.py --learn Viktor --door far    # ...and at the far door
                                                          # repeat both for each roommate

Every night:
    tmux new -s night
    python bathroom_night.py               # waits until 21:00, then logs events until Ctrl-C
    python bathroom_night.py --now --show  # start right away with a window (testing / demo video)

In the morning:
    python bathroom_night.py --morning     # tally + a short Qwen report

Only the event log (bathroom_log.jsonl) is saved. --snaps also saves a photo of each exit,
to check the height guesses; delete those after the demo.
"""
import argparse
import collections
import datetime
import json
import pathlib
import statistics
import time

import cv2
import numpy as np
import requests

ZONES_FILE = "zones.json"
LOG_FILE = "bathroom_log.jsonl"
DOORS = ("near", "far")
CHECK_AFTER = 8      # seconds after someone comes out before checking their light
LIGHT_MEMORY = 30    # a "came out" only counts if that light was on within this many seconds
UNSURE_GAP = 0.03    # if the two closest learned heights are within 3%, report both names

model = None         # YOLO is loaded only when the camera is used (not for --morning)


# ---------- helpers ----------

def load_zones():
    global ROTATE
    try:
        with open(ZONES_FILE) as f:
            zones = json.load(f)
    except FileNotFoundError:
        raise SystemExit("no zones.json yet: run `python calibrate.py` first")
    ROTATE = zones.get("rotate")
    return zones


def save_zones(zones):
    with open(ZONES_FILE, "w") as f:
        json.dump(zones, f, indent=2)


def open_cam():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        raise SystemExit("no webcam found: is it plugged in?")
    return cap


ROTATIONS = {"cw": cv2.ROTATE_90_CLOCKWISE, "ccw": cv2.ROTATE_90_COUNTERCLOCKWISE,
             "180": cv2.ROTATE_180}
ROTATE = None        # set from zones.json ("rotate"), written by `calibrate.py --rotate`


def grab(cap):
    for _ in range(4):              # the webcam buffers frames; skip the stale ones
        cap.grab()
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError("no frame from the webcam")
    code = ROTATIONS.get(ROTATE)
    return frame if code is None else cv2.rotate(frame, code)


def detect(frame, imgsz):
    """Person boxes as [x1, y1, x2, y2] in frame pixels."""
    global model
    if model is None:
        from ultralytics import YOLO
        model = YOLO("yolo26n_ncnn_model")
    r = model.predict(frame, imgsz=imgsz, conf=0.4, classes=[0], verbose=False)[0]
    return [b.xyxy[0].tolist() for b in r.boxes]


def strip_p90(frame, box):
    """Brightness of a light strip: the 90th percentile of its grayscale pixels."""
    x, y, w, h = box
    gray = cv2.cvtColor(frame[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
    return float(np.percentile(gray, 90))


class Debounced:
    """A yes/no that only flips after the raw reading disagrees for `n` frames in a row.
    This is what stops YOLO's flicker from turning into fake events."""

    def __init__(self, n=2):
        self.n, self.value, self.streak = n, False, 0

    def update(self, raw):
        if raw == self.value:
            self.streak = 0
            return False
        self.streak += 1
        if self.streak >= self.n:
            self.value, self.streak = raw, 0
            return True              # it flipped this frame
        return False


def door_of(box, people):
    """Which door a person box is standing at ('near', 'far' or None), using where and
    how big the learned roommates looked at each door."""
    x1, y1, x2, y2 = box
    cx, h = (x1 + x2) / 2, y2 - y1
    best = None
    for door in DOORS:
        for p in people.values():
            ref = p.get(door)
            if not ref:
                continue
            if abs(cx - ref["cx"]) <= 0.75 * ref["w"] and 0.8 * ref["h"] <= h <= 1.25 * ref["h"]:
                err = abs(h - ref["h"]) / ref["h"]
                if best is None or err < best[1]:
                    best = (door, err)
    return best[0] if best else None


def guess_who(door, heights, people):
    """Closest learned box height at this door. Two names if it is too close to call."""
    cands = sorted((abs(statistics.median(heights) - p[door]["h"]) / p[door]["h"], name)
                   for name, p in people.items() if door in p) if heights else []
    if not cands:
        return "someone"
    if len(cands) > 1 and cands[1][0] - cands[0][0] < UNSURE_GAP:
        return f"{cands[0][1]} or {cands[1][1]}"
    return cands[0][1]


def log_event(f, text, **fields):
    entry = {"t": datetime.datetime.now().isoformat(timespec="seconds"), "reading": text, **fields}
    f.write(json.dumps(entry) + "\n")
    f.flush()
    print(f"{entry['t'][11:]} {text}", flush=True)


# ---------- setup: learn each roommate's height at each door ----------

def learn(name, door, seconds, imgsz, show):
    load_zones()                    # needs zones.json first (and picks up the rotation)
    cap = open_cam()
    samples = []
    print(f"{name}: stand in front of the {door} bathroom door, facing the camera, and shift "
          f"around a little. Recording for {seconds} s...", flush=True)
    t_end = time.time() + seconds
    while time.time() < t_end:
        frame = grab(cap)
        boxes = detect(frame, imgsz)
        if len(boxes) == 1:         # only learn from frames with exactly one person in view
            x1, y1, x2, y2 = boxes[0]
            samples.append(((x1 + x2) / 2, x2 - x1, y2 - y1))
        if show:
            for x1, y1, x2, y2 in boxes:
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.imshow("learning", frame)
            cv2.waitKey(1)
    cap.release()
    if show:
        cv2.destroyAllWindows()
    if len(samples) < 5:
        raise SystemExit("saw exactly one person in fewer than 5 frames: try again (more light, "
                         "only one person in view)")
    cx, w, h = (statistics.median(s[i] for s in samples) for i in range(3))
    zones = load_zones()
    zones.setdefault("people", {}).setdefault(name, {})[door] = {
        "cx": round(cx, 1), "w": round(w, 1), "h": round(h, 1)}
    save_zones(zones)
    print(f"saved: {name} at the {door} door looks {h:.0f} px tall ({len(samples)} frames)")
    for other, p in zones["people"].items():
        if other != name and door in p:
            print(f"  for comparison, {other} at the {door} door: {p[door]['h']:.0f} px")


# ---------- the night shift ----------

def is_night(start_hour):
    hour = datetime.datetime.now().hour
    return hour >= start_hour or hour < 8


def light_thresholds(zones, cap):
    th = dict(zones.get("light_on", {}))
    missing = [d for d in DOORS if d not in th]
    if missing:
        frames = [grab(cap) for _ in range(5)]
        for d in missing:
            base = statistics.median(strip_p90(f, zones[f"{d}_strip"]) for f in frames)
            th[d] = base + 40
            print(f"no '{d}' light threshold in zones.json: assuming that light is OFF right now "
                  f"(strip {base:.0f}), so ON means above {th[d]:.0f}", flush=True)
    return th


def night(args):
    zones = load_zones()
    people = zones.get("people", {})
    if not people:
        raise SystemExit("nobody learned yet: run `python bathroom_night.py --learn NAME --door near` "
                         "(and far) for each roommate first")
    if not args.now and not is_night(args.start):
        print(f"waiting until {args.start}:00 to start watching (--now starts right away)...", flush=True)
        while not is_night(args.start):
            time.sleep(30)

    cap = open_cam()
    thresholds = light_thresholds(zones, cap)
    light = {d: Debounced() for d in DOORS}
    at_door = {d: Debounced() for d in DOORS}
    last_on = {d: 0.0 for d in DOORS}
    visit = {d: None for d in DOORS}
    pending = []                                  # (check time, door, name)
    counts = collections.deque(maxlen=5)          # people in view, recent frames
    last_beat = 0.0
    if args.snaps:
        pathlib.Path("bathroom_snaps").mkdir(exist_ok=True)
    log = open(LOG_FILE, "a")
    log_event(log, "night shift started", event="start")

    try:
        while True:
            t0 = time.time()
            try:
                frame = grab(cap)
            except RuntimeError as e:
                print("hiccup:", e, flush=True)
                time.sleep(args.interval)
                continue
            boxes = detect(frame, args.imgsz)
            n, now = len(boxes), time.time()

            # 1. lights: the strip under each door
            for d in DOORS:
                raw = strip_p90(frame, zones[f"{d}_strip"]) > thresholds[d]
                if light[d].update(raw):
                    state = "ON" if light[d].value else "OFF"
                    log_event(log, f"{d} bathroom light turned {state}", event="light", door=d,
                              light=light[d].value)
                if light[d].value:
                    last_on[d] = now

            # 2. people: who is standing at which door
            heights = {d: [] for d in DOORS}
            for b in boxes:
                d = door_of(b, people)
                if d:
                    heights[d].append(b[3] - b[1])

            for d in DOORS:
                if at_door[d].update(bool(heights[d])):
                    if at_door[d].value:
                        # someone just showed up at this door. Did they pop into view right
                        # here (came out of the bathroom) or walk over from the hallway?
                        before = counts[-2] if len(counts) >= 2 else n
                        visit[d] = {"appeared": n > before, "n": n, "hs": [], "frame": frame.copy()}
                    else:
                        # they just left the door spot: decide what happened
                        v = visit[d] or {"appeared": False, "n": n, "hs": [], "frame": None}
                        name = guess_who(d, v["hs"], people)
                        if v["appeared"] and now - last_on[d] <= LIGHT_MEMORY:
                            log_event(log, f"{name} came out of the {d} bathroom",
                                      event="exit", door=d, who=name)
                            pending.append((now + CHECK_AFTER, d, name))
                            if args.snaps and v["frame"] is not None:
                                stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                                cv2.imwrite(f"bathroom_snaps/{stamp}-{d}.jpg", v["frame"])
                        elif not v["appeared"] and n < v["n"]:
                            log_event(log, f"{name} went into the {d} bathroom",
                                      event="enter", door=d, who=name)
                        visit[d] = None
                if at_door[d].value and visit[d] is not None:
                    visit[d]["hs"].extend(heights[d])

            # 3. a few seconds after each exit, check whether the light stayed on
            for item in [p for p in pending if p[0] <= now]:
                pending.remove(item)
                _, d, name = item
                if light[d].value:
                    log_event(log, f"{name} left the {d} bathroom light ON",
                              event="left_on", door=d, who=name)
                else:
                    log_event(log, f"{name} turned the {d} bathroom light off",
                              event="turned_off", door=d, who=name)

            counts.append(n)
            if now - last_beat > 600:               # so a quiet night is not mistaken for a crash
                log.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"),
                                      "alive": True}) + "\n")
                log.flush()
                last_beat = now

            if args.show or args.record:
                view = annotate(frame, boxes, people, zones, light)
                # record only while something is happening: someone in view, or an exit
                # waiting for its light check. A quiet hallway adds nothing to the video.
                if args.record and (n > 0 or pending):
                    if writer is None:
                        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                        video_path = f"bathroom_record_{stamp}.mp4"
                        writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*"mp4v"),
                                                 max(1.0, 1 / args.interval),
                                                 (view.shape[1], view.shape[0]))
                        print(f"recording to {video_path}", flush=True)
                    writer.write(view)
                if args.show:
                    cv2.imshow("bathroom tracker", view)
                    if cv2.waitKey(1) == ord("q"):
                        break

            time.sleep(max(0.0, args.interval - (time.time() - t0)))
    except KeyboardInterrupt:
        pass
    cap.release()
    if writer is not None:
        writer.release()
        print(f"saved {video_path}", flush=True)
    if args.show:
        cv2.destroyAllWindows()
    log_event(log, "night shift stopped", event="stop")


# ---------- the morning report ----------

def morning(args):
    try:
        entries = [json.loads(l) for l in open(LOG_FILE) if l.strip()]
    except FileNotFoundError:
        raise SystemExit("no bathroom_log.jsonl yet: run a night first")
    starts = [i for i, e in enumerate(entries) if e.get("event") == "start"]
    night_entries = entries[starts[-1]:] if starts else entries     # only the most recent night
    events = [e for e in night_entries if e.get("event") in ("enter", "exit", "left_on", "turned_off")]

    left_on = collections.Counter(e["who"] for e in events if e["event"] == "left_on")
    turned_off = collections.Counter(e["who"] for e in events if e["event"] == "turned_off")
    print("Last night's tally:")
    if not left_on and not turned_off:
        print("  no bathroom trips seen")
    for name in sorted(set(left_on) | set(turned_off)):
        print(f"  {name}: left the light ON {left_on[name]}x, turned it off {turned_off[name]}x")

    lines = "\n".join(f"{e['t'][11:16]} {e['reading']}" for e in events) or "(no bathroom events)"
    prompt = f"""You are a friendly hallway device that keeps track of who leaves the bathroom lights on at night.
Times each person left a bathroom light ON last night: {dict(left_on) or 'nobody'}
Times each person turned it off: {dict(turned_off) or 'nobody'}
Event log:
{lines}

Write a short, light-hearted morning report in at most three sentences. Use only these facts and numbers and do not invent events.
A name like "A or B" means the device was not sure which of the two it was. If there were no events, say it was a quiet night."""
    print("\nasking Qwen...", flush=True)
    t0 = time.time()
    try:
        r = requests.post("http://localhost:11434/api/generate", timeout=600, json={
            "model": args.model, "prompt": prompt, "think": False, "stream": False,
            "options": {"temperature": 0.3, "num_predict": 150}})
        r.raise_for_status()
        print(f"\nQwen ({time.time() - t0:.1f} s):\n{r.json()['response']}")
    except requests.RequestException as e:
        print(f"could not reach Ollama ({e}); the tally above is the report")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--learn", metavar="NAME", help="learn this roommate's height at --door")
    parser.add_argument("--door", choices=DOORS, help="which door to learn at")
    parser.add_argument("--seconds", type=int, default=10, help="how long --learn records")
    parser.add_argument("--now", action="store_true", help="start watching now instead of at --start")
    parser.add_argument("--start", type=int, default=21, help="hour to start watching (default 21)")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between looks")
    parser.add_argument("--imgsz", type=int, default=640, help="YOLO input size (bigger = steadier heights)")
    parser.add_argument("--show", action="store_true", help="open a window (Pi desktop only)")
    parser.add_argument("--snaps", action="store_true", help="save a photo of each exit")
    parser.add_argument("--morning", action="store_true", help="tally last night and ask Qwen for a report")
    parser.add_argument("--model", default="qwen3.5:0.8b", help="Ollama model for --morning")
    args = parser.parse_args()

    if args.morning:
        morning(args)
    elif args.learn:
        if not args.door:
            raise SystemExit("--learn needs --door near or --door far")
        learn(args.learn, args.door, args.seconds, args.imgsz, args.show)
    else:
        night(args)
