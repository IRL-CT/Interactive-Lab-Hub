"""
tram_collect.py: point the camera at the tram, mark where it runs, and collect training images.

    python tram_collect.py --setup --rotate none   # click an outline around the tram's path (Pi desktop)
    python tram_collect.py --setup --mirror on     # same, but un-mirror a webcam that flips left/right
    python tram_collect.py --exposure-test         # watch our exposure control settle (60 s)
    python tram_collect.py --minutes 45            # one session right now: a crop every 4 s for 45 min
    python tram_collect.py --plan                  # all four sessions, each at its time, then stop
    python tram_collect.py --plan --times 06:15 12:30 18:15 22:30   # choose your own times

The default plan is four 45-minute sessions: early morning (06:15), day (12:30),
evening (18:15) and night (22:30). Sessions whose time already passed today run tomorrow.
That is ~675 images per session, ~2700 total, covering every kind of light.
Run --plan inside tmux so it survives closing your laptop.

Only the marked box is saved, shrunk to 320 px wide: no street, no cars, no windows.
Images go to tram_data/YYYYMMDD/HHMMSS.jpg.
"""
import argparse
import datetime
import time

import cv2
import numpy as np

from tram_common import DATA, ROTATIONS, Exposure, crop, grab, load_config, open_cam, save_config


def setup(args):
    cfg = load_config(required=False)
    cfg["width"], cfg["height"] = args.width, args.height
    if args.crop_width:
        cfg["crop_width"] = args.crop_width
    if args.rotate:
        cfg["rotate"] = None if args.rotate == "none" else args.rotate
    if args.mirror is not None:
        cfg["mirror"] = args.mirror == "on"
    cap = open_cam(cfg)
    frame = grab(cap, cfg)
    cap.release()
    print(f"camera gives {frame.shape[1]}x{frame.shape[0]} (asked for {args.width}x{args.height})",
          flush=True)

    # show the frame at most 1000 px wide so it fits the screen, but keep full-size coordinates
    scale = min(1.0, 1000 / frame.shape[1])
    small = cv2.resize(frame, None, fx=scale, fy=scale)
    clicks = []

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            clicks.append((x, y))

    title = "tram setup"
    cv2.namedWindow(title)
    cv2.setMouseCallback(title, on_mouse)
    print("Click points around the tram's path, like tracing an outline (6-10 points is plenty;\n"
          "leave room for the cabin hanging below the cable), then press ENTER.\n"
          "Exactly 2 clicks = a plain rectangle instead. u = undo last point, r = redo, q = quit.\n"
          "Everything outside the outline is blacked out and never saved.", flush=True)
    while True:
        view = small.copy()
        for c in clicks:
            cv2.circle(view, c, 4, (0, 255, 255), -1)
        if len(clicks) == 2:
            cv2.rectangle(view, clicks[0], clicks[1], (0, 255, 255), 1)
        if len(clicks) >= 3:
            cv2.polylines(view, [np.array(clicks, np.int32)], True, (0, 255, 255), 2)
        cv2.imshow(title, view)
        key = cv2.waitKey(50) & 0xFF
        if key == ord("r"):
            clicks.clear()
        elif key == ord("u") and clicks:
            clicks.pop()
        elif key == ord("q"):
            raise SystemExit("quit; nothing saved")
        elif key in (13, 10, 32) and len(clicks) >= 2:
            pts = [(int(px / scale), int(py / scale)) for px, py in clicks]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            x, y, w, h = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
            if w > 10 and h > 10:
                break
            print("outline too small, click again", flush=True)
            clicks.clear()
    cv2.destroyAllWindows()
    cfg["roi"] = [x, y, w, h]
    if len(pts) >= 3:
        cfg["polygon"] = [list(p) for p in pts]
    else:
        cfg.pop("polygon", None)
    save_config(cfg)
    cv2.imwrite("tram_preview.jpg", crop(frame, cfg))
    shape = f"outline of {len(pts)} points" if len(pts) >= 3 else "rectangle"
    print(f"saved tram_config.json ({shape}, {w}x{h} px) and tram_preview.jpg (what gets saved)")


def settle(cap, cfg, exposure, seconds=20):
    """Let our exposure controller find a good level before saving anything."""
    end = time.time() + seconds
    while time.time() < end:
        try:
            exposure.update(crop(grab(cap, cfg), cfg))
        except RuntimeError:
            time.sleep(0.5)


