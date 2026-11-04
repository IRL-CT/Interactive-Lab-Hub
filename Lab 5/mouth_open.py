"""
Mouth-aspect-ratio (MAR) detector with MediaPipe Face Mesh.

MAR is the inner-lip gap divided by the mouth-corner width:

        13 (upper inner lip)
         |
   61 ---+--- 291        MAR = |13 - 14| / |61 - 291|
         |
        14 (lower inner lip)

It reads ~0.0 with the mouth closed and ~0.3-0.6 wide open. Every frame is
compared to a threshold; above it the script reports "snoring_detected",
otherwise "snoring_not_detected".

    python mouth_open.py                     # run until Ctrl-C / q
    python mouth_open.py --threshold 0.25    # tune the cut-off
    python mouth_open.py --save-dir frames   # also save annotated frames
    python mouth_open.py --seconds 20        # timed run

The camera stream is shown in a window. Over ssh DISPLAY is usually empty,
so the script falls back to the local screen (:0, the Xwayland server behind
wayvnc / rpi-connect) and the window shows up on the Pi's desktop. Use
--no-window for a pure console run, or ssh -X and --display $DISPLAY.

Logging (Part H). Every finished mouth state is appended to night_log.jsonl,
the same file and the same shape overnight.py writes, so the morning report
reads one night instead of two.

    {"t": "2025-10-29T03:12:20", "reading": "mouth_open 0.41 for 6s",
     "mouth": "open", "mar": 0.41, "snoring": true, "threshold": 0.25,
     "held_s": 6.2}

That line is the README's `03:12:20 snore_event 6s, mouth_open 0.41`. Three
rules come from how morning.py reads the file:

  * `t` is local ISO time; the report slices `t[11:19]` and `t[11:13]` out of it.
  * `reading` is the only thing the language model ever sees, so it is a
    sentence: which mouth state, the MAR, and how long it held.
  * a state is written once it *ends*, so every line knows its own duration --
    a reading that held 8 s and one that held 8 h look different.

An `alive` line with no `reading` key goes in every ten minutes (the same
trick as overnight.py) so a quiet night is distinguishable from a crash, and
it is not counted as a change. States shorter than --min-hold are dropped, so
flicker never becomes a log entry. Nothing is sampled besides the number:
no frames are written unless you ask for --save-dir.
"""
import argparse
import datetime
import json
import os
import time

# MediaPipe's data files are looked up from the package; nothing to set here.
# Note: the first few seconds of every run print two or three harmless MediaPipe
# warnings on stderr (a NORM_RECT hint and a TFLite feedback-manager note). They
# come from inside the bundled glog and cannot be turned off with GLOG_minloglevel.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import cv2
import mediapipe as mp
import numpy as np

# Face Mesh indices (see https://github.com/google/mediapipe/wiki/FaceMesh)
UPPER_LIP = 13
LOWER_LIP = 14
LEFT_CORNER = 61
RIGHT_CORNER = 291

mp_face_mesh = mp.solutions.face_mesh
mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


def mouth_aspect_ratio(landmarks, w, h):
    """MAR for one face, in pixels so the 640x480 aspect ratio cannot skew it."""
    def pt(i):
        lm = landmarks[i]
        return np.array([lm.x * w, lm.y * h], dtype=np.float32)

    gap = np.linalg.norm(pt(UPPER_LIP) - pt(LOWER_LIP))
    width = np.linalg.norm(pt(LEFT_CORNER) - pt(RIGHT_CORNER))
    if width < 1e-6:
        return 0.0
    return float(gap / width)


def detect(frame, face_mesh):
    """Run Face Mesh on a BGR frame. Returns (mar or None, landmarks or None)."""
    h, w = frame.shape[:2]
    result = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if not result.multi_face_landmarks:
        return None, None
    landmarks = result.multi_face_landmarks[0].landmark
    return mouth_aspect_ratio(landmarks, w, h), landmarks


