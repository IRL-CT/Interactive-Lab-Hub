"""
tram_box.py: draw a box around the tram, for training a detector that knows WHERE it is.

    python tram_box.py              # photos you labeled "tram" that don't have a box yet
    python tram_box.py --bursts     # ALL burst photos, in time order (incl. grip-only at the station)
    python tram_box.py --review     # go back through the boxes you already drew

For each photo: click one corner, then the opposite corner, then ENTER.
Box EVERYTHING you can see of the tram: the grip/hanger on the cable plus the cabin under it.
If the cabin is hidden (behind the trees at the station), box just the grip.
The TOP-CENTER of the box is the grip on the cable: that is the position we track, the same
way whether the cabin is visible or not.
    r = redo the box    n = no tram at all (not even the grip)    s = skip    b = back    q = quit
Saved to tram_boxes.csv after every photo (crop-relative 0..1 coordinates), so quitting
never loses work. About 150 boxes is a good start; include dusk and night if you can see it.
"""
import argparse
import csv
from pathlib import Path

import cv2

from tram_common import DATA
from tram_label import load_labels

BOXES = Path("tram_boxes.csv")      # name,x1,y1,x2,y2  (0..1 of the crop), or name,none
ZOOM = 3


def load_boxes():
    if not BOXES.exists():
        return {}
    out = {}
    with open(BOXES) as f:
        for row in csv.reader(f):
            if len(row) == 2 and row[1] == "none":
                out[row[0]] = None
            elif len(row) == 5:
                out[row[0]] = tuple(float(v) for v in row[1:])
    return out


def save_boxes(boxes):
    with open(BOXES, "w", newline="") as f:
        w = csv.writer(f)
        for name in sorted(boxes):
            b = boxes[name]
            w.writerow([name, "none"] if b is None else [name, *(f"{v:.4f}" for v in b)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", action="store_true", help="go through boxes already drawn")
    parser.add_argument("--bursts", action="store_true",
                        help="all burst photos in time order, whatever their tram/no-tram label")
    args = parser.parse_args()

    labels = load_labels()
    boxes = load_boxes()
    if args.bursts:
        trams = sorted(str(p.relative_to(DATA)) for p in DATA.glob("*/*_*.jpg"))
    else:
        trams = sorted(n for n, y in labels.items() if y == 1 and (DATA / n).exists())
    todo = [n for n in trams if (n in boxes) == args.review]
    if not todo:
        raise SystemExit("nothing to do: label some trams first (tram_label.py)" if not trams
                         else "every tram photo has a box already")
    print(f"{len(boxes)} boxes so far; {len(todo)} photos to go.\n"
          "click 2 corners around grip + cabin (just the grip if the cabin is hidden), ENTER.\n"
          "r = redo, n = no tram at all, s = skip, b = back, q = quit", flush=True)

    clicks = []

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(clicks) < 2:
            clicks.append((x, y))

    title = "tram boxes"
    cv2.namedWindow(title)
    cv2.setMouseCallback(title, on_mouse)
    i = 0
    while 0 <= i < len(todo):
        name = todo[i]
        img = cv2.imread(str(DATA / name))
        if img is None:
            i += 1
            continue
        h, w = img.shape[:2]
        big = cv2.resize(img, None, fx=ZOOM, fy=ZOOM, interpolation=cv2.INTER_NEAREST)
        clicks.clear()
        old = boxes.get(name)
        while True:
            view = big.copy()
            if old and not clicks:                          # show the existing box when reviewing
                x1, y1, x2, y2 = old
                cv2.rectangle(view, (int(x1 * w * ZOOM), int(y1 * h * ZOOM)),
                              (int(x2 * w * ZOOM), int(y2 * h * ZOOM)), (0, 200, 255), 1)
            for c in clicks:
                cv2.circle(view, c, 4, (0, 255, 0), -1)
            if len(clicks) == 2:
                cv2.rectangle(view, clicks[0], clicks[1], (0, 255, 0), 2)
            cv2.rectangle(view, (0, 0), (view.shape[1], 24), (0, 0, 0), -1)
            cv2.putText(view, f"{i + 1}/{len(todo)}  {name}", (6, 17),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.imshow(title, view)
            key = cv2.waitKey(50) & 0xFF
            if key in (13, 10, 32) and len(clicks) == 2:
                (ax, ay), (bx, by) = clicks
                x1, x2 = sorted((ax / (w * ZOOM), bx / (w * ZOOM)))
                y1, y2 = sorted((ay / (h * ZOOM), by / (h * ZOOM)))
                if (x2 - x1) * w >= 3 and (y2 - y1) * h >= 3:
                    boxes[name] = (max(0, x1), max(0, y1), min(1, x2), min(1, y2))
                    save_boxes(boxes)
                    i += 1
                    break
                clicks.clear()
            elif key == ord("r"):
                clicks.clear()
            elif key == ord("n"):
                boxes[name] = None
                save_boxes(boxes)
                i += 1
                break
            elif key == ord("s"):
                i += 1
                break
            elif key == ord("b"):
                i = max(0, i - 1)
                break
            elif key == ord("q"):
                i = -1
                break
    cv2.destroyAllWindows()
    n_box = sum(1 for b in boxes.values() if b)
    print(f"saved: {n_box} boxes ({sum(1 for b in boxes.values() if b is None)} marked no cabin)")


if __name__ == "__main__":
    main()
