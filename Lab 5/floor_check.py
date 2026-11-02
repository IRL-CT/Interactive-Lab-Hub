"""Aim the under-bed camera and tune the feet detector before the first night.

    python floor_check.py                     # window (VNC): live floor view with the numbers
    python floor_check.py --headless          # just print the numbers once a second (ssh)
    python floor_check.py --roi 0,0.3,1,1     # try a different floor region

What to do:
  1. Clear the floor next to the bed and press b (or wait: the first frames become the baseline).
  2. Step on and off the floor beside the bed. Watch "change" and "yolo".
     - "change" should jump well above --change-area (default 0.04) with feet, and stay
       near 0 without. If it hovers near the threshold, raise or lower --change-area.
     - "yolo" is the best person-box confidence inside the floor region. Often 0 for
       bare feet; legs and the lower body sometimes get one.
  3. Turn the room light off. If "bright" falls below --dark (default 15), the camera
     can't see: add a dim light under the bed.
  4. Press s to save floor_check.jpg for your writeup. q quits.
Then run monster.py with the same --roi / --change-area / --pixel-diff / --dark values.
"""
import argparse
import os
import sys
import time

import cv2
import numpy as np

from overnight import FeetDetector

p = argparse.ArgumentParser()
p.add_argument("--camera", type=int, default=0)
p.add_argument("--roi", default="0,0.2,1,1")
p.add_argument("--change-area", type=float, default=0.04)
p.add_argument("--pixel-diff", type=int, default=25)
p.add_argument("--dark", type=float, default=15)
p.add_argument("--yolo-conf", type=float, default=0.25)
p.add_argument("--no-yolo", action="store_true")
p.add_argument("--headless", action="store_true")
args = p.parse_args()

show = not args.headless
if show and os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":0"           # Pi OS Wayland desktop: OpenCV's window goes through XWayland
if show and sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
    print("no display (plain ssh?): printing numbers only. Use VNC to see the picture.")
    show = False

roi = tuple(float(v) for v in args.roi.split(","))
det = FeetDetector(args.camera, roi, args.change_area, args.pixel_diff, args.dark,
                   not args.no_yolo, args.yolo_conf)
print("taking the empty-floor baseline: keep your feet off the floor...")
det.take_baseline()

while True:
    r = det.look()
    verdict = "TOO DARK" if r["feet"] is None else ("FEET" if r["feet"] else "no feet")
    line = f"{time.strftime('%H:%M:%S')}  {verdict:8s} change {r['change']:.3f}  yolo {r['yolo']:.2f}  bright {r['bright']:.0f}"
    print(line, flush=True)
    key = -1
    if show:
        view = r["frame"].copy()
        h, w = view.shape[:2]
        x0, y0, x1, y1 = roi
        color = (0, 0, 255) if r["feet"] else (0, 200, 0)
        cv2.rectangle(view, (int(x0 * w), int(y0 * h)), (int(x1 * w) - 1, int(y1 * h) - 1), color, 2)
        cv2.putText(view, line[10:], (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        cv2.putText(view, "b: new baseline  s: save  q: quit", (10, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow("floor check", view)
        key = cv2.waitKey(1000) & 0xFF
    else:
        time.sleep(1)
    if key == ord("q"):
        break
    if key == ord("b"):
        det.take_baseline()
        print("new baseline taken")
    if key == ord("s"):
        cv2.imwrite("floor_check.jpg", view)
        print("saved floor_check.jpg")
