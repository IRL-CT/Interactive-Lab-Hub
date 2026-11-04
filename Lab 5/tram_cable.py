"""
tram_cable.py: find the cable line, so a detected grip point becomes "how far along the cable".

    python tram_cable.py          # fit the line through your boxed grip points, then confirm

The grip points (top-center of every box you drew in tram_box.py) all sit on the cable, so a
straight line fitted through them IS the cable. Progress along it is 0.0 at one end and 1.0
at the other. The window shows the line with a big "0" and "1":
    ENTER = accept     s = swap the ends     q = quit without saving
Make "0" the end where the cabin LEAVES the view toward Manhattan (the tower side) and
"1" the island/station end, so progress 1.0 means "at the station".
Saved in tram_config.json as "cable".
"""
import cv2
import numpy as np

from tram_box import load_boxes
from tram_common import DATA, load_config, save_config


def fit_cable(points):
    """Total-least-squares line through the points; returns its two extreme ends (0..1)."""
    pts = np.array(points, dtype=float)
    center = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - center)
    d = vt[0]                                    # direction of the line
    t = (pts - center) @ d
    return (center + d * t.min()).tolist(), (center + d * t.max()).tolist()


def progress(point, cable):
    """Project a (x, y) point onto the cable: 0 at end A, 1 at end B (can go slightly beyond)."""
    a, b = np.array(cable[0]), np.array(cable[1])
    ab = b - a
    return float(np.dot(np.array(point) - a, ab) / np.dot(ab, ab))


def main():
    cfg = load_config()
    boxes = {n: b for n, b in load_boxes().items() if b}
    if len(boxes) < 10:
        raise SystemExit(f"only {len(boxes)} boxes: draw at least 10 with tram_box.py first")
    grips = [((x1 + x2) / 2, y1) for x1, y1, x2, y2 in boxes.values()]
    a, b = fit_cable(grips)
    ab = np.subtract(b, a)
    spread = np.median([abs(ab[0] * (g[1] - a[1]) - ab[1] * (g[0] - a[0])) / np.linalg.norm(ab)
                        for g in grips])
    print(f"fitted the cable through {len(grips)} grip points "
          f"(typical distance from the line: {spread:.1%} of the crop)", flush=True)

    sample = cv2.imread(str(DATA / next(iter(boxes))))
    h, w = sample.shape[:2]
    zoom = 3
    title = "tram cable"
    while True:
        view = cv2.resize(sample, None, fx=zoom, fy=zoom)
        P = lambda p: (int(p[0] * w * zoom), int(p[1] * h * zoom))
        for g in grips:
            cv2.circle(view, P(g), 3, (0, 255, 255), -1)
        cv2.line(view, P(a), P(b), (0, 255, 0), 2)
        for p, txt in ((a, "0"), (b, "1")):
            cv2.putText(view, txt, P(p), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 3)
        cv2.putText(view, "ENTER accept, s swap ends, q quit", (8, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow(title, view)
        key = cv2.waitKey(0) & 0xFF
        if key == ord("s"):
            a, b = b, a
        elif key == ord("q"):
            raise SystemExit("not saved")
        elif key in (13, 10, 32):
            break
    cv2.destroyAllWindows()
    cfg["cable"] = [a, b]
    save_config(cfg)
    print("saved the cable to tram_config.json (0 = tower end, 1 = station end)")


if __name__ == "__main__":
    main()
