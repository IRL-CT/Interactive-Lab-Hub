#!/usr/bin/env python3
"""
Part H, both sensors: one night shift that listens for snoring and watches the mouth,
on one screen and in one log.

    python night_watch.py                       # audio + camera, full-screen panel
    python night_watch.py --no-camera           # audio only (dark room, no frames)
    python night_watch.py --cam-interval 5      # look at the pillow more often
    python night_watch.py --duration 60 -v      # a one-minute test, plain lines
    python night_watch.py --no-tui              # plain lines, e.g. under nohup

Two sensors, two different rhythms
----------------------------------
The microphone is continuous because sound has to be: a snore lasts a fraction of a
second, and a drop-out would delete it. The camera is *sampled* - one frame every
--cam-interval seconds (10 by default) - because a mouth that is open at 03:12 is
still open at 03:14, and holding the camera open all night costs CPU, heat and video
bandwidth for no extra information. That is the README's house rule, applied.

The two are married in the log: when a snore clip finishes, the last mouth reading is
written with it, which is the README's line

    03:12:20 snore_event 6s, mouth_open 0.41

What each sensor can and cannot say
-----------------------------------
The microphone says "this was loud, low, and lasted a while" - it cannot tell a snore
from a door. The camera says "the mouth was open 0.41" - which is not the same as
snoring either: people sleep with open mouths, and a snore can happen with the lips
shut. So neither is a diagnosis, and the log says *possible* snoring. Apnea is a stop
in airflow measured by airflow and blood-oxygen sensors; nothing here can see it.

An empty frame is not a closed mouth: with the camera working and no face in it, the
user has got up (the restroom, the morning), and the log calls that `user_leave`. A
broken camera is `camera_unknown` and `--no-camera` is `camera_off`, because blaming
the user for a dead camera would put a false story into the morning report.

Privacy: no frames are saved, ever. A frame is read, reduced to one number (the mouth
aspect ratio) and dropped, so what leaves this process is 0.41, not a picture.

The log (night_log.jsonl) is the one morning.py already reads: every line has a `t`
and a `reading` sentence, states are written when they end so each line knows its own
duration, and an `alive` line goes in every ten minutes so a quiet night is not
mistaken for a crash.

    {"t": "...", "reading": "mouth_open 0.41 for 6s", "mouth": "open", "mar": 0.41, ...}
    {"t": "...", "reading": "snore_event 6s, mouth_open 0.41", "event": "snore", ...}

The preview window
------------------
With --preview (the default when an X display exists) a second window shows the camera
itself with the numbers burnt onto it: current sound level, mouth aspect ratio, and
whether a clip is recording right now. It is the window to check that the camera really
sees the pillow, and to watch a clip start when someone snores.

Know what it costs. With the window open the camera is *streamed* and Face Mesh measures
every shown frame, instead of sampling one frame every --cam-interval; that is more CPU,
more heat, and a live picture of the room on the desktop. Right for a tuning session,
wrong for the real night - use --no-preview then, which also restores sampling.
"""
import argparse
import collections
import curses
import datetime
import json
import os
import pathlib
import queue
import signal
import sys
import threading
import time

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")   # MediaPipe is chatty on stderr

import cv2
import numpy as np
import sounddevice as sd

from mouth_open import (LEFT_CORNER, LOWER_LIP, RIGHT_CORNER, UPPER_LIP, detect, human_span,
                        mp_face_mesh, resolve_display)
from snore_monitor import (BLOCK_SECONDS, SILENCE_DB, SnoreMachine, choose_source,
                           db_bar, meter_range, pick_device, pick_rate, shown_level)

stop = False          # flipped by Ctrl-C / SIGTERM / q
PREVIEW_WINDOW = "night watch - camera"


# --------------------------------------------------------------------------- camera

def request_stop():
    """Let the camera thread (and the preview window's q key) stop the whole program."""
    global stop
    stop = True


class Shared:
    """What the audio side knows, for the preview window's overlay.

    The camera thread draws the overlay, so the numbers it needs have to cross threads;
    a dict behind a lock is small enough to copy on every frame.
    """

    def __init__(self, trigger, mouth_threshold):
        self.lock = threading.Lock()
        self.state = {"level": SILENCE_DB, "peak": SILENCE_DB, "recording": False,
                      "clip_seconds": 0.0, "mar": None, "mouth": "unknown",
                      "trigger": trigger, "mouth_threshold": mouth_threshold,
                      "clips": 0}

    def update(self, **fields):
        with self.lock:
            self.state.update(fields)

    def get(self):
        with self.lock:
            return dict(self.state)


