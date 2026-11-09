"""
Part 2: a sleep watcher. Before bed you hand the night over, while you sleep the camera
counts tossing and turning and the microphone measures how loud the room is, and in the
morning Qwen tells you whether you moved more when the room was noisier.

    python sleep_watch.py                        # bedtime hand-off, watch until Ctrl-C, then the morning report
    python sleep_watch.py --until 07:00          # stop on its own at 7 am and give the report
    python sleep_watch.py --voice                # ask out loud at bedtime (needs faster-whisper, see Lab 3)
    python sleep_watch.py --interval 10          # one look every 10 s instead of 5
    python sleep_watch.py --settle 300           # give yourself 5 minutes to fall asleep before counting
    python sleep_watch.py --morning              # skip the night, just report on the last sleep_log.jsonl
    python sleep_watch.py --morning --say        # ...and read the report aloud (Piper voice from Lab 3)
    python sleep_watch.py --tts en_US-hfc_female-medium   # another Piper voice (default: en_GB-jenny_dioco-medium)
    python sleep_watch.py --morning --log fake.jsonl   # report on another log

The night starts counting 2 minutes after the hand-off (--settle). Fake a night first: run it with --settle 5, toss around in view of the camera, clap a few
times, Ctrl-C, and check the report. Start the real night inside tmux (see Part H).

How it decides things:
  * Movement: every --interval seconds, YOLO looks for the person (people only). The frame is
    compared with the previous look inside the person's box (or the whole frame if YOLO cannot
    find you under the blanket). A big enough change, or the box jumping/flipping shape, is one
    toss. Tosses closer together than --cooldown seconds count as one.
  * Sound: the mic is read continuously and turned into loudness in dBFS (0 is the loudest the
    mic can record, quiet rooms sit around -60). It is relative, not a calibrated dB meter.
    Each look records the average and the peak since the previous look.
  * The arithmetic (counts, noisy vs quiet, correlation) is done here in Python. Qwen only gets
    the finished numbers and writes the words, because a 0.8B model is bad at maths.

Writes sleep_log.jsonl (one JSON object per line) and, in the morning, a graph of the night
next to it (sleep_YYYYMMDD-HHMM.png): movement on top, loudness below, with the three
busiest moments shaded and labelled with how loud the room was then. No photos are saved.
"""
import argparse
import collections
import datetime
import json
import math
import pathlib
import shutil
import subprocess
import sys
import threading
import time

import cv2
import numpy as np
import requests

# ---------------------------------------------------------------- talking to the person

# Piper from Lab 3 (voices live in Lab 3/voices), a British English woman's voice by default.
# Falls back to espeak-ng.
LAB3 = pathlib.Path(__file__).resolve().parent.parent / "Lab 3"
VOICE, SPEAKER = "en_GB-jenny_dioco-medium", 0     # --length-scale below sets the pace: under 1 is faster


