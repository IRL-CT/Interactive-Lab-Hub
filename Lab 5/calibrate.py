"""
calibrate.py: mark the light strips (and door zones) for the bathroom tracker,
then check how bright each strip reads with the bathroom light on vs off.

    python calibrate.py --rotate ccw        # camera on its side? rotate the view first (ccw, cw, 180, none)
    python calibrate.py                     # grab a webcam frame and click the 4 boxes
    python calibrate.py --image snap.jpg    # mark boxes on a saved photo instead
    python calibrate.py --test              # print strip brightness once a second (Ctrl-C to stop)

Boxes are made with CLICKS, not drags (drags do not work well over Raspberry Pi Connect):
click the top-left corner, then the bottom-right corner, then press ENTER. Press r to redo.

Needs a window, so run it from the Pi desktop (Screen sharing), or over ssh after
`export DISPLAY=:0`. Saves zones.json and calib_preview.jpg here.
"""
import argparse
import json
import time

import cv2
import numpy as np

ZONES = [
    ("near_door", "NEAR bathroom door: the whole door, floor to top (reference only)"),
    ("far_door", "FAR bathroom door: the whole door, floor to top (reference only)"),
    ("near_strip", "NEAR door: a THIN box along the gap under the door"),
    ("far_strip", "FAR door: a THIN box along the gap under the door"),
]
COLORS = {"near_door": (0, 255, 0), "far_door": (255, 128, 0),
          "near_strip": (0, 255, 255), "far_strip": (0, 128, 255)}
ROTATIONS = {"none": None, "cw": cv2.ROTATE_90_CLOCKWISE,
             "ccw": cv2.ROTATE_90_COUNTERCLOCKWISE, "180": cv2.ROTATE_180}


def load_zones():
    try:
        with open("zones.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_zones(zones):
    with open("zones.json", "w") as f:
        json.dump(zones, f, indent=2)


def rotate(frame, how):
    code = ROTATIONS.get(how or "none")
    return frame if code is None else cv2.rotate(frame, code)


def open_cam():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        raise SystemExit("no webcam found: is it plugged in?")
    return cap


def grab(cap, how):
    for _ in range(4):              # skip stale buffered frames
        cap.grab()
    ok, frame = cap.read()
    if not ok:
        raise SystemExit("could not read a frame from the webcam")
    return rotate(frame, how)


def strip_reading(frame, box):
    """Brightness of one light strip: mean and 90th percentile of the grayscale pixels."""
    x, y, w, h = box
    gray = cv2.cvtColor(frame[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
    return float(gray.mean()), float(np.percentile(gray, 90))


def draw(frame, boxes):
    view = frame.copy()
    for name, (x, y, w, h) in boxes.items():
        cv2.rectangle(view, (x, y), (x + w, y + h), COLORS[name], 2)
        cv2.putText(view, name, (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLORS[name], 1)
    return view


def click_box(frame, boxes, name, prompt):
    """Two clicks make a box: first corner, then the opposite corner. ENTER accepts, r redoes."""
    title = "calibrate"
    clicks = []

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(clicks) < 2:
            clicks.append((x, y))

    cv2.namedWindow(title)
    cv2.setMouseCallback(title, on_mouse)
    print(f"\n{prompt}\n  click one corner, then the opposite corner, then press ENTER "
          f"(r = redo, q = quit)", flush=True)
    while True:
        view = draw(frame, boxes)
        cv2.putText(view, f"{name}: click 2 corners, ENTER", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        for c in clicks:
            cv2.circle(view, c, 4, COLORS[name], -1)
        if len(clicks) == 2:
            cv2.rectangle(view, clicks[0], clicks[1], COLORS[name], 2)
        cv2.imshow(title, view)
        key = cv2.waitKey(50) & 0xFF
        if key == ord("r"):
            clicks.clear()
        elif key == ord("q"):
            raise SystemExit("quit; nothing saved")
        elif key in (13, 10, 32) and len(clicks) == 2:      # Enter / Return / Space
            (x1, y1), (x2, y2) = clicks
            x, y = min(x1, x2), min(y1, y2)
            w, h = abs(x2 - x1), abs(y2 - y1)
            if w >= 2 and h >= 2:
                return [int(x), int(y), int(w), int(h)]
            print("  box too small, click again", flush=True)
            clicks.clear()


def mark(frame, zones):
    boxes = {}
    for name, prompt in ZONES:
        boxes[name] = click_box(frame, boxes, name, prompt)
    cv2.destroyAllWindows()
    zones.update(boxes)
    save_zones(zones)
    cv2.imwrite("calib_preview.jpg", draw(frame, boxes))
    print("\nsaved zones.json and calib_preview.jpg", flush=True)
    for side in ("near", "far"):
        mean, p90 = strip_reading(frame, boxes[f"{side}_strip"])
        print(f"{side} strip right now: mean {mean:.0f}, p90 {p90:.0f}", flush=True)


def test(zones):
    if "near_strip" not in zones:
        raise SystemExit("no strips in zones.json yet: run `python calibrate.py` first")
    cap = open_cam()
    how = zones.get("rotate")
    print("strip brightness (0 = black, 255 = white). Turn each bathroom light on and off "
          "with the door closed and note the numbers. Ctrl-C to stop.\n", flush=True)
    try:
        while True:
            frame = grab(cap, how)
            near = strip_reading(frame, zones["near_strip"])
            far = strip_reading(frame, zones["far_strip"])
            print(f"{time.strftime('%H:%M:%S')}  near: mean {near[0]:5.1f} p90 {near[1]:5.1f}"
                  f"   |   far: mean {far[0]:5.1f} p90 {far[1]:5.1f}", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    cap.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rotate", choices=list(ROTATIONS),
                        help="rotate the camera view (saved to zones.json, used by bathroom_night.py)")
    parser.add_argument("--image", help="mark boxes on this saved photo instead of a webcam frame")
    parser.add_argument("--test", action="store_true", help="print strip brightness every second")
    args = parser.parse_args()

    zones = load_zones()
    if args.rotate:
        if args.rotate != zones.get("rotate", "none") and any(k in zones for k in ("near_strip", "people")):
            print("rotation changed: redo the boxes (this run) and the --learn steps afterwards", flush=True)
        zones["rotate"] = args.rotate
        save_zones(zones)
        print(f"camera view will be rotated: {args.rotate}", flush=True)

    if args.test:
        test(zones)
    else:
        if args.image:
            frame = cv2.imread(args.image)
            if frame is None:
                raise SystemExit(f"could not read {args.image}")
            frame = rotate(frame, zones.get("rotate"))
        else:
            cap = open_cam()
            frame = grab(cap, zones.get("rotate"))
            cap.release()
        mark(frame, zones)
