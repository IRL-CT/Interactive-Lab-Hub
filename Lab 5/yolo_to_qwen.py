"""
Part E: the pipeline. YOLO watches for a while, an interpreter turns boxes into
readings in words, the readings become a log, and Qwen answers a question about it.

    python yolo_to_qwen.py                               # watch 60 s with a window (VNC), then ask the default question
    python yolo_to_qwen.py --headless                    # no window, so it runs over plain ssh
    python yolo_to_qwen.py --seconds 300                 # watch longer
    python yolo_to_qwen.py --question "Did anyone leave?"
    python yolo_to_qwen.py --all                         # report the other objects too, not only people
    python yolo_to_qwen.py --every                       # log every reading, not only changes
    python yolo_to_qwen.py --json                        # ask for a structured answer
    python yolo_to_qwen.py --log watch_log.txt           # skip the camera, reason over a saved log

The window shows YOLO's boxes, the current reading and the seconds left; press q to stop
watching early. Each run saves its log to watch_log.txt. Edit that file by hand and feed
it back with --log to see whether the model notices contradictions.

overnight.py imports interpret() and model from this file, so keep them at the top level.
"""
import argparse
import datetime
import os
import sys
import time

import cv2
import requests
from ultralytics import YOLO

model = YOLO("yolo26n_ncnn_model")


def interpret(r):
    """The interpreter: turn one YOLO result into one short reading in words.

    This is the most important design decision in the pipeline. The language model
    never sees pixels, only the words chosen here. Change it and the model's world changes.
    """
    h, w = r.orig_shape
    people, others = [], set()
    for box in r.boxes:
        name = model.names[int(box.cls)]
        if name != "person":
            others.add(name)                 # only with --all; see watch()
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cx = (x1 + x2) / 2
        side = "left" if cx < w / 3 else "right" if cx > 2 * w / 3 else "center"   # which third of the frame
        dist = "close" if (y2 - y1) > 0.6 * h else "far"                           # how tall the box is
        posture = "lying" if (x2 - x1) > 1.2 * (y2 - y1) else "upright"           # wider than tall: lying down
        people.append(f"{side}/{dist}/{posture}")
    reading = f"{len(people)} person(s) at {', '.join(people)}" if people else "nobody"
    if others:
        reading += "; also " + ", ".join(sorted(others))
    return reading


def watch(seconds, every=False, interval=0.5, show=True, all_classes=False):
    """Watch the webcam for `seconds`. Returns the log as a list of 'HH:MM:SS reading' lines."""
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        raise SystemExit("no webcam found: is it plugged in?")
    classes = None if all_classes else [0]      # class 0 is "person"; the other 79 are noisy at this frame size
    log, last = [], None
    t_end = time.time() + seconds
    while time.time() < t_end:
        ok, frame = cap.read()
        if not ok:
            time.sleep(1)
            continue
        r = model.predict(frame, imgsz=320, conf=0.4, classes=classes, verbose=False)[0]
        reading = interpret(r)
        if every or reading != last:
            log.append(f"{datetime.datetime.now():%H:%M:%S} {reading}")
            print(log[-1], flush=True)
            last = reading
        if show:
            view = r.plot()                          # the frame with YOLO's boxes drawn on it
            cv2.putText(view, reading, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(view, f"{int(t_end - time.time())} s left, q to stop", (10, view.shape[0] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("YOLO to Qwen", view)
            if cv2.waitKey(int(interval * 1000)) == ord("q"):   # the wait also lets the window redraw
                break
        else:
            time.sleep(interval)
    cap.release()
    if show:
        cv2.destroyAllWindows()
    return log


def ask(log, question, seconds, llm="qwen3.5:0.8b", every=False, as_json=False):
    """The reasoner: give the model the log and the question, nothing else."""
    how = "every half second" if every else "only when the reading changed"
    log_text = "\n".join(log)
    prompt = f"""You are the reasoning part of an observant device. A camera watched a room for {seconds} seconds.
Below is the detector's log. A line was written {how}.

{log_text}

Question: {question}
Answer in at most three sentences. Only use what is in the log. If the log does not say, say so."""
    request = {
        "model": llm,
        "prompt": prompt,
        "think": False,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 250},    # three sentences, and a hard cap in case it forgets
    }
    if as_json:
        request["format"] = {
            "type": "object",
            "properties": {
                "people": {"type": "integer"},
                "activity": {"type": "string"},
                "unusual": {"type": "boolean"},
            },
            "required": ["people", "activity", "unusual"],
        }
    t0 = time.time()
    r = requests.post("http://localhost:11434/api/generate", json=request, timeout=600)
    r.raise_for_status()
    return r.json()["response"], time.time() - t0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=60, help="how long to watch")
    parser.add_argument("--question",
                        default="How many people were there, what were they doing, and did anything change?")
    parser.add_argument("--model", default="qwen3.5:0.8b")
    parser.add_argument("--headless", action="store_true", help="do not open a window (plain ssh)")
    parser.add_argument("--all", action="store_true", help="detect all 80 classes, not only people")
    parser.add_argument("--every", action="store_true", help="log every reading, not only changes")
    parser.add_argument("--json", action="store_true", help="ask for a structured JSON answer")
    parser.add_argument("--log", help="reason over this saved log instead of watching")
    args = parser.parse_args()

    seconds = args.seconds
    if args.log:
        log = [line.rstrip("\n") for line in open(args.log) if line.strip()]
    else:
        show = not args.headless
        if show and sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
            print("no display found (plain ssh?): running without the window. Use VNC to see it.", flush=True)
            show = False
        t0 = time.time()
        log = watch(args.seconds, every=args.every, show=show, all_classes=args.all)
        seconds = round(time.time() - t0)           # shorter than --seconds if you pressed q
        with open("watch_log.txt", "w") as f:
            f.write("\n".join(log) + "\n")
        print(f"\n{len(log)} lines saved to watch_log.txt")

    print("asking Qwen...", flush=True)
    answer, took = ask(log, args.question, seconds, llm=args.model,
                       every=args.every, as_json=args.json)
    print(f"\nQwen ({took:.1f} s):\n{answer}")
