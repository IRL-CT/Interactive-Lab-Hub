"""
tram_label.py: label collected crops as "tram" or "no tram", fast.

    python tram_label.py                 # random unlabeled images (start here)
    python tram_label.py --find-trams    # images that changed most first: finds trams fast (no model needed)
    python tram_label.py --uncertain     # after training: the images the model is least sure about
    python tram_label.py --bursts        # photos from tram_burst.py, in time order
    python tram_label.py --stats         # counts per day/hour, and whether it's enough to train
    python tram_label.py --review        # flip through what you already labeled, to fix mistakes

Keys:  t = tram in view   n = no tram   s = skip   b = back one   q = save and quit
Labels are saved to tram_labels.csv after every key press, so quitting never loses work.

--uncertain is the "active learning" half of the semi-supervised loop: once a model exists,
your labels go where they help most (the confusing images), and tram_train.py fills in the
easy ones on its own (pseudo-labels).

Tip: label in sessions. Get ~50 trams with --find-trams, add ~150 random no-tram images,
train, then do a round of --uncertain.
"""
import argparse
import csv
import random

import cv2

import numpy as np

from tram_common import DATA, LABELS, change_score, load_classifier


def load_labels():
    if not LABELS.exists():
        return {}
    with open(LABELS) as f:
        return {row[0]: int(row[1]) for row in csv.reader(f) if len(row) == 2 and row[1] in ("0", "1")}


def save_labels(labels):
    with open(LABELS, "w", newline="") as f:
        csv.writer(f).writerows(sorted(labels.items()))


def all_images():
    return sorted(str(p.relative_to(DATA)) for p in DATA.glob("*/*.jpg"))


def order_by_uncertainty(names, limit):
    """Images the current model is least sure about (closest to 50%) first."""
    p_tram = load_classifier()
    pool = random.sample(names, min(len(names), limit))
    probs = {}
    for n in pool:
        img = cv2.imread(str(DATA / n))
        if img is not None:
            probs[n] = p_tram(img)
    order = sorted(probs, key=lambda n: abs(probs[n] - 0.5))
    return order, probs


def order_by_change(names, limit):
    """The tram is in view only a few % of the time, so random images are almost all empty.
    This builds an "empty view" per day and hour (the median image: a passing tram is gone
    from the median), then shows the images that differ from it most. No color rules: anything
    that changed comes first, and you decide what it is."""
    pool = random.sample(names, min(len(names), limit))
    groups = {}
    for n in pool:
        groups.setdefault(n[:11], []).append(n)          # "YYYYMMDD/HH" = same day and hour
    scores = {}
    for _, members in groups.items():
        imgs = [cv2.imread(str(DATA / n)) for n in members]
        ok = [(n, im) for n, im in zip(members, imgs) if im is not None]
        if len(ok) < 5:
            continue
        shape = ok[0][1].shape
        stack = [im for _, im in ok if im.shape == shape]
        background = np.median(np.stack(stack[:200]), axis=0).astype(np.uint8)
        for n, im in ok:
            if im.shape == shape:
                scores[n] = change_score(im, background)
    return sorted(scores, key=scores.get, reverse=True)


def stats(labels):
    """How many images, how many labeled, how many trams, per day and hour."""
    names = all_images()
    print(f"images collected: {len(names)}   labeled: {len(labels)}   "
          f"unlabeled: {len([n for n in names if n not in labels])}")
    groups = {}
    for n in names:
        g = groups.setdefault(n[:11], [0, 0, 0])      # "YYYYMMDD/HH": images, labeled, trams
        g[0] += 1
        if n in labels:
            g[1] += 1
            g[2] += labels[n]
    print("\nday       hour  images  labeled  trams")
    for k in sorted(groups):
        day, hour = k.split("/")
        print(f"{day}  {hour}:00  {groups[k][0]:6d}  {groups[k][1]:7d}  {groups[k][2]:5d}")
    n_tram = sum(labels.values())
    print(f"\ntotal: {n_tram} tram, {len(labels) - n_tram} no tram")
    if n_tram < 15:
        print("not enough trams to train yet (need 15+)")
    elif n_tram < 100:
        print("enough to train a first model; 100+ trams (incl. dusk/night) will make it much better")
    else:
        print("good amount of trams")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uncertain", action="store_true", help="show the most confusing images first")
    parser.add_argument("--find-trams", action="store_true", help="images that differ most from the empty view first")
    parser.add_argument("--review", action="store_true", help="go through already-labeled images")
    parser.add_argument("--bursts", action="store_true", help="only photos from tram_burst.py")
    parser.add_argument("--stats", action="store_true", help="count labels per session and exit")
    parser.add_argument("--pool", type=int, default=3000, help="images to score for --uncertain")
    args = parser.parse_args()

    labels = load_labels()
    if args.stats:
        stats(labels)
        return
    names = all_images()
    if not names:
        raise SystemExit(f"no images in {DATA}/ yet: run tram_collect.py first")
    hints = {}
    if args.review:
        todo = [n for n in names if n in labels]
    else:
        todo = [n for n in names if n not in labels]
        if args.bursts:
            todo = sorted(n for n in todo if "_" in n.split("/")[1])     # burst names: HHMMSS_mmm.jpg
        if args.uncertain:
            todo, hints = order_by_uncertainty(todo, args.pool)
        elif args.find_trams:
            todo = order_by_change(todo, args.pool)
        elif not args.bursts:                 # bursts stay in time order: faster to label
            random.shuffle(todo)
    if not todo:
        raise SystemExit("nothing to label")

    n_tram = sum(labels.values())
    print(f"{len(labels)} labeled so far ({n_tram} tram, {len(labels) - n_tram} no tram); "
          f"{len(todo)} to go.\nt = tram, n = no tram, s = skip, b = back, q = quit", flush=True)

    i = 0
    title = "tram labeler"
    while 0 <= i < len(todo):
        name = todo[i]
        img = cv2.imread(str(DATA / name))
        if img is None:
            i += 1
            continue
        view = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
        status = {1: "TRAM", 0: "no tram"}.get(labels.get(name), "unlabeled")
        text = f"{i + 1}/{len(todo)}  {name}  [{status}]"
        if name in hints:
            text += f"  model: {hints[name]:.0%} tram"
        cv2.rectangle(view, (0, 0), (view.shape[1], 26), (0, 0, 0), -1)
        cv2.putText(view, text, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow(title, view)
        key = cv2.waitKey(0) & 0xFF
        if key == ord("t"):
            labels[name] = 1
            save_labels(labels)
            i += 1
        elif key == ord("n"):
            labels[name] = 0
            save_labels(labels)
            i += 1
        elif key == ord("s"):
            i += 1
        elif key == ord("b"):
            i = max(0, i - 1)
        elif key == ord("q"):
            break
    cv2.destroyAllWindows()
    n_tram = sum(labels.values())
    print(f"saved: {len(labels)} labeled ({n_tram} tram, {len(labels) - n_tram} no tram)")


if __name__ == "__main__":
    main()
