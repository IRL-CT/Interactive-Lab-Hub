"""
tram_train_det.py: train a small YOLO DETECTOR that finds where the tram is in the crop.

    python tram_train_det.py                 # train, report, save tram_det.pt
    python tram_train_det.py --epochs 80     # train longer

Uses the boxes from tram_box.py (grip + cabin, or just the grip). Photos marked "no tram"
in tram_box.py, plus some photos you labeled "no tram" in tram_label.py, are added as
empty examples so it also learns to say "nothing here".

Like tram_train.py, photos are split by 3-minute blocks, so near-identical burst photos
never land on both sides of the train/test split.

The number that matters at the end is the POSITION ERROR: how far (in % of the crop width)
the detected grip point (top-center of the box) is from the one you drew. That point is
what the live tracker follows along the cable.
"""
import argparse
import json
import random
import shutil
from pathlib import Path

import numpy as np

from tram_box import load_boxes
from tram_common import DATA
from tram_label import load_labels

DS = Path("tram_det_dataset")
RUNS = Path("tram_runs")
DET = Path("tram_det.pt")


def block_of(name):
    day, fname = name.split("/")
    minute = int(fname[0:2]) * 60 + int(fname[2:4])
    return f"{day}-{minute // 3}"


def write_item(name, box, split):
    stem = name.replace("/", "_").rsplit(".", 1)[0]
    img_dst = DS / "images" / split / f"{stem}.jpg"
    img_dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        img_dst.symlink_to((DATA / name).resolve())
    except OSError:
        shutil.copy(DATA / name, img_dst)
    lbl = DS / "labels" / split / f"{stem}.txt"
    lbl.parent.mkdir(parents=True, exist_ok=True)
    with open(lbl, "w") as f:
        if box:
            x1, y1, x2, y2 = box
            f.write(f"0 {(x1 + x2) / 2:.5f} {(y1 + y2) / 2:.5f} {x2 - x1:.5f} {y2 - y1:.5f}\n")


def grip_point(box):
    """Top-center of a box (0..1 crop coords): the grip on the cable."""
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2, y1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=320, help="crops are ~320 px wide")
    parser.add_argument("--base", default="yolo26n.pt", help="pretrained detector to start from")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    from ultralytics import YOLO

    boxes = {n: b for n, b in load_boxes().items() if (DATA / n).exists()}
    labels = load_labels()
    n_pos = sum(1 for b in boxes.values() if b)
    if n_pos < 30:
        raise SystemExit(f"only {n_pos} boxes: draw at least 30 (python tram_box.py)")

    # empty examples: the "no tram" boxes, plus as many labeled no-tram photos as there are boxes
    rng = random.Random(0)
    items = dict(boxes)
    empties = [n for n, y in labels.items() if y == 0 and n not in items and (DATA / n).exists()]
    for n in rng.sample(empties, min(len(empties), n_pos)):
        items[n] = None

    blocks = {}
    for n in items:
        blocks.setdefault(block_of(n), []).append(n)
    keys = sorted(blocks)
    rng.shuffle(keys)
    pos_keys = [k for k in keys if any(items[n] for n in blocks[k])]
    neg_keys = [k for k in keys if k not in pos_keys]
    val_keys = set(pos_keys[:max(1, len(pos_keys) // 5)] + neg_keys[:max(1, len(neg_keys) // 5)])

    shutil.rmtree(DS, ignore_errors=True)
    val_items = []
    for k in keys:
        split = "val" if k in val_keys else "train"
        for n in blocks[k]:
            write_item(n, items[n], split)
            if split == "val":
                val_items.append(n)
    with open(DS / "data.yaml", "w") as f:
        f.write(f"path: {DS.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: tram\n")
    n_val_pos = sum(1 for n in val_items if items[n])
    print(f"{n_pos} boxes + {len(items) - n_pos} empty photos; testing on {len(val_items)} "
          f"({n_val_pos} with a tram) from held-back passes", flush=True)

    model = YOLO(args.base)
    model.train(data=str(DS / "data.yaml"), epochs=args.epochs, imgsz=args.imgsz, batch=16,
                device=args.device, workers=2, project=str(RUNS.resolve()), name="detector",
                exist_ok=True, patience=15, plots=False, verbose=False,
                mosaic=0.5, degrees=0, flipud=0, fliplr=0.5)
    best = RUNS / "detector" / "weights" / "best.pt"
    model = YOLO(str(best))

    # our own check on the held-back photos
    errors, missed, false_alarms = [], 0, 0
    for n in val_items:
        r = model.predict(str(DATA / n), imgsz=args.imgsz, conf=0.3, verbose=False)[0]
        found = len(r.boxes) > 0
        if items[n]:
            if not found:
                missed += 1
                continue
            b = r.boxes[int(r.boxes.conf.argmax())].xyxyn[0].tolist()
            gx, gy = grip_point(b)
            tx, ty = grip_point(items[n])
            errors.append(float(np.hypot(gx - tx, gy - ty)))
        elif found:
            false_alarms += 1
    print("\non held-back photos:")
    print(f"  trams found:   {n_val_pos - missed}/{n_val_pos}")
    print(f"  false alarms:  {false_alarms}/{len(val_items) - n_val_pos} empty photos")
    if errors:
        print(f"  grip position error: median {np.median(errors):.1%} of the crop width, "
              f"worst {max(errors):.1%}")

    shutil.copy(best, DET)
    with open(DET.with_suffix(".json"), "w") as f:
        json.dump({"imgsz": args.imgsz, "boxes": n_pos,
                   "median_error": float(np.median(errors)) if errors else None}, f)
    print(f"\nsaved {DET}")


if __name__ == "__main__":
    main()
