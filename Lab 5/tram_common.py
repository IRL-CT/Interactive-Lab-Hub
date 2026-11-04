"""
tram_common.py: shared pieces for the Roosevelt Island tram watcher.

Camera access, the config file (tram_config.json), change detection versus an empty
background (for direction and for finding tram images to label), and the operating hours. The other tram_*.py scripts import this file.
"""
import datetime
import json
import pathlib
from pathlib import Path

import cv2
import numpy as np

CONFIG = pathlib.Path("tram_config.json")
DATA = pathlib.Path("tram_data")            # cropped frames: tram_data/YYYYMMDD/HHMMSS.jpg
LABELS = pathlib.Path("tram_labels.csv")    # filename,label   (1 = tram in view, 0 = no tram)
MODEL = pathlib.Path("tram_model.pt")          # the trained classifier (copied here by tram_train.py)
EVENTS = pathlib.Path("tram_events.jsonl")  # one line per pass: start, end, duration, direction
STATE = pathlib.Path("tram_state.json")     # live state, rewritten every second (display + API read it)

ROTATIONS = {"cw": cv2.ROTATE_90_CLOCKWISE, "ccw": cv2.ROTATE_90_COUNTERCLOCKWISE,
             "180": cv2.ROTATE_180}
CROP_WIDTH = 320                            # crops are shrunk to at most this width (tram_config.json "crop_width" overrides)


# ---------- config ----------

def load_config(required=True):
    if CONFIG.exists():
        with open(CONFIG) as f:
            return json.load(f)
    if required:
        raise SystemExit("no tram_config.json yet: run `python tram_collect.py --setup` first")
    return {}


def save_config(cfg):
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)


# ---------- camera ----------

def v4l2_set(cfg):
    """Apply camera controls with v4l2-ctl (Linux). Default: 60 Hz mains, to avoid flicker
    bands from indoor lights in the US. Add more in tram_config.json under "v4l2"."""
    import subprocess
    controls = {"power_line_frequency": 2, **cfg.get("v4l2", {})}
    args = ["v4l2-ctl", "-d", f"/dev/video{cfg.get('camera', 0)}"]
    for k, v in controls.items():
        args += ["-c", f"{k}={v}"]
    try:
        subprocess.run(args, capture_output=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        pass                                   # v4l2-ctl missing: not essential


def open_cam(cfg):
    cap = cv2.VideoCapture(cfg.get("camera", 0))
    if cfg.get("fourcc"):                        # e.g. "MJPG" for 1080p; off unless set in the config
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*cfg["fourcc"]))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.get("width", 1280))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.get("height", 720))
    if not cap.isOpened():
        raise SystemExit("no webcam found: is it plugged in?")
    v4l2_set(cfg)
    return cap


def grab(cap, cfg):
    """One fresh full frame, rotated as configured. Raises RuntimeError if the camera fails."""
    for _ in range(4):                       # the webcam buffers frames; skip the stale ones
        cap.grab()
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError("no frame from the webcam")
    if cfg.get("mirror"):
        frame = cv2.flip(frame, 1)          # undo a webcam that mirrors left/right
    code = ROTATIONS.get(cfg.get("rotate"))
    return frame if code is None else cv2.rotate(frame, code)


class Exposure:
    """Our own auto-exposure, metered on the tram's box only.

    The webcam's built-in auto-exposure looks at the whole picture, so at night a few bright
    windows and bridge lamps make it keep the exposure short and the sky goes black. This
    switches the webcam to manual and nudges exposure (then gain) until the box's median
    brightness sits near `target`. Exposure is in 0.1 ms steps (5000 = half a second);
    see the camera's ranges with: v4l2-ctl --list-ctrls
    """

    def __init__(self, cap, cfg):
        e = cfg.get("exposure", {})
        self.cap, self.target = cap, e.get("target", 100)
        self.lo, self.hi = e.get("min", 3), e.get("max", 5000)          # exposure range (0.1 ms)
        self.gain_lo, self.gain_hi = e.get("min_gain", 0), e.get("max_gain", 63)
        self.enabled = e.get("enabled", True)
        self.value = e.get("start", 150)
        self.gain = e.get("start_gain", 32)                               # the camera's default
        self.frames = 0
        self.device = f"/dev/video{cfg.get('camera', 0)}"
        if self.enabled and not self._apply():
            print("note: could not set exposure (is v4l2-ctl installed? sudo apt install "
                  "v4l-utils); using the camera's own auto-exposure", flush=True)
            self.enabled = False

    def _apply(self):
        """Set manual exposure and gain with v4l2-ctl (OpenCV's exposure setting is ignored by
        many webcams, including ours). Returns False if it could not."""
        import subprocess
        try:
            r = subprocess.run(["v4l2-ctl", "-d", self.device, "-c", "auto_exposure=1",
                                "-c", f"exposure_time_absolute={int(self.value)}",
                                "-c", f"gain={int(self.gain)}"], capture_output=True, timeout=5)
            return r.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def update(self, roi_img):
        """Call once per frame with the crop. Adjusts every 3rd frame so the camera can settle."""
        self.frames += 1
        if not self.enabled or self.frames % 3:
            return
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        inside = gray[roi_img.max(axis=2) > 0]           # skip the blacked-out area outside the outline
        level = float(np.median(inside if inside.size else gray))
        if level < self.target * 0.75:                  # too dark: longer exposure, then gain
            if self.value < self.hi:
                self.value = min(self.hi, max(self.value + 1, int(self.value * 1.4)))
            elif self.gain < self.gain_hi:
                self.gain = min(self.gain_hi, self.gain + 8)
            else:
                return
        elif level > self.target * 1.3:                 # too bright: less gain, then shorter
            if self.gain > self.gain_lo:
                self.gain = max(self.gain_lo, self.gain - 8)
            elif self.value > self.lo:
                self.value = max(self.lo, int(self.value / 1.4))
            else:
                return
        else:
            return
        self._apply()

    def status(self):
        return f"exposure {self.value}, gain {self.gain}" if self.enabled else "camera auto-exposure"