def annotate_preview(frame, landmarks, view):
    """Burn the live numbers onto the camera frame: sound, MAR, and REC right now.

    Drawn on the 640x480 frame before any zoom, so the text scales with the window.
    Every string is drawn twice - black then colour - to stay readable over a bright
    pillow as well as a dark room.
    """
    h, w = frame.shape[:2]
    if landmarks is not None:
        for idx, colour in ((UPPER_LIP, (0, 255, 0)), (LOWER_LIP, (0, 255, 0)),
                            (LEFT_CORNER, (255, 200, 0)),
                            (RIGHT_CORNER, (255, 200, 0))):
            lm = landmarks[idx]
            cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 3, colour, -1)
        for a, b, colour in ((UPPER_LIP, LOWER_LIP, (0, 255, 0)),
                             (LEFT_CORNER, RIGHT_CORNER, (255, 200, 0))):
            pa, pb = landmarks[a], landmarks[b]
            cv2.line(frame, (int(pa.x * w), int(pa.y * h)),
                     (int(pb.x * w), int(pb.y * h)), colour, 1)

    def put(text, y, colour):
        cv2.putText(frame, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    colour, 1, cv2.LINE_AA)

    recording = view["recording"]
    level_ok = view["level"] >= view["trigger"]
    mar_text = "--" if view["mar"] is None else f"{view['mar']:.2f}"
    put(f"sound {view['level']:6.1f} dBFS  (trigger {view['trigger']:.0f})", 26,
        (0, 255, 255) if level_ok else (235, 235, 235))
    put(f"REC {view['clip_seconds']:.1f} s" if recording else "idle", 52,
        (0, 0, 255) if recording else (0, 220, 0))
    put(f"MAR {mar_text:>5}  {mouth_label(view['mouth'])}", 78,
        {"open": (0, 0, 255), "closed": (0, 220, 0),
         "user_leave": (0, 200, 255)}.get(view["mouth"], (150, 150, 150)))
    put(f"mouth open above {view['mouth_threshold']:.2f}   clips {view['clips']}", 104,
        (200, 200, 200))
    put("q quits", h - 12, (200, 200, 200))
    if recording:
        cv2.circle(frame, (w - 28, 28), 11, (0, 0, 255), -1)
        cv2.circle(frame, (w - 28, 28), 11, (255, 255, 255), 1)
    return frame


class MouthSampler(threading.Thread):
    """Look at the pillow and keep the last mouth reading.

    A thread, because grabbing a frame and running Face Mesh (~12 ms) must not hold up
    the audio loop; it only ever writes a few numbers, which the main thread reads under
    a lock. Two rhythms: headless it takes one reading every `interval` seconds, while
    with the preview window open the camera is streamed and every shown frame is
    measured, so the numbers on the picture describe the picture.

    If the camera disappears it retries, and the rest of the program keeps working as
    an audio-only night.
    """

    def __init__(self, index, interval, smooth=3, shared=None, preview=False,
                 preview_fps=12.0, scale=1.5):
        super().__init__(daemon=True)
        self.index = index
        self.interval = max(0.2, interval)
        self.smooth = max(1, smooth)
        self.shared = shared
        self.preview = preview
        self.preview_fps = max(1.0, preview_fps)
        self.scale = scale
        self.preview_error = None
        self.window = "night watch - camera"
        self.stop_flag = threading.Event()
        self.wake = threading.Event()
        self.lock = threading.Lock()
        self.history = collections.deque(maxlen=self.smooth)
        self.mar = None
        self.face = False
        self.sampled_at = None
        self.error = None
        self.samples = 0
        self._landmarks = None
        self.frame = None

    def sample_now(self):
        self.wake.set()

    def snapshot(self):
        with self.lock:
            return self.mar, self.face, self.sampled_at, self.error, self.samples

    def _set(self, **fields):
        with self.lock:
            for key, value in fields.items():
                setattr(self, key, value)

    def run(self):
        try:
            while not self.stop_flag.is_set():
                cap = cv2.VideoCapture(self.index)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                if not cap.isOpened():
                    self._set(error=f"no camera at index {self.index}")
                    if self.stop_flag.wait(30):      # try again later, stay alive
                        return
                    continue
                self._set(error=None)
                try:
                    self._watch(cap)
                finally:
                    cap.release()
                if self.stop_flag.is_set():
                    return
                self._set(mar=None, face=False, error="lost the camera")
                if self.stop_flag.wait(5):
                    return
        except Exception as exc:            # never die quietly: the panel must say so
            with self.lock:
                self.error = f"camera thread stopped: {exc}"
                self.mar = None
                self.face = False
            self.preview_error = self.preview_error or str(exc)
        finally:
            pass

    @staticmethod
    def _mar_text(mar):
        return "--" if mar is None else f"{mar:.2f}"

    def latest_frame(self):
        """The newest frame and its landmarks, or (None, None). Copied under the lock.

        The window is drawn by the main thread: OpenCV's Qt backend silently fails to
        map a window created from a worker thread (the picture just never appears), so
        the camera thread only captures and this hands the frame over.
        """
        with self.lock:
            if self.frame is None:
                return None, None
            return self.frame.copy(), self._landmarks

    def _measure(self, frame, face_mesh):
        mar, self._landmarks = detect(frame, face_mesh)
        if mar is None:
            self.history.clear()
            self._set(mar=None, face=False, sampled_at=time.time())
        else:
            self.history.append(mar)
            self._set(mar=float(np.median(self.history)), face=True,
                      sampled_at=time.time())
        with self.lock:
            self.samples += 1

    def _watch(self, cap):
        with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True,
                                   min_detection_confidence=0.5,
                                   min_tracking_confidence=0.5,
                                   static_image_mode=False) as face_mesh:
            if self.preview:
                self._stream(cap, face_mesh)
            else:
                self._sample(cap, face_mesh)

    def _sample(self, cap, face_mesh):
        """Headless: one look every `interval` seconds - the cheap rhythm."""
        while not self.stop_flag.is_set():
            self.wake.wait(self.interval)
            self.wake.clear()
            if self.stop_flag.is_set():
                return
            for _ in range(2):        # the camera buffers a few stale frames
                cap.grab()
            ok, frame = cap.read()
            if not ok:
                return
            self._measure(frame, face_mesh)

    def _stream(self, cap, face_mesh):
        """Preview: keep grabbing frames; the main thread draws and measures them."""
        delay = 1.0 / self.preview_fps
        while not self.stop_flag.is_set():
            started = time.monotonic()
            ok, frame = cap.read()
            if not ok:
                return
            self._measure(frame, face_mesh)
            with self.lock:
                self.frame = frame
            spare = delay - (time.monotonic() - started)
            if spare > 0 and self.stop_flag.wait(spare):
                return