def say(text, enabled=True):
    print(f"[pi] {text}", flush=True)
    if not enabled:
        return
    model = LAB3 / "voices" / f"{VOICE}.onnx"
    if model.exists():
        rate = json.load(open(f"{model}.json"))["audio"]["sample_rate"]
        piper = subprocess.Popen([str(LAB3 / ".venv" / "bin" / "python"), "-m", "piper", "--model", VOICE,
                                  "--data-dir", str(LAB3 / "voices"), "--speaker", str(SPEAKER),
                                  "--length-scale", "0.85", "--output-raw", "--", text],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        subprocess.run(["aplay", "-q", "-r", str(rate), "-f", "S16_LE", "-t", "raw", "-"],
                       stdin=piper.stdout, stderr=subprocess.DEVNULL)
        piper.wait()
    elif shutil.which("espeak-ng"):
        subprocess.run(["espeak-ng", "-s", "140", text], stderr=subprocess.DEVNULL)


def listen_once(seconds=15, pause=1.5):
    """Record one sentence and transcribe it with faster-whisper (Lab 3). None if unavailable.

    Listens for up to `seconds`, and stops early once you have spoken and then been quiet for
    `pause` seconds. Speech means 10 dB louder than the room sounded in the first half second.
    """
    try:
        import sounddevice as sd
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper is not installed in this venv: falling back to typing", flush=True)
        return None
    print(f"listening (up to {seconds} s, stops when you pause)...", flush=True)
    blocks, levels, spoke, quiet = [], [], False, 0.0
    with sd.InputStream(samplerate=16000, channels=1, dtype="float32", blocksize=1600) as stream:
        while len(blocks) < seconds * 10:                    # 0.1 s blocks
            block, _ = stream.read(1600)
            blocks.append(block[:, 0].copy())
            levels.append(20 * math.log10(max(float(np.sqrt(np.mean(block ** 2))), 1e-6)))
            if len(levels) <= 5:                             # the first half second is the room on its own
                continue
            if levels[-1] > np.median(levels[:5]) + 10:
                spoke, quiet = True, 0.0
            elif spoke:
                quiet += 0.1
                if quiet >= pause:
                    break
    audio = np.concatenate(blocks)
    print(f"heard {len(audio) / 16000:.1f} s, transcribing...", flush=True)
    segments, _ = WhisperModel("tiny.en", device="cpu", compute_type="int8").transcribe(audio, beam_size=1)
    return " ".join(s.text.strip() for s in segments).strip() or None


def bedtime(args):
    """The hand-off: the person says what they want to know, the device acknowledges and dims."""
    say("Hi. What would you like me to watch tonight?", args.speak)
    request = listen_once(args.listen) if args.voice else None
    if request is None:
        request = input("(type it, or press Enter for the default) > ").strip()
    if not request:
        request = "Do I toss and turn more when the room is noisier?"
    print(f"[you] {request}", flush=True)
    say(f"Okay. I will count your tossing and turning and listen to the room. "
        f"I start counting in {args.settle // 60 or args.settle} "
        f"{'minutes' if args.settle >= 60 else 'seconds'}. Good night.", args.speak)
    return request


# ---------------------------------------------------------------- the night shift

class SoundMeter:
    """Reads the mic in the background and keeps loudness (dBFS) per 0.1 s block."""

    def __init__(self, rate=16000):
        self.blocks = collections.deque(maxlen=6000)    # 10 minutes of blocks, more than one interval needs
        self.lock = threading.Lock()
        self.stream = None
        try:
            import sounddevice as sd
            self.stream = sd.InputStream(samplerate=rate, channels=1, blocksize=rate // 10,
                                         dtype="float32", callback=self._callback)
            self.stream.start()
        except Exception as e:                           # no mic plugged in: keep watching, log sound as null
            print("no microphone, sound will not be logged:", e, flush=True)

    def _callback(self, data, frames, t, status):
        rms = float(np.sqrt(np.mean(data[:, 0] ** 2)))
        with self.lock:
            self.blocks.append(20 * math.log10(max(rms, 1e-6)))

    def take(self):
        """Average and peak dBFS since the last call, or (None, None)."""
        with self.lock:
            levels = list(self.blocks)
            self.blocks.clear()
        if not levels:
            return None, None
        energy = np.mean([10 ** (db / 10) for db in levels])       # average the power, not the decibels
        return round(10 * math.log10(energy), 1), round(max(levels), 1)

    def close(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()


def brighten(frame, dark, gamma):
    """Lift a dark frame with a gamma curve so YOLO and the motion check can see something.

    Gamma lifts the shadows without stretching the sensor noise as much as a plain gain does
    (measured on this webcam: a still dark room stays under 1% changed pixels). Frames that are
    bright enough on average are left alone. Returns the frame and whether it was brightened.
    """
    if dark <= 0 or cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).mean() >= dark:
        return frame, False
    lut = (255 * (np.arange(256) / 255) ** gamma).astype(np.uint8)
    return cv2.LUT(frame, lut), True


def find_person(model, frame):
    """The largest person box as (x1, y1, x2, y2), or None."""
    r = model.predict(frame, imgsz=320, conf=0.3, classes=[0], verbose=False)[0]   # lower conf: a sleeper is half hidden
    if not len(r.boxes):
        return None
    boxes = r.boxes.xyxy.tolist()
    return max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))