def crop(frame, cfg):
    """Cut out only the tram's part of the sky and shrink it. Everything else in the view
    (street, cars, windows) is thrown away before anything is saved or analyzed."""
    x, y, w, h = cfg["roi"]
    roi = frame[y:y + h, x:x + w].copy()
    if cfg.get("polygon"):                        # black out everything outside the tram's path
        mask = np.zeros(roi.shape[:2], np.uint8)
        pts = np.array([[px - x, py - y] for px, py in cfg["polygon"]], np.int32)
        cv2.fillPoly(mask, [pts], 255)
        roi[mask == 0] = 0
    width = cfg.get("crop_width", CROP_WIDTH)
    if roi.shape[1] <= width:                    # never blow up a small crop; keep every pixel
        return roi
    scale = width / roi.shape[1]
    return cv2.resize(roi, (width, max(8, int(roi.shape[0] * scale))), interpolation=cv2.INTER_AREA)


# ---------- change-based helpers (no color rules) ----------

def gray_small(img):
    """A small, slightly blurred grayscale copy: cheap to compare, ignores sensor noise."""
    g = cv2.cvtColor(cv2.resize(img, (160, max(8, img.shape[0] * 160 // img.shape[1]))),
                     cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(g, (5, 5), 0).astype(np.float32)


def change_mask(img, background, thresh=25):
    """Pixels that differ clearly from the background (the same view with no tram).
    Brightness is matched first, so a cloud or dusk darkening the whole view does not count."""
    g, b = gray_small(img), gray_small(background.astype(np.uint8))
    g = g * (b.mean() + 1e-6) / (g.mean() + 1e-6)
    return np.abs(g - b) > thresh


def change_score(img, background):
    """Fraction of the crop that changed versus the background."""
    return float(change_mask(img, background).mean())


def motion_x(img, background):
    """Horizontal position (0 = left, 1 = right) of whatever changed, or None.
    Used only to tell which way a cabin is moving."""
    m = change_mask(img, background)
    xs = np.nonzero(m)[1]
    if len(xs) < 6:
        return None
    return float(np.median(xs) / m.shape[1])


# ---------- the trained classifier ----------

def load_classifier():
    """Returns p_tram(img) -> probability (0..1) that a tram is in the crop."""
    if not MODEL.exists():
        raise SystemExit("no tram_model.pt yet: label some images and run tram_train.py first")
    from ultralytics import YOLO
    model = YOLO(str(MODEL), task="classify")
    meta = MODEL.with_suffix(".json")
    imgsz = json.load(open(meta)).get("imgsz", 160) if meta.exists() else 160
    idx = [k for k, v in model.names.items() if v == "tram"][0]

    def p_tram(img):
        r = model.predict(img, imgsz=imgsz, verbose=False)[0]
        return float(r.probs.data[idx])
    return p_tram


def load_detector():
    """Returns find(img) -> [(confidence, (x1, y1, x2, y2) as 0..1 of the crop), ...], most
    confident first: EVERY tram it sees, so both cabins can be tracked when both are in view.
    None if no detector has been trained yet (tram_train_det.py)."""
    det = Path("tram_det.pt")
    if not det.exists():
        return None
    from ultralytics import YOLO
    model = YOLO(str(det), task="detect")
    meta = det.with_suffix(".json")
    imgsz = json.load(open(meta)).get("imgsz", 320) if meta.exists() else 320

    def find(img):
        r = model.predict(img, imgsz=imgsz, conf=0.05, verbose=False)[0]
        out = [(float(c), tuple(b)) for c, b in zip(r.boxes.conf.tolist(), r.boxes.xyxyn.tolist())]
        return sorted(out, reverse=True)
    return find


# ---------- operating hours ----------

def in_service(t=None):
    """Tram hours: 6:00 to 2:00 the next morning, until 3:30 on Friday and Saturday nights.
    (Check the operator's posted schedule; holidays and outages are not modeled.)"""
    t = t or datetime.datetime.now()
    minutes = t.hour * 60 + t.minute
    if minutes >= 6 * 60:
        return True
    yesterday = (t - datetime.timedelta(days=1)).weekday()     # night after Fri (4) / Sat (5)
    end = 3 * 60 + 30 if yesterday in (4, 5) else 2 * 60
    return minutes < end


def period(t):
    """The time-of-day bucket a gap between passes is grouped into."""
    weekend = t.weekday() >= 5
    h = t.hour
    if h < 6:
        name = "late night"
    elif h < 10:
        name = "morning"
    elif h < 16:
        name = "midday"
    elif h < 20:
        name = "evening"
    else:
        name = "night"
    return ("weekend " if weekend else "weekday ") + name