# ----------------------------------------------------------------------------- log

class NightLog:
    """One append-only JSONL for both sensors, in the shape morning.py reads.

    A state is written when it *ends*, because that is the only moment its duration
    is known - it is what turns a list of readings into a timeline. Audio clips are
    written when they close, carrying the last mouth reading, which is how the two
    sensors end up on the same line.
    """

    def __init__(self, path, mouth_threshold, min_hold=1.0, alive_every=600.0):
        self.fp = open(path, "a", buffering=1)      # line buffered: survives Ctrl-C
        self.mouth_threshold = mouth_threshold
        self.min_hold = min_hold
        self.alive_every = alive_every
        self.run = None                             # mouth state being measured
        self.run_start = 0.0
        self.run_mar = None
        self.mouth_states = 0
        self.last_alive = time.time()

    @staticmethod
    def _iso(t):
        return datetime.datetime.fromtimestamp(t).isoformat(timespec="seconds")

    def _write(self, entry):
        self.fp.write(json.dumps(entry) + "\n")
        return entry

    def mouth(self, state, mar, now):
        """Feed one camera reading. Returns the entry written when a state ends."""
        if self.run is None:
            self.run, self.run_start, self.run_mar = state, now, mar
            return None
        if state == self.run:
            if mar is not None and (self.run_mar is None or mar > self.run_mar):
                self.run_mar = mar
            return None

        entry = None
        held = now - self.run_start
        if held >= self.min_hold:                   # shorter = flicker, not an event
            entry = self._mouth_entry(self.run_start, self.run, self.run_mar, held)
            self._write(entry)
            self.mouth_states += 1
        self.run, self.run_start, self.run_mar = state, now, mar
        return entry

    def _mouth_entry(self, start, state, mar, held):
        # Three different absences: the user got up (user_leave), the camera cannot
        # tell us anything (unknown), and the camera was never turned on (off).
        # Saying "user_leave" for a dead camera would invent a story for the morning.
        if state == "user_leave":
            reading, mouth, snoring = f"user_leave for {human_span(held)}", "user_leave", False
        elif mar is None or state in ("unknown", "off"):
            reading = f"camera_{state} for {human_span(held)}"
            mouth, snoring = state, False
        else:
            mouth = state
            reading = f"mouth_{mouth} {mar:.2f} for {human_span(held)}"
            snoring = state == "open"
        return {
            "t": self._iso(start),
            "reading": reading,
            "mouth": mouth,
            "mar": None if mar is None else round(mar, 3),
            "snoring": snoring,
            "threshold": self.mouth_threshold,
            "held_s": round(held, 1),
        }

    def snore(self, clip, mouth_state, mar):
        """Write a finished snore clip, with whatever the camera last saw."""
        if mouth_state == "open" and mar is not None:
            tail = f", mouth_open {mar:.2f}"
        elif mouth_state == "closed" and mar is not None:
            tail = f", mouth_closed {mar:.2f}"
        elif mouth_state == "user_leave":
            tail = ", user_leave"
        elif mouth_state == "off":
            tail = ", camera off"
        else:
            tail = ", camera unknown"
        entry = {
            "t": self._iso(clip.started),
            "reading": f"snore_event {span_text(clip.seconds)}{tail}",
            "event": "snore",
            "dur": round(clip.seconds, 2),
            "peak_dbfs": round(clip.peak_db, 1),
            "mean_dbfs": round(clip.mean_db, 1),
            "mouth": mouth_state,
            "mar": None if mar is None else round(mar, 3),
            "file": str(clip.path),
            "written": self._iso(time.time()),
        }
        return self._write(entry)

    def alive(self, now, state=None):
        if not self.alive_every or now - self.last_alive < self.alive_every:
            return None
        self.last_alive = now
        return self._write({"t": self._iso(now), "alive": True, "mouth": state})

    def close(self, now):
        """Flush the mouth stretch in progress, so Ctrl-C still logs it."""
        if self.run is not None:
            held = now - self.run_start
            if held >= self.min_hold:
                self._write(self._mouth_entry(self.run_start, self.run, self.run_mar, held))
                self.mouth_states += 1
            self.run = None
        self.fp.close()