def motion_in(prev, gray, box):
    """Fraction of pixels that changed between two looks, inside the (padded) box."""
    h, w = gray.shape
    if box:
        x1, y1, x2, y2 = box
        px, py = 0.15 * (x2 - x1), 0.15 * (y2 - y1)
        x1, y1 = int(max(0, x1 - px)), int(max(0, y1 - py))
        x2, y2 = int(min(w, x2 + px)), int(min(h, y2 + py))
    else:
        x1, y1, x2, y2 = 0, 0, w, h
    diff = cv2.absdiff(prev[y1:y2, x1:x2], gray[y1:y2, x1:x2])
    return float(np.mean(diff > 25))


def box_jump(a, b, w):
    """True when the person box moved a lot or changed shape (lying on the back vs the side)."""
    if not a or not b:
        return False
    ca, cb = (a[0] + a[2]) / 2, (b[0] + b[2]) / 2
    ra = (a[2] - a[0]) / max(1, a[3] - a[1])
    rb = (b[2] - b[0]) / max(1, b[3] - b[1])
    return abs(ca - cb) > 0.1 * w or abs(math.log(max(ra, 1e-3) / max(rb, 1e-3))) > 0.4


def night(args, request):
    from yolo_to_qwen import model                  # the YOLO model you exported in Part A

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        raise SystemExit("no webcam found: is it plugged in?")
    meter = SoundMeter()
    log = open(args.log, "w")                             # a new night starts a new log

    def write(entry):
        log.write(json.dumps(entry) + "\n")
        log.flush()

    write({"t": datetime.datetime.now().isoformat(timespec="seconds"), "start": True,
           "request": request, "interval": args.interval})
    stop_at = None
    if args.until:
        hh, mm = map(int, args.until.split(":"))
        stop_at = datetime.datetime.now().replace(hour=hh, minute=mm, second=0, microsecond=0)
        if stop_at <= datetime.datetime.now():
            stop_at += datetime.timedelta(days=1)
        print(f"will stop at {stop_at:%a %H:%M}", flush=True)

    for left in range(args.settle, 0, -1):          # 2 minutes by default, counted down on screen
        if left % 30 == 0 or left <= 5:
            print(f"starting in {left // 60}:{left % 60:02d}", flush=True)
        time.sleep(1)
    meter.take()                                   # throw away the noise of getting into bed
    print("watching, Ctrl-C to stop", flush=True)
    prev_gray, prev_box, last_toss, last_beat = None, None, 0.0, 0.0
    try:
        while stop_at is None or datetime.datetime.now() < stop_at:
            try:
                for _ in range(4):                   # the webcam buffers a few frames; skip the stale ones
                    cap.grab()
                ok, frame = cap.read()
                if not ok:
                    raise RuntimeError("no frame")
                frame, dark = brighten(frame, args.dark, args.gamma)
                gray =cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
                box = find_person(model, frame)
                motion, toss, light = 0.0, False, False
                if prev_gray is not None:
                    whole = float(np.mean(cv2.absdiff(prev_gray, gray) > 25))
                    light = whole > 0.6              # nearly every pixel changed: a lamp, not a person
                    motion = motion_in(prev_gray, gray, box or prev_box)
                    moved = not light and (motion > args.motion or box_jump(prev_box, box, gray.shape[1]))
                    if moved and time.time() - last_toss > args.cooldown:
                        toss, last_toss = True, time.time()
                db_avg, db_peak = meter.take()
                entry = {"t": datetime.datetime.now().isoformat(timespec="seconds"),
                         "person": box is not None, "motion": round(motion, 3), "toss": toss,
                         "db": db_avg, "peak": db_peak}
                if light:
                    entry["light"] = True
                if dark:
                    entry["dark"] = True
                write(entry)
                if toss or args.verbose:
                    print(f'{entry["t"][11:]} motion={motion:.3f} toss={toss} db={db_avg} peak={db_peak}'
                          f'{" person" if box else ""}{" dark" if dark else ""}', flush=True)
                if time.time() - last_beat > 600:
                    print(f'{entry["t"][11:]} still watching', flush=True)
                    last_beat = time.time()
                prev_gray, prev_box = gray, box or prev_box
                time.sleep(args.interval)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print("hiccup:", e, flush=True)
                time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    write({"t": datetime.datetime.now().isoformat(timespec="seconds"), "stop": True})
    cap.release()
    meter.close()
    log.close()
    print("night shift stopped", flush=True)


