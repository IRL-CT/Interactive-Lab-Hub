"""
tram_burst.py: grab a burst of photos when YOU see the tram go by.

    python tram_burst.py                  # press ENTER when you see a tram; q + ENTER to quit
    python tram_burst.py --count 80       # more photos per burst

The camera runs the whole time and remembers the last few seconds, so pressing ENTER saves
the moment before you reacted too (--preroll), then keeps saving every 0.5 s (--every) until
--count photos. Bursts go into tram_data/ like everything else, named HHMMSS_mmm.jpg, so
tram_label.py finds them; label them fast with:

    python tram_label.py --bursts

Don't run this while tram_collect.py or tram_watch.py is running: only one program can use
the camera at a time. Try to also catch a few trams at dusk and at night, not just in daylight.
"""
import argparse
import collections
import datetime
import queue
import threading
import time

import cv2

from tram_common import DATA, Exposure, crop, grab, load_config, open_cam


def save(img, t):
    folder = DATA / t.strftime("%Y%m%d")
    folder.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(folder / (t.strftime("%H%M%S_") + f"{t.microsecond // 1000:03d}.jpg")), img,
                [cv2.IMWRITE_JPEG_QUALITY, 90])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50, help="photos per burst")
    parser.add_argument("--every", type=float, default=0.5, help="seconds between burst photos")
    parser.add_argument("--preroll", type=float, default=3, help="seconds before ENTER to keep")
    args = parser.parse_args()

    cfg = load_config()
    cap = open_cam(cfg)
    exposure = Exposure(cap, cfg)
    keys = queue.Queue()

    def read_keys():
        try:
            while True:
                keys.put(input().strip())
        except (EOFError, OSError):
            keys.put("q")

    threading.Thread(target=read_keys, daemon=True).start()
    history = collections.deque()            # (time, crop) for the last --preroll seconds
    bursts = saved_total = 0
    print("warming up the exposure for 10 s...", flush=True)
    warm_until = time.time() + 10
    burst_left, next_save = 0, 0.0

    try:
        while True:
            try:
                img = crop(grab(cap, cfg), cfg)
            except RuntimeError as e:
                print("hiccup:", e, flush=True)
                time.sleep(0.5)
                continue
            now = datetime.datetime.now()
            if burst_left == 0:
                exposure.update(img)          # don't change exposure in the middle of a burst
            history.append((now, img))
            while history and (now - history[0][0]).total_seconds() > args.preroll:
                history.popleft()

            if warm_until and time.time() > warm_until:
                warm_until = 0
                print("ready. Press ENTER when you see a tram (q + ENTER to quit).", flush=True)

            try:
                key = keys.get_nowait()
            except queue.Empty:
                key = None
            if key == "q":
                break
            if key is not None and not warm_until and burst_left == 0:
                bursts += 1
                last = None
                for t, im in list(history)[:-1]:            # the seconds before you pressed
                    if last is None or (t - last).total_seconds() >= args.every:
                        save(im, t)
                        saved_total += 1
                        last = t
                burst_left, next_save = args.count, 0.0
                print(f"{now:%H:%M:%S} burst {bursts}: saving...", flush=True)

            if burst_left and time.time() >= next_save:
                save(img, now)
                saved_total += 1
                burst_left -= 1
                next_save = time.time() + args.every
                if burst_left == 0:
                    print(f"{datetime.datetime.now():%H:%M:%S} burst {bursts} done "
                          f"({saved_total} photos so far). ENTER for the next tram.", flush=True)
            time.sleep(0.05)
    except (KeyboardInterrupt, EOFError):
        pass
    cap.release()
    print(f"done: {bursts} bursts, {saved_total} photos. Label them: python tram_label.py --bursts")


if __name__ == "__main__":
    main()