def exposure_test(args):
    """Show the box's brightness and the exposure for 60 s, so you can see it settle."""
    cfg = load_config()
    cap = open_cam(cfg)
    exposure = Exposure(cap, cfg)
    end = time.time() + 60
    while time.time() < end:
        img = crop(grab(cap, cfg), cfg)
        exposure.update(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inside = gray[img.max(axis=2) > 0]
        level = float(np.median(inside if inside.size else gray))
        print(f"box brightness {level:5.1f} (target {exposure.target})   {exposure.status()}",
              flush=True)
        cv2.imwrite("tram_preview.jpg", img)
        time.sleep(0.5)
    cap.release()
    print("tram_preview.jpg shows the last frame")


def session(cap, cfg, every, minutes, name="", exposure=None):
    """Save a crop every `every` seconds for `minutes` minutes."""
    if exposure:
        settle(cap, cfg, exposure)
    stop = time.time() + minutes * 60
    n = 0
    print(f"{datetime.datetime.now():%H:%M:%S} session {name} started: every {every} s for "
          f"{minutes} min", flush=True)
    while time.time() < stop:
        t0 = time.time()
        try:
            img = crop(grab(cap, cfg), cfg)
        except RuntimeError as e:
            print("hiccup:", e, flush=True)
            time.sleep(every)
            continue
        if exposure:
            exposure.update(img)
        now = datetime.datetime.now()
        folder = DATA / now.strftime("%Y%m%d")
        folder.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(folder / now.strftime("%H%M%S.jpg")), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        n += 1
        if n % 75 == 0:                               # about every 5 minutes at 4 s
            print(f"{now:%H:%M:%S} {n} images" + (f" ({exposure.status()})" if exposure else ""),
                  flush=True)
        time.sleep(max(0.0, every - (time.time() - t0)))
    print(f"{datetime.datetime.now():%H:%M:%S} session {name} done: {n} images", flush=True)
    return n


def plan(times, now):
    """(start datetime, label) for each session, in order; past times move to tomorrow."""
    out = []
    for hhmm in times:
        h, m = map(int, hhmm.split(":"))
        t = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if t + datetime.timedelta(minutes=1) < now:
            t += datetime.timedelta(days=1)
        out.append((t, hhmm))
    return sorted(out)


def collect(args):
    cfg = load_config()
    if "roi" not in cfg:
        raise SystemExit("no box yet: run `python tram_collect.py --setup` first")
    cap = open_cam(cfg)
    exposure = Exposure(cap, cfg)
    total = 0
    try:
        if args.plan:
            sessions = plan(args.times, datetime.datetime.now())
            print("plan: " + ", ".join(f"{t:%a %H:%M}" for t, _ in sessions), flush=True)
            for start, label in sessions:
                wait = (start - datetime.datetime.now()).total_seconds()
                if wait > 0:
                    print(f"waiting until {start:%a %H:%M} for the {label} session...", flush=True)
                    # keep the camera awake: some webcams drift or sleep if left unread for hours
                    while (start - datetime.datetime.now()).total_seconds() > 0:
                        cap.grab()
                        time.sleep(5)
                total += session(cap, cfg, args.every, args.minutes, label, exposure)
        else:
            total += session(cap, cfg, args.every, args.minutes, "now", exposure)
    except KeyboardInterrupt:
        pass
    cap.release()
    print(f"done: {total} images in {DATA}/", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true", help="mark the tram's box on the camera view")
    parser.add_argument("--rotate", choices=["none"] + list(ROTATIONS), help="rotate the camera view")
    parser.add_argument("--mirror", choices=["on", "off"], help="flip the view left/right (setup)")
    parser.add_argument("--width", type=int, default=1280, help="camera width to ask for (setup)")
    parser.add_argument("--height", type=int, default=720, help="camera height to ask for (setup)")
    parser.add_argument("--crop-width", type=int, help="max width of saved crops (setup; default 320)")
    parser.add_argument("--every", type=float, default=4, help="seconds between saved crops")
    parser.add_argument("--minutes", type=float, default=45, help="length of each session")
    parser.add_argument("--exposure-test", action="store_true",
                        help="print the box brightness and exposure for 60 s")
    parser.add_argument("--plan", action="store_true", help="run the four daily sessions at --times")
    parser.add_argument("--times", nargs="+", default=["06:15", "12:30", "18:15", "22:30"],
                        help="session start times (HH:MM) for --plan")
    args = parser.parse_args()
    if args.setup:
        setup(args)
    elif args.exposure_test:
        exposure_test(args)
    else:
        collect(args)