def resolve_display(requested, no_window):
    """Pick an X display for the preview window, or None to stay headless.

    Over ssh DISPLAY is empty, but the Pi still has a local X server (:0, the
    Xwayland behind wayvnc / rpi-connect) whose socket we can check for.
    """
    if no_window:
        return None
    for candidate in (requested, os.environ.get("DISPLAY"), ":0"):
        if not candidate:
            continue
        try:
            number = candidate.split(":", 1)[1].split(".", 1)[0]
        except IndexError:
            continue
        if os.path.exists(f"/tmp/.X11-unix/X{number}"):
            os.environ["DISPLAY"] = candidate
            return candidate
    return None


def annotate(frame, mar, landmarks, threshold, status):
    """Draw the lips, the measurement and the verdict onto the frame."""
    h, w = frame.shape[:2]
    if landmarks is not None:
        for idx, colour in (
            (UPPER_LIP, (0, 255, 0)),
            (LOWER_LIP, (0, 255, 0)),
            (LEFT_CORNER, (255, 200, 0)),
            (RIGHT_CORNER, (255, 200, 0)),
        ):
            lm = landmarks[idx]
            cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 3, colour, -1)

        up = landmarks[UPPER_LIP]
        low = landmarks[LOWER_LIP]
        left = landmarks[LEFT_CORNER]
        right = landmarks[RIGHT_CORNER]
        cv2.line(frame, (int(up.x * w), int(up.y * h)), (int(low.x * w), int(low.y * h)),
                 (0, 255, 0), 1)
        cv2.line(frame, (int(left.x * w), int(left.y * h)), (int(right.x * w), int(right.y * h)),
                 (255, 200, 0), 1)

    colour = (0, 0, 255) if status == "snoring_detected" else (0, 255, 0)
    mar_text = "MAR: --" if mar is None else f"MAR: {mar:.3f}"
    cv2.putText(frame, mar_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(frame, f"threshold: {threshold:.2f}", (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.putText(frame, status, (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, colour, 2)
    if mar is None:
        cv2.putText(frame, "no face", (20, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 1)
    return frame


def human_span(seconds):
    """6s / 45m / 7h20m -- a duration the morning report can read out loud."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds:.0f}m"
    return f"{int(seconds // 3600)}h{int(seconds % 3600 // 60):02d}m"


class NightLog:
    """Append-only JSONL of finished mouth states, shared with overnight.py.

    A state is written when it ends, which is the only moment its duration is
    known: that is what turns a list of readings into a timeline. The MAR kept
    for the state is its peak, i.e. the widest the mouth got in that stretch.
    """

    def __init__(self, path, threshold, min_hold=1.0, alive_every=600.0):
        self.fp = open(path, "a", buffering=1)      # line buffered: survives Ctrl-C
        self.threshold = threshold
        self.min_hold = min_hold
        self.alive_every = alive_every
        self.run = None                             # state being measured right now
        self.run_start = 0.0
        self.run_mar = None                         # peak MAR inside this state
        self.last_mar = None
        self.last_alive = time.time()

    @staticmethod
    def _iso(t):
        return datetime.datetime.fromtimestamp(t).isoformat(timespec="seconds")

    def _entry(self, start, status, mar, held, now=None):
        if status == "nobody" or mar is None:
            reading, mouth, snoring = "nobody", "nobody", False
        else:
            open_ = status == "snoring_detected"
            mouth = "open" if open_ else "closed"
            reading = f"mouth_{mouth} {mar:.2f} for {human_span(held)}"
            snoring = open_
        entry = {
            "t": self._iso(start),          # when the state began, as in the README line
            "reading": reading,
            "mouth": mouth,
            "mar": None if mar is None else round(mar, 3),
            "snoring": snoring,
            "threshold": self.threshold,
            "held_s": round(held, 1),
        }
        if now is not None:
            # Lines are written when a state ends, so t and file order can disagree;
            # this is the moment the line was written, for sorting the file back out.
            entry["written"] = self._iso(now)
        return entry

    def _write(self, entry):
        self.fp.write(json.dumps(entry) + "\n")

    def update(self, status, mar, now):
        """Feed one frame's verdict. Returns the entry written, or None."""
        # An empty frame and a closed mouth both read "not snoring", but they are
        # different events: one is a person leaving, the other a person asleep.
        state = "nobody" if mar is None else status
        self.last_mar = mar
        if self.run is None:
            self.run, self.run_start, self.run_mar = state, now, mar
            return None
        if state == self.run:
            if mar is not None and (self.run_mar is None or mar > self.run_mar):
                self.run_mar = mar
            return None

        # The state just changed, so the old one is complete and can be timed.
        entry = None
        held = now - self.run_start
        if held >= self.min_hold:                   # shorter = flicker, not an event
            entry = self._entry(self.run_start, self.run, self.run_mar, held, now)
            self._write(entry)
        self.run, self.run_start, self.run_mar = state, now, mar
        return entry

    def alive(self, now):
        if not self.alive_every or now - self.last_alive < self.alive_every:
            return None
        self.last_alive = now
        entry = {"t": self._iso(now), "alive": True, "state": self.run,
                 "mar": None if self.last_mar is None else round(self.last_mar, 3)}
        self._write(entry)
        return entry

    def close(self, now):
        """Flush the state in progress, so Ctrl-C mid-stretch still logs it."""
        if self.run is not None:
            held = now - self.run_start
            if held >= self.min_hold:
                self._write(self._entry(self.run_start, self.run, self.run_mar, held, now))
            self.run = None
        self.fp.close()


def main():
    parser = argparse.ArgumentParser(
        description="Mouth aspect ratio (MAR) -> snoring_detected / snoring_not_detected",
        epilog="examples:\n"
               "  python mouth_open.py            # default threshold 0.25\n"
               "  python mouth_open.py 0.32       # positional threshold\n"
               "  python mouth_open.py --threshold 0.32",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("threshold_pos", nargs="?", type=float, default=None, metavar="THRESHOLD",
                        help="MAR above this counts as an open mouth (same as --threshold)")
    parser.add_argument("--threshold", type=float, default=None,
                        help="MAR above this counts as an open mouth (default 0.25)")
    parser.add_argument("--camera", type=int, default=0, help="webcam index (default 0)")
    parser.add_argument("--seconds", type=float, default=None, help="stop after N seconds")
    parser.add_argument("--save-dir", default=None,
                        help="save an annotated jpg here whenever the status changes")
    parser.add_argument("--smooth", type=int, default=3,
                        help="median over the last N frames, 1 = raw (default 3)")
    parser.add_argument("--heartbeat", type=float, default=1.0,
                        help="seconds between MAR printouts in headless mode (0 = off)")
    parser.add_argument("--no-window", action="store_true",
                        help="never open a window, even if DISPLAY is set")
    parser.add_argument("--display", default=None,
                        help="X display for the window (default: $DISPLAY, then :0)")
    parser.add_argument("--scale", type=float, default=1.5,
                        help="window zoom factor, 1.0 = 640x480 (default 1.5)")
    parser.add_argument("--log", default="night_log.jsonl",
                        help="JSONL file to append each finished state to "
                             "(default night_log.jsonl, same file as overnight.py)")
    parser.add_argument("--no-log", action="store_true", help="do not write a log file")
    parser.add_argument("--min-hold", type=float, default=1.0,
                        help="seconds a state must last before it is logged (default 1.0)")
    parser.add_argument("--alive-every", type=float, default=600.0,
                        help="seconds between 'alive' lines in the log, 0 = off (default 600)")
    args = parser.parse_args()

    # `python mouth_open.py 0.3` and `--threshold 0.3` both work; giving both
    # different values is a mistake worth stopping for.
    if args.threshold_pos is not None and args.threshold is not None \
            and args.threshold_pos != args.threshold:
        parser.error(f"threshold given twice: positional {args.threshold_pos:g} "
                     f"vs --threshold {args.threshold:g}")
    threshold = args.threshold_pos if args.threshold_pos is not None else args.threshold
    if threshold is None:
        threshold = 0.25
    if not 0.0 < threshold < 2.0:
        parser.error(f"threshold {threshold:g} is outside the sensible MAR range 0-2")
    args.threshold = threshold

    if args.display:
        os.environ["DISPLAY"] = args.display
    display = resolve_display(args.display, args.no_window)
    show = display is not None
    if show:
        print(f"preview window on DISPLAY={display}", flush=True)
    else:
        print("no X display found: console only (use --display, or ssh -X)", flush=True)
    if args.save_dir:
        os.makedirs(args.save_dir, exist_ok=True)

    logger = None
    if not args.no_log:
        try:
            logger = NightLog(args.log, args.threshold, args.min_hold, args.alive_every)
            print(f"logging mouth states to {args.log}"
                  f" (a line is written when a state ends, min {args.min_hold:g}s)", flush=True)
        except OSError as exc:
            print(f"cannot write {args.log} ({exc}): running without a log", flush=True)

    cap = cv2.VideoCapture(args.camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        raise SystemExit(f"no webcam at index {args.camera}: is it plugged in?")

    history = []
    status = "snoring_not_detected"
    last_status = None
    saved_status = None
    saved = 0
    last_print = 0.0
    start = time.time()
    fps_t, frames = time.time(), 0

    print(f"threshold MAR > {args.threshold:.2f} -> snoring_detected", flush=True)
    if not show:
        print("printing status to the console (Ctrl-C to stop)", flush=True)
    elif args.scale != 1.0:
        print(f"window zoom {args.scale:g}x, press q or Esc to quit", flush=True)

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        static_image_mode=False,
    ) as face_mesh:
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("lost the camera", flush=True)
                    break

                mar, landmarks = detect(frame, face_mesh)

                if mar is not None:
                    history.append(mar)
                    del history[:-max(args.smooth, 1)]
                    smoothed = float(np.median(history))
                    status = ("snoring_detected" if smoothed > args.threshold
                              else "snoring_not_detected")
                else:
                    history.clear()
                    status = "snoring_not_detected"
                    smoothed = None

                # Report on every change, so the log is a list of events, not a stream.
                if status != last_status:
                    if smoothed is None:
                        print(f"{status}  (no face in view)", flush=True)
                    else:
                        print(f"{status}  MAR={smoothed:.3f}", flush=True)
                    last_status = status

                now = time.time()
                if not show and args.heartbeat and now - last_print >= args.heartbeat:
                    last_print = now
                    if smoothed is None:
                        print("MAR=--", flush=True)
                    else:
                        print(f"MAR={smoothed:.3f}  {status}", flush=True)

                annotate(frame, smoothed, landmarks, args.threshold, status)

                if logger is not None:
                    entry = logger.update(status, smoothed, now)
                    if entry is not None:
                        print(f"logged {entry['t'][11:19]} {entry['reading']}", flush=True)
                    beat = logger.alive(now)
                    if beat is not None:
                        print(f"logged {beat['t'][11:19]} alive", flush=True)

                if args.save_dir and status != saved_status:
                    saved_status = status
                    path = os.path.join(args.save_dir, f"{saved:03d}_{status}.jpg")
                    cv2.imwrite(path, frame)
                    saved += 1
                    print(f"saved {path}", flush=True)

                if show:
                    try:
                        shown = frame
                        if args.scale != 1.0:
                            shown = cv2.resize(
                                frame, None, fx=args.scale, fy=args.scale,
                                interpolation=cv2.INTER_LINEAR)
                        cv2.imshow("mouth_open", shown)
                        cv2.setWindowTitle("mouth_open",
                                           f"MAR {'--' if smoothed is None else f'{smoothed:.3f}'} | {status}")
                        key = cv2.waitKey(1) & 0xFF
                        if key in (ord("q"), 27):
                            break
                    except cv2.error as exc:
                        print(f"cannot open a window ({exc}): falling back to console",
                              flush=True)
                        show = False

                frames += 1
                if frames >= 30:
                    if not show:
                        print(f"~{frames / (time.time() - fps_t):.1f} fps", flush=True)
                    frames, fps_t = 0, time.time()

                if args.seconds and time.time() - start >= args.seconds:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            cap.release()
            cv2.destroyAllWindows()
            if logger is not None:
                logger.close(time.time())

    print(f"stopped after {time.time() - start:.1f} s, last status {status}", flush=True)


if __name__ == "__main__":
    main()