# --------------------------------------------------------------------------- panel

def span_text(seconds):
    """A duration the morning report can read out loud: 6.2s / 45m / 7h20m."""
    if seconds < 10:
        return f"{seconds:.1f}s"
    return human_span(seconds)


def mouth_label(mouth):
    """How a mouth state is drawn: user_leave reads better as USER LEAVE."""
    return mouth.replace("_", " ").upper()


def mar_bar(mar, threshold, width=24, high=0.8):
    """MAR on a fixed 0..0.8 scale, with a tick where 'open' starts."""
    frac = 0.0 if mar is None else min(1.0, max(0.0, mar / high))
    filled = int(round(frac * width))
    cells = ["#"] * filled + ["."] * (width - filled)
    pos = int(round(min(1.0, threshold / high) * (width - 1)))
    if 0 <= pos < width:
        cells[pos] = "|"
    return "[" + "".join(cells) + "]"


class Panel:
    """The full-screen panel: one block per sensor, then the night's totals."""

    is_tui = True
    KEYS = {ord("q"): "quit", ord("Q"): "quit", 3: "quit",
            ord("m"): "save", ord("M"): "save",
            ord("c"): "camera", ord("C"): "camera"}

    def __init__(self, threshold, spl_offset, mouth_threshold, mic, cam, log_path):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.colour = curses.has_colors()
        if self.colour:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_GREEN, -1)
            curses.init_pair(2, curses.COLOR_RED, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            curses.init_pair(4, curses.COLOR_CYAN, -1)
        self.low, self.high = meter_range(threshold)
        self.threshold = threshold
        self.spl_offset = spl_offset
        self.mouth_threshold = mouth_threshold
        self.mic, self.cam, self.log_path = mic, cam, log_path
        self.events = collections.deque(maxlen=10)
        self.last_draw = 0.0

    def _put(self, y, x, text, attr=0):
        """addstr that survives a small window and never leaves stale characters."""
        height, width = self.stdscr.getmaxyx()
        if y < 0 or y >= height or x < 0 or x >= width or not text:
            return
        room = max(0, width - x - 1)
        try:
            self.stdscr.addstr(y, x, text[:room].ljust(room), attr)
        except curses.error:
            pass

    def event(self, msg):
        self.events.appendleft(f"{datetime.datetime.now():%H:%M:%S} {msg}")

    def update(self, now, view):
        if now - self.last_draw < (0.1 if view["recording"] else 0.25):
            return
        self.last_draw = now
        height, width = self.stdscr.getmaxyx()
        bar_w = max(10, min(36, width - 46))
        green = curses.color_pair(1) if self.colour else 0
        red = curses.color_pair(2) if self.colour else 0
        yellow = curses.color_pair(3) if self.colour else 0
        cyan = curses.color_pair(4) if self.colour else 0

        self.stdscr.erase()
        self._put(0, 0, " night watch - snore + mouth ".ljust(width - 1), curses.A_REVERSE)
        self._put(1, 1, f"mic  {self.mic}")
        self._put(2, 1, f"cam  {view['cam_text']}")
        self._put(3, 1, "-" * (width - 2))

        self._put(4, 1, "sound")
        self._put(4, 7, db_bar(view["level"], width=bar_w, low=self.low, high=self.high,
                               marker=self.threshold), green if view["recording"] else 0)
        self._put(4, 9 + bar_w, shown_level(view["level"], self.spl_offset))
        self._put(5, 7, f"trigger {shown_level(self.threshold, self.spl_offset)}   "
                        f"peak {shown_level(view['peak'], self.spl_offset)}", yellow)

        mar_attr = red if view["mouth"] == "open" else 0
        self._put(6, 1, "mouth")
        self._put(6, 7, mar_bar(view["mar"], self.mouth_threshold, width=bar_w), mar_attr)
        self._put(6, 9 + bar_w, f" MAR {view['mar_text']:>4}  {mouth_label(view['mouth'])}")
        self._put(7, 7, f"threshold {self.mouth_threshold:.2f}   "
                        f"sampled {view['cam_age']}", cyan)

        self._put(8, 1, "-" * (width - 2))
        self._put(9, 1, "state")
        self._put(9, 7, view["state_text"], red if view["recording"] else 0)
        self._put(10, 1, "night")
        self._put(10, 7, f"{view['clips']} clip(s)  ·  {view['rec_min']:4.1f} min  ·  "
                         f"{view['mouth_states']} mouth state(s)  ·  "
                         f"{view['bytes_mb']:.1f} MB")

        self._put(11, 1, "-" * (width - 2))
        self._put(12, 1, "events (newest first)", curses.A_BOLD)
        for i, line in enumerate(list(self.events)[:max(0, height - 14)]):
            self._put(13 + i, 1, line)

        self._put(height - 1, 0, " q quit   m save clip   c look now ".ljust(width - 1),
                  curses.A_REVERSE)
        self.stdscr.refresh()

    def poll_keys(self):
        keys = []
        while True:
            try:
                ch = self.stdscr.getch()
            except curses.error:
                break
            if ch == -1:
                break
            if ch in self.KEYS:
                keys.append(self.KEYS[ch])
        return keys

    def close(self):
        try:
            self.stdscr.keypad(False)
            curses.nocbreak()
            curses.echo()
            curses.curs_set(1)
        except Exception:
            pass
        try:
            curses.endwin()
        except Exception:
            pass


class PlainPanel:
    """Line output for nohup, redirects, and -v: events as they happen, no escapes."""

    is_tui = False

    def __init__(self, threshold, spl_offset, mouth_threshold, mic, cam, log_path):
        self.spl_offset = spl_offset
        self.mouth_threshold = mouth_threshold
        self.last_status = 0.0
        self.tty = sys.stdout.isatty()

    def event(self, msg):
        print(msg, flush=True)

    def update(self, now, view):
        if not self.tty or now - self.last_status < 2.0:
            return
        self.last_status = now
        print(f"\r{datetime.datetime.now():%H:%M:%S} "
              f"sound {shown_level(view['level'], self.spl_offset)}  "
              f"mouth {view['mar_text']:>5} {view['mouth']}  {view['state_text']}   ",
              end="", flush=True)

    def poll_keys(self):
        return ()

    def close(self):
        if self.tty:
            print()


# ---------------------------------------------------------------------------- main

def main():
    global stop
    parser = argparse.ArgumentParser(
        description="Listen for snoring and watch the mouth, on one screen and one log.")
    # audio
    parser.add_argument("--device", help="input device index or name fragment")
    parser.add_argument("--source", help="Pulse capture source, i.e. which mic")
    parser.add_argument("--threshold", type=float, default=-32.0,
                        help="sound trigger level in dBFS (default -32)")
    parser.add_argument("--calibrate", type=float, metavar="SECONDS",
                        help="set the sound trigger from the room: floor + --margin")
    parser.add_argument("--margin", type=float, default=15.0,
                        help="dB above the room floor, for --calibrate (default 15)")
    parser.add_argument("--spl-offset", type=float,
                        help="dB SPL minus this mic's dBFS reading")
    parser.add_argument("--rate", type=int, help="sample rate (default: the mic's own)")
    parser.add_argument("--preroll", type=float, default=1.5,
                        help="seconds of audio kept before the trigger (default 1.5)")
    parser.add_argument("--min-trigger", type=float, default=0.3,
                        help="seconds above the threshold before recording (default 0.3)")
    parser.add_argument("--hold", type=float, default=3.0,
                        help="seconds of quiet that end a clip (default 3)")
    parser.add_argument("--max-len", type=float, default=300.0,
                        help="longest single clip in seconds (default 300)")
    parser.add_argument("--min-save", type=float, default=0.5,
                        help="drop clips shorter than this (default 0.5)")
    parser.add_argument("--low-band", type=float, metavar="RATIO",
                        help="only trigger if this share of energy is below 1 kHz")
    parser.add_argument("--stall-timeout", type=float, default=15.0,
                        help="reopen the mic stream after this long with no audio (default 15)")
    parser.add_argument("--min-free-mb", type=float, default=500.0,
                        help="pause recording below this much free disk (default 500 MB)")
    # camera
    parser.add_argument("--camera", type=int, default=0, help="webcam index (default 0)")
    parser.add_argument("--cam-interval", type=float, default=10.0,
                        help="seconds between camera samples (default 10)")
    parser.add_argument("--mouth-threshold", type=float, default=0.25,
                        help="MAR above this counts as an open mouth (default 0.25)")
    parser.add_argument("--smooth", type=int, default=3,
                        help="median over the last N camera samples (default 3)")
    parser.add_argument("--no-camera", action="store_true",
                        help="audio only: never open the camera")
    parser.add_argument("--preview", dest="preview", action="store_true", default=None,
                        help="show the camera in a window (default: when an X display exists)")
    parser.add_argument("--no-preview", dest="preview", action="store_false",
                        help="never open a window; also keeps the camera sampled, not streamed")
    parser.add_argument("--display", default=None, help="X display for the preview window")
    parser.add_argument("--preview-fps", type=float, default=12.0,
                        help="frames per second in the preview window (default 12)")
    parser.add_argument("--scale", type=float, default=1.5,
                        help="preview zoom, 1.0 = 640x480 (default 1.5)")
    # output
    parser.add_argument("--dir", default="snores", help="where WAV clips go (default snores/)")
    parser.add_argument("--log", default="night_log.jsonl",
                        help="JSONL log, same file morning.py reads (default night_log.jsonl)")
    parser.add_argument("--duration", type=float, help="stop after this many seconds")
    parser.add_argument("--no-tui", action="store_true", help="plain lines even in a terminal")
    parser.add_argument("-v", "--verbose", action="store_true", help="plain lines, every 2 s")
    args = parser.parse_args()

    # ---- audio device
    device = pick_device(args.device)
    info = sd.query_devices(device)
    rate = pick_rate(device, args.rate)
    block = max(1, int(round(rate * BLOCK_SECONDS)))
    print(f"mic  {device}: {info['name']}", flush=True)
    print(f"     mono int16 at {rate} Hz, {block / rate * 1000:.0f} ms blocks", flush=True)

    source = None
    if "pulse" in info["name"].lower() or info["name"].strip() == "default":
        source = choose_source(args.source)
        if source:
            os.environ["PULSE_SOURCE"] = source      # must precede the stream open
            print(f"     pulse source: {source}", flush=True)

    if args.calibrate:
        from snore_monitor import measure_floor
        print(f"     listening to the room for {args.calibrate:g} s...", flush=True)
        floor = measure_floor(device, rate, args.calibrate, block)
        threshold = min(-6.0, floor + args.margin)
        print(f"     room floor {floor:.1f} dBFS, trigger {threshold:.1f} dBFS", flush=True)
    else:
        threshold = args.threshold
        if args.spl_offset is not None:
            threshold -= args.spl_offset

    # ---- camera (a thread; the mic loop must never wait for a frame)
    preview = False
    if not args.no_camera and args.preview is not False:
        display = resolve_display(args.display, no_window=False)
        preview = display is not None
        if preview:
            print(f"     preview window on DISPLAY={display}, {args.preview_fps:g} fps,"
                  f" {args.scale:g}x -- use --no-preview for a real night run", flush=True)
        elif args.preview:
            print("     no X display found, so no preview window (see --display)", flush=True)
    cam_name = ("disabled (--no-camera)" if args.no_camera
                else f"camera {args.camera}" + (" + window" if preview else ""))
    shared = Shared(threshold, args.mouth_threshold)
    sampler = None
    if not args.no_camera:
        sampler = MouthSampler(args.camera, args.cam_interval, args.smooth,
                               shared=shared, preview=preview,
                               preview_fps=args.preview_fps, scale=args.scale)
        sampler.start()

    outdir = pathlib.Path(args.dir)
    outdir.mkdir(parents=True, exist_ok=True)
    log = NightLog(args.log, args.mouth_threshold, min_hold=1.0, alive_every=600.0)
    machine = SnoreMachine(rate, outdir, threshold, preroll=args.preroll,
                           min_trigger=args.min_trigger, hold=args.hold,
                           max_len=args.max_len, min_save=args.min_save,
                           low_band=args.low_band, min_free_mb=args.min_free_mb)

    panel = None
    if sys.stdout.isatty() and not (args.no_tui or args.verbose):
        try:
            panel = Panel(threshold, args.spl_offset, args.mouth_threshold,
                          f"{info['name']}", cam_name, args.log)
        except Exception as e:
            try:
                curses.endwin()
            except Exception:
                pass
            print(f"could not start the panel ({e}); using plain output", flush=True)
    if panel is None:
        panel = PlainPanel(threshold, args.spl_offset, args.mouth_threshold,
                           info["name"], cam_name, args.log)

    clips = restarts = skipped_disk = 0
    rec_done = 0.0
    bytes_written = 0
    peak = SILENCE_DB
    last_cam_sample = 0.0
    cam_error_noted = False
    deadline = time.monotonic() + args.duration if args.duration else None
    panel.event(f"listening to {info['name']}; clips -> {outdir}/")
    panel.event(f"log -> {args.log}; mouth open above MAR {args.mouth_threshold:.2f}")

    def finish_clip(clip, manual=False):
        """Log and account for a clip that just closed."""
        nonlocal clips, rec_done, bytes_written
        rec_done += clip.seconds
        clips += 1
        try:
            bytes_written += clip.path.stat().st_size
        except OSError:
            pass
        mouth, mar = mouth_now(sampler, args.mouth_threshold)
        entry = log.snore(clip, mouth, mar)
        panel.event(f"saved{' (manual)' if manual else ''} {clip.path.name}  "
                    f"{clip.seconds:5.1f} s  {entry['reading']}")
        return entry

    def on_signal(signum, frame):
        global stop
        stop = True

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    audio_q = queue.Queue(maxsize=int(rate / block * 30))
    dropped = 0

    def callback(indata, frames, time_info, status):
        nonlocal dropped
        if status:
            dropped += 1
        try:
            audio_q.put_nowait(indata[:, 0].copy())
        except queue.Full:
            dropped += 1

    def open_stream():
        return sd.InputStream(device=device, channels=1, samplerate=rate, dtype="int16",
                              blocksize=block, latency="high", callback=callback)

    stream = None
    try:
        try:
            stream = open_stream()
            stream.start()
        except sd.PortAudioError as e:
            raise SystemExit(f"could not open the mic ({info['name']}): {e}\n"
                             "another program may be holding it; try --device pulse")

        last_audio = time.monotonic()
        while not stop:
            if deadline and time.monotonic() >= deadline:
                break

            # ---- audio: the fast loop
            try:
                chunk = audio_q.get(timeout=0.2)
                last_audio = time.monotonic()
            except queue.Empty:
                chunk = None
                # A silent room still sends blocks; no audio at all means the stream
                # died, so reopen it rather than record nothing all night.
                if time.monotonic() - last_audio >= args.stall_timeout:
                    panel.event(f"no audio for {args.stall_timeout:g} s, reopening")
                    partial = machine.save_now()
                    if partial is not None:
                        if partial.seconds >= args.min_save:
                            finish_clip(partial)
                        else:
                            partial.path.unlink(missing_ok=True)
                    try:
                        stream.stop()
                        stream.close()
                    except Exception:
                        pass
                    while not audio_q.empty():
                        try:
                            audio_q.get_nowait()
                        except queue.Empty:
                            break
                    while not stop:
                        try:
                            stream = open_stream()
                            stream.start()
                            break
                        except Exception as e:
                            panel.event(f"reopen failed ({e}), retrying in 5 s")
                            time.sleep(5)
                    restarts += 1
                    log.fp.write(json.dumps({"event": "restart",
                                             "t": NightLog._iso(time.time()),
                                             "n": restarts}) + "\n")
                    last_audio = time.monotonic()

            if chunk is not None:
                level, outcomes = machine.feed(chunk)
                peak = max(peak, level)
                for kind, payload in outcomes:
                    if kind == "start":
                        panel.event(f"loud {shown_level(level, args.spl_offset)} -> recording")
                    elif kind == "close":
                        finish_clip(payload)
                    elif kind == "short":
                        rec_done += payload.seconds
                    elif kind == "disk":
                        skipped_disk += 1
                        if skipped_disk == 1 or skipped_disk % 300 == 0:
                            panel.event(f"only {payload:.0f} MB free, not recording")

            # ---- camera: only when a new sample has landed
            mouth, mar = ("off", None) if sampler is None else ("unknown", None)
            cam_age, cam_text = "never", cam_name
            if sampler is not None:
                mar, face, sampled_at, error, samples = sampler.snapshot()
                if mar is None:
                    # No face means the user got up; an error means the camera is the
                    # thing that left. Keeping those apart stops the log inventing a
                    # story about the user out of a broken camera.
                    mouth = "unknown" if error else "user_leave"
                else:
                    mouth = "open" if mar > args.mouth_threshold else "closed"
                if error:
                    cam_text = f"{cam_name} - {error}"
                    if not cam_error_noted:      # close the last state, log the fault
                        cam_error_noted = True
                        log.mouth("unknown", None, time.time())
                        panel.event(f"camera problem: {error}")
                else:
                    cam_error_noted = False
                if sampled_at and sampled_at != last_cam_sample:
                    last_cam_sample = sampled_at
                    entry = log.mouth(mouth, mar, sampled_at)
                    if entry is not None:
                        panel.event(f"mouth {entry['reading']}")
                if sampled_at:
                    cam_age = f"{time.time() - sampled_at:.0f} s ago"
                    cam_text = f"{cam_name} ok - last look {cam_age}"
                if sampler.preview_error:
                    cam_text = f"{cam_name} - window failed: {sampler.preview_error[:28]}"

            # ---- keys and the panel
            now = time.monotonic()
            rec = machine.clip
            view = {
                "level": machine.level,
                "recording": rec is not None,
                "peak": peak,
                "mar": mar,
                "mar_text": "--" if mar is None else f"{mar:.2f}",
                "mouth": mouth,
                "cam_text": cam_text,
                "cam_age": cam_age,
                "state_text": (f"REC {rec.seconds:6.1f} s" if rec else "idle, listening"),
                "clips": clips,
                "rec_min": (rec_done + (rec.seconds if rec else 0.0)) / 60,
                "mouth_states": log.mouth_states,
                "bytes_mb": bytes_written / 1e6,
            }
            panel.update(now, view)
            if sampler is not None:            # the preview window's overlay reads this
                shared.update(level=view["level"], peak=view["peak"],
                              recording=view["recording"],
                              clip_seconds=rec.seconds if rec else 0.0,
                              mar=mar, mouth=view["mouth"], clips=clips)

            # ---- preview window: drawn here, in the main thread, on purpose
            if preview and sampler is not None:
                frame, landmarks = sampler.latest_frame()
                if frame is not None:
                    try:
                        shown = annotate_preview(frame, landmarks, shared.get())
                        if args.scale != 1.0:
                            shown = cv2.resize(shown, None, fx=args.scale, fy=args.scale,
                                               interpolation=cv2.INTER_LINEAR)
                        cv2.imshow(PREVIEW_WINDOW, shown)
                        cv2.setWindowTitle(
                            PREVIEW_WINDOW,
                            f"night watch | {view['level']:6.1f} dBFS | "
                            f"MAR {view['mar_text']} {view['mouth']} | "
                            f"{'REC' if view['recording'] else 'idle'}")
                        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                            stop = True
                    except cv2.error as exc:
                        preview = False
                        panel.event(f"preview window failed ({exc}); camera keeps sampling")

            for action in panel.poll_keys():
                if action == "quit":
                    stop = True
                elif action == "save":
                    clip = machine.save_now()
                    if clip is not None:
                        finish_clip(clip, manual=True)
                elif action == "camera" and sampler is not None:
                    sampler.sample_now()
                    panel.event("looking now")

            beat = log.alive(time.time(), mouth)
            if beat is not None and not panel.is_tui:
                panel.event(f"alive, {clips} clip(s) so far")
    finally:
        clip = machine.save_now()                       # keep a clip cut short by Ctrl-C
        if clip is not None:
            if clip.seconds >= args.min_save:
                finish_clip(clip)
            else:
                clip.path.unlink(missing_ok=True)
        if sampler is not None:
            sampler.stop_flag.set()
            sampler.wake.set()
            sampler.join(timeout=3)
        if preview:
            try:
                cv2.destroyAllWindows()     # main thread owns the window
            except Exception:
                pass
        log.close(time.time())
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        panel.close()

    print(f"stopped: {clips} clip(s), {log.mouth_states} mouth state(s), "
          f"{restarts} restart(s)", flush=True)
    if dropped:
        print(f"warning: {dropped} dropped audio block(s)", flush=True)
    print(f"log: {args.log}  (morning.py reads this file)", flush=True)
    return 0


def mouth_now(sampler, threshold):
    """The camera's latest verdict, as (state, mar), for tagging an audio clip."""
    if sampler is None:
        return "off", None
    mar, _face, _at, error, _n = sampler.snapshot()
    if error:
        return "unknown", None
    if mar is None:
        return "user_leave", None
    return ("open" if mar > threshold else "closed"), mar


if __name__ == "__main__":
    sys.exit(main())