# ---------------------------------------------------------------- the morning

def analyse(entries, noisy_margin):
    """All the numbers the morning report needs, computed here rather than by the language model."""
    looks = [e for e in entries if "toss" in e]
    start = next((e for e in entries if e.get("start")), {})
    if not looks:
        return None
    t0, t1 = looks[0]["t"], looks[-1]["t"]
    hours = (datetime.datetime.fromisoformat(t1) - datetime.datetime.fromisoformat(t0)).total_seconds() / 3600
    tosses = [e for e in looks if e["toss"]]
    heard = [e for e in looks if e.get("db") is not None]
    facts = {
        "request": start.get("request", "Do I toss and turn more when the room is noisier?"),
        "from": t0[11:16], "to": t1[11:16], "hours": round(hours, 1),
        "tosses": len(tosses),
        "tosses_per_hour": round(len(tosses) / hours, 1) if hours > 0 else None,
        "seen_in_bed_pct": round(100 * sum(e["person"] for e in looks) / len(looks)),
        "toss_times": [e["t"][11:16] for e in tosses][:40],
    }
    per_hour = collections.OrderedDict()
    for e in looks:
        h = per_hour.setdefault(e["t"][11:13] + ":00", {"tosses": 0, "db": []})
        h["tosses"] += e["toss"]
        if e.get("db") is not None:
            h["db"].append(e["db"])
    facts["per_hour"] = {k: {"tosses": v["tosses"],
                             "avg_db": round(float(np.median(v["db"])), 1) if v["db"] else None}
                         for k, v in per_hour.items()}
    if not heard:
        facts["sound"] = "no microphone data"
        return facts

    dbs = np.array([e["db"] for e in heard])
    peaks = np.array([e["peak"] for e in heard])
    baseline = float(np.percentile(dbs, 20))         # what a quiet moment in this room sounds like
    noisy = peaks > baseline + noisy_margin          # a look counts as noisy if something stood out of the baseline
    toss = np.array([e["toss"] for e in heard])
    n_noisy, n_quiet = int(noisy.sum()), int((~noisy).sum())
    rate = lambda mask: float(toss[mask].sum()) / mask.sum() if mask.sum() else None
    r_noisy, r_quiet = rate(noisy), rate(~noisy)

    # Tosses that came within a minute after a noisy moment: did a sound wake you?
    times = [datetime.datetime.fromisoformat(e["t"]) for e in heard]
    noisy_times = [t for t, n in zip(times, noisy) if n]
    after_noise = sum(1 for t, e in zip(times, heard) if e["toss"] and
                      any(0 <= (t - nt).total_seconds() <= 60 for nt in noisy_times))

    # 10-minute bins: correlation between how loud a bin was and how much you moved in it
    bins = collections.defaultdict(lambda: [[], 0])
    for t, e in zip(times, heard):
        key = t.replace(minute=t.minute // 10 * 10, second=0)
        bins[key][0].append(e["db"])
        bins[key][1] += e["toss"]
    loud = np.array([np.mean(v[0]) for v in bins.values()])
    moves = np.array([v[1] for v in bins.values()])
    corr = None
    if len(bins) >= 4 and loud.std() > 0 and moves.std() > 0:
        corr = round(float(np.corrcoef(loud, moves)[0, 1]), 2)

    if r_noisy is None or r_quiet is None or len(tosses) < 3:
        verdict = "not enough tossing or not enough noisy moments to compare"
    elif r_noisy > 1.5 * r_quiet:
        verdict = "tossed MORE when it was noisy"
    elif r_quiet > 1.5 * r_noisy:
        verdict = "tossed LESS when it was noisy"
    else:
        verdict = "tossed about the SAME whether it was noisy or quiet"

    loudest = max(heard, key=lambda e: e["peak"])
    full = [k for k, v in bins.items() if len(v[0]) >= 0.5 * len(max(bins.values(), key=lambda v: len(v[0]))[0])]
    quiet = min(full, key=lambda k: np.mean(bins[k][0]))      # the calmest 10 minutes (skip a cut-off last bin)
    facts.update({
        "sound": "dBFS, relative: about -60 is a silent room, -30 is talking nearby, 0 is the loudest the mic records",
        "night_avg_db": round(10 * math.log10(np.mean(10 ** (dbs / 10))), 1),
        "quiet_baseline_db": round(baseline, 1),
        "loudest_moment": f'{loudest["t"][11:16]} at {loudest["peak"]} dB',
        "noisiest_time": loudest["t"][11:16],
        "quietest_time": f"{quiet:%H:%M} to {quiet + datetime.timedelta(minutes=10):%H:%M}",
        "noisy_minutes": round(n_noisy * start.get("interval", 5) / 60),
        "tosses_per_100_noisy_looks": round(100 * r_noisy, 1) if r_noisy is not None else None,
        "tosses_per_100_quiet_looks": round(100 * r_quiet, 1) if r_quiet is not None else None,
        "tosses_within_1_min_after_noise": after_noise,
        "loudness_vs_movement_correlation_10min": corr,
        "verdict": verdict,
    })
    if r_noisy is not None and r_quiet is not None and r_quiet > 0:
        facts["comparison"] = (f"after a noisy moment you moved {r_noisy / r_quiet:.1f} times as often as in quiet moments; "
                               f"{after_noise} of your {len(tosses)} tosses came within a minute of a noise")
    return facts



def plot_night(entries, facts, args):
    """Save a picture of the night: movement and loudness as two overlapping lines on one chart.

    The busiest moments of movement are shaded, so you can see whether the room was noisy
    when you moved. Returns the path of the PNG.
    """
    import matplotlib
    matplotlib.use("Agg")                            # no window needed, so it works over ssh
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    BLUE, BLUE_DARK, ORANGE, ORANGE_DARK = "#2a78d6", "#184f95", "#eb6834", "#b8461c"
    INK, MUTED, GRID, SURFACE = "#1a1a19", "#6b6a63", "#e6e5df", "#fcfcfb"

    looks = [e for e in entries if "toss" in e]
    times = [datetime.datetime.fromisoformat(e["t"]) for e in looks]
    t0 = times[0]
    interval = next((e for e in entries if e.get("start")), {}).get("interval", 5)
    span = (times[-1] - t0).total_seconds()
    step = 60 if span > 1800 else interval          # a real night: one point per minute; a fake one: every look

    bins = collections.OrderedDict()                 # bin start -> motion values, loudness values, peaks
    for t, e in zip(times, looks):
        key = t0 + datetime.timedelta(seconds=(t - t0).total_seconds() // step * step)
        b = bins.setdefault(key, {"motion": [], "db": [], "peak": [], "toss": 0})
        b["motion"].append(100 * e["motion"])
        b["toss"] += e["toss"]
        if e.get("db") is not None:
            b["db"].append(e["db"])
            b["peak"].append(e["peak"])
    bt = list(bins)
    motion = [max(b["motion"]) for b in bins.values()]      # the biggest change in each bin
    activity = [sum(b["motion"]) for b in bins.values()]     # how much moving there was in it overall
    db = [10 * math.log10(np.mean([10 ** (d / 10) for d in b["db"]])) if b["db"] else np.nan for b in bins.values()]
    peak = [max(b["peak"]) if b["peak"] else np.nan for b in bins.values()]

    # The three busiest moments, at least 10 bins apart so they are three different episodes
    busiest = []
    for i in sorted(range(len(activity)), key=lambda i: -activity[i]):
        if activity[i] <= 0 or len(busiest) == 3:
            break
        if all(abs(i - j) >= 10 for j in busiest):
            busiest.append(i)
    half = datetime.timedelta(seconds=max(step, span / 120))   # wide enough to see on an 8-hour axis

    # One chart, two lines. Movement (% of the picture) and loudness (dB) have different units, so
    # each is drawn on its own 0-100 scale: 0 is its lowest point of the night, 100 its highest.
    def scale(values, lo=None, hi=None):
        arr = np.array(values, dtype=float)
        lo = np.nanmin(arr) if lo is None else lo
        hi = np.nanmax(arr) if hi is None else hi
        return (arr - lo) / (hi - lo) * 100 if hi > lo else arr * 0

    fig, ax = plt.subplots(figsize=(11, 4.8), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    for i in busiest:
        ax.axvspan(bt[i] - half, bt[i] + half, color="#efeee8", zorder=0)

    heard = any(not np.isnan(p) for p in peak)
    if heard:
        # Noise: the loudest sound in each bin, so a door or a car shows up as a spike like a toss does
        lo, hi = np.nanmin(peak), np.nanmax(peak)
        threshold = facts["quiet_baseline_db"] + args.noisy_margin
        ax.plot(bt, scale(peak, lo, hi), color=ORANGE, linewidth=1.5, alpha=0.9, zorder=2,
                label=f"loudest sound ({lo:.0f} to {hi:.0f} dB)")
        if lo < threshold < hi:
            y = (threshold - lo) / (hi - lo) * 100
            ax.axhline(y, color=ORANGE_DARK, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
            ax.text(bt[0], y, f" noisy above {threshold:.0f} dB", color=ORANGE_DARK, fontsize=8, va="bottom")
    else:
        ax.text(0.5, 0.92, "no microphone data", transform=ax.transAxes, ha="center", color=MUTED, fontsize=9)

    # Movement on top of it, with each counted toss marked
    mhi = max(motion) if max(motion) > 0 else 1
    m = scale(motion, 0, mhi)
    ax.plot(bt, m, color=BLUE, linewidth=2, zorder=3, label=f"movement (0 to {mhi:.0f}% of the picture changed)")
    toss_bins = [i for i, b in enumerate(bins.values()) if b["toss"]]
    ax.scatter([bt[i] for i in toss_bins], [m[i] for i in toss_bins], s=40, color=BLUE_DARK,
               edgecolor=SURFACE, linewidth=1.5, zorder=4, label=f"counted toss ({facts['tosses']})")

    # Label the busiest moments with how loud the room was right then
    for rank, i in enumerate(busiest, 1):
        noise = f", peak {peak[i]:.0f} dB" if not np.isnan(peak[i]) else ""
        ax.annotate(f"#{rank} {bt[i]:%H:%M}{noise}", (bt[i], 100), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=8, color=INK)

    ax.set_ylim(0, 118)                              # headroom for the labels of the busiest moments
    ax.set_yticks([0, 50, 100], ["lowest", "", "highest"])
    ax.legend(loc="lower right", bbox_to_anchor=(1, 1), ncol=3, frameon=False, fontsize=9, labelcolor=INK)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M" if span > 1800 else "%H:%M:%S"))
    fig.suptitle(f"Night of {t0:%a %d %b}, {facts['from']} to {facts['to']}: {facts['tosses']} tosses, "
                 f"{facts.get('verdict', 'no sound to compare')}",
                 x=0.06, y=1.02, ha="left", color=INK, fontsize=12, fontweight="bold")
    fig.text(0.06, 0.955, "Each line is scaled to its own range for the night. "
             "Shaded: the three moments with the most movement, labelled with how loud the room was then",
             color=MUTED, fontsize=9)
    path = str(pathlib.Path(args.log).with_name(f"sleep_{t0:%Y%m%d-%H%M}.png"))
    fig.savefig(path, dpi=120, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


# What Qwen is told. The decibel numbers stay in the printout and the graph, out of the spoken report.
TOLD = ("request", "from", "to", "hours", "tosses", "tosses_per_hour", "seen_in_bed_pct",
        "noisiest_time", "quietest_time", "verdict", "comparison")


def morning(args):
    try:
        entries = [json.loads(line) for line in open(args.log) if line.strip()]
    except FileNotFoundError:
        raise SystemExit(f"no {args.log} yet: run a night first")
    facts = analyse(entries, args.noisy_margin)
    if facts is None:
        say("Good morning. I did not record anything last night, so I have nothing to report.", args.say)
        return
    print(json.dumps(facts, indent=2))
    print(f"\ngraph of the night saved to {plot_night(entries, facts, args)}")

    if facts["tosses"] == 0 and facts["seen_in_bed_pct"] == 0:
        # honest about a night where the camera never saw anyone: do not let the model invent one
        say(f'Good morning. I watched from {facts["from"]} to {facts["to"]} but never saw you in bed, '
            f'so I cannot say how you slept.' + (f' It was noisiest at {facts["noisiest_time"]} and quietest '
            f'from {facts["quietest_time"]}.' if "noisiest_time" in facts else ""), args.say)
        return

    prompt = f"""You are a gentle bedside sleep device talking to someone who just woke up.
Last night they asked you: "{facts['request']}"
You watched them with a camera and listened to the room with a microphone. These are the measured facts:

{json.dumps({k: v for k, v in facts.items() if k in TOLD}, indent=1)}

Write a short morning report of at most four sentences, speaking to them as "you":
1. How many times they tossed and turned, and roughly how restless that is.
2. When the room was noisiest and when it was quietest (say the times; no decibel numbers).
3. Answer their question using the verdict and the comparison sentence.
Use only these facts and these numbers; do not guess the current time. Do not give medical advice."""
    print("\nasking Qwen...", flush=True)
    t0 = time.time()
    r = requests.post("http://localhost:11434/api/generate", json={
        "model": args.model,
        "prompt": prompt,
        "think": False,
        "stream": False,
        "options": {"num_ctx": 4096, "temperature": 0.1, "num_predict": 250},
    }, timeout=600)
    r.raise_for_status()
    answer = r.json()["response"].strip()
    print(f"\nQwen ({time.time() - t0:.1f} s):")
    say(answer, args.say)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--morning", action="store_true", help="only give the report on the last log")
    parser.add_argument("--until", help="stop on its own at this time, HH:MM")
    parser.add_argument("--interval", type=float, default=5, help="seconds between looks")
    parser.add_argument("--settle", type=int, default=120, help="seconds to wait after the hand-off before counting")
    parser.add_argument("--motion", type=float, default=0.04,
                        help="fraction of the person's pixels that must change to count as a toss")
    parser.add_argument("--cooldown", type=float, default=30, help="tosses closer than this many seconds count once")
    parser.add_argument("--dark", type=float, default=40,
                        help="brighten frames whose average brightness (0-255) is below this; 0 turns it off")
    parser.add_argument("--gamma", type=float, default=0.4,
                        help="how hard to brighten dark frames: lower is brighter but noisier")
    parser.add_argument("--noisy-margin", type=float, default=15,
                        help="dB above the night's quiet baseline that makes a moment noisy")
    parser.add_argument("--voice", action="store_true", help="speak the bedtime request instead of typing it")
    parser.add_argument("--listen", type=float, default=15,
                        help="with --voice: listen for up to this many seconds (stops early when you pause)")
    parser.add_argument("--quiet", dest="speak", action="store_false", help="no spoken acknowledgement at bedtime")
    parser.add_argument("--say", action="store_true", help="read the morning report aloud")
    parser.add_argument("--verbose", action="store_true", help="print every look, not only tosses")
    parser.add_argument("--model", default="qwen3.5:0.8b")
    parser.add_argument("--tts", default=VOICE, help="Piper voice in Lab 3/voices (default: en_GB-jenny_dioco-medium, a British woman's voice)")
    parser.add_argument("--log", default="sleep_log.jsonl")
    args = parser.parse_args()
    VOICE = args.tts
    sys.stdout.reconfigure(errors="replace")         # a latin-1 terminal (tmux) would crash on Qwen's dashes

    if not args.morning:
        night(args, bedtime(args))
        args.say = args.say or args.speak            # the person spoke to it at night: answer out loud in the morning
    morning(args)
