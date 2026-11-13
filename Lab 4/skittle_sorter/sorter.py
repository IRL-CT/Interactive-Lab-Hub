#!/usr/bin/env python3
"""
Skittle color sorter for Raspberry Pi.

  USB webcam  ->  OpenCV reads the Skittle's color (red / orange / yellow / green)
  Qwiic OLED  ->  shows the color + a 3-second countdown, then "DROP NOW!"
  3 servos    ->  set the flaps so the dropped Skittle lands in the right bin

Usage
  python3 sorter.py                 run the sorter (headless is fine)
  python3 sorter.py --preview       also show the camera window with the aiming box
  python3 sorter.py --calibrate     teach it your Skittles under your lighting
  python3 sorter.py --sim --preview no OLED/servo pHAT needed (try it on a laptop)
  python3 sorter.py --find-servos   wiggle each servo to learn which flap is on which channel
  python3 sorter.py --test-servos   run each color's flap sequence

All settings are in config.py.
"""

import argparse
import json
import os
import sys
import time
from collections import deque

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config as C

HERE = os.path.dirname(os.path.abspath(__file__))
SHORT = {"red": "R", "orange": "O", "yellow": "Y", "green": "G"}
SERVO_MAP_FILE = "servo_channels.json"


# ==========================================================================
# Vision
# ==========================================================================
def roi_box(frame):
    h, w = frame.shape[:2]
    s = C.ROI_SIZE // 2
    cx, cy = w // 2, h // 2
    return cx - s, cy - s, cx + s, cy + s


def measure(frame):
    """Return (hue, coverage). hue is None when no Skittle is in the box.

    hue is the circular mean of the colorful pixels, on OpenCV's 0-179 scale.
    Circular mean matters because red sits on both ends (0 and 179).
    """
    x0, y0, x1, y1 = roi_box(frame)
    roi = cv2.GaussianBlur(frame[y0:y1, x0:x1], (5, 5), 0)
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    mask = (s >= C.MIN_SAT) & (v >= C.MIN_VAL)
    coverage = float(mask.mean())
    if coverage < C.MIN_COVERAGE:
        return None, coverage
    ang = h[mask].astype(np.float32) * (2 * np.pi / 180.0)
    mean = np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())
    hue = float((mean * 180.0 / (2 * np.pi)) % 180.0)
    return hue, coverage


def hue_dist(a, b):
    d = abs(a - b) % 180
    return min(d, 180 - d)


def classify(hue, centers):
    """Nearest calibrated color, or 'unknown' if nothing is close. None = nothing there."""
    if hue is None:
        return None
    best = min(centers, key=lambda c: hue_dist(hue, centers[c]))
    return best if hue_dist(hue, centers[best]) <= C.MAX_HUE_DIST else "unknown"


def circular_mean_hue(hues):
    ang = np.asarray(hues, dtype=np.float32) * (2 * np.pi / 180.0)
    m = np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())
    return float((m * 180.0 / (2 * np.pi)) % 180.0)


def load_centers():
    path = os.path.join(HERE, C.CALIBRATION_FILE)
    centers = dict(C.HUE_CENTERS)
    if os.path.exists(path):
        with open(path) as f:
            centers.update(json.load(f))
        print(f"[cal] loaded {path}: " + ", ".join(f"{k}={v:.1f}" for k, v in centers.items()))
    else:
        print("[cal] no calibration.json yet, using defaults (run --calibrate for best results)")
    return centers


def open_camera(index):
    backend = cv2.CAP_V4L2 if sys.platform.startswith("linux") else cv2.CAP_ANY
    cap = cv2.VideoCapture(index, backend)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, C.FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, C.FRAME_H)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        sys.exit(f"Could not open camera {index}. Check `ls /dev/video*` and try --camera 1")
    return cap


# ==========================================================================
# OLED screens
# ==========================================================================
def load_font(size):
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)   # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


F_BIG, F_MED, F_SMALL = load_font(22), load_font(14), load_font(10)
_FONT_CACHE = {}


def fit_font(text, max_w, max_size):
    """Largest font (<= max_size) that fits text into max_w pixels."""
    for size in range(max_size, 7, -1):
        if size not in _FONT_CACHE:
            _FONT_CACHE[size] = load_font(size)
        l, t, r, b = _FONT_CACHE[size].getbbox(text)
        if r - l <= max_w:
            return _FONT_CACHE[size]
    return _FONT_CACHE[8]


class Oled:
    """One SparkFun Qwiic OLED (SSD1306 128x32), driven like Lab 4/oled_test.py.
    In --sim mode it's a virtual screen (shown in the --preview window)."""

    _i2c = None
    _mux = None

    def __init__(self, address=0x3C, mux_channel=None, sim=False):
        self.last_key = None
        self.image = Image.new("1", (C.OLED_W, C.OLED_H))
        self.dev = None
        if sim:
            return
        import board
        import adafruit_ssd1306
        if Oled._i2c is None:
            Oled._i2c = board.I2C()
        bus = Oled._i2c
        if mux_channel is not None:
            import adafruit_tca9548a
            if Oled._mux is None:
                Oled._mux = adafruit_tca9548a.TCA9548A(Oled._i2c, address=C.MUX_ADDRESS)
            bus = Oled._mux[mux_channel]
        self.dev = adafruit_ssd1306.SSD1306_I2C(C.OLED_W, C.OLED_H, bus, addr=address)

    def show(self, image, key):
        """Only push to the screen when the content changed (I2C is slow)."""
        if key == self.last_key:
            return
        self.last_key, self.image = key, image
        if self.dev is not None:
            self.dev.image(image.rotate(180) if C.OLED_FLIP else image)
            self.dev.show()

    def clear(self):
        self.show(Image.new("1", (C.OLED_W, C.OLED_H)), "clear")


def _canvas(invert=False):
    img = Image.new("1", (C.OLED_W, C.OLED_H), 1 if invert else 0)
    return img, ImageDraw.Draw(img), (0 if invert else 1)


def _centered(d, y, text, font, fill):
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    d.text(((C.OLED_W - (r - l)) // 2 - l, y - t), text, font=font, fill=fill)


def tally_text(counts):
    return "  ".join(f"{SHORT[c]}:{counts[c]}" for c in C.COLORS)


def screen_idle(counts, hint):
    img, d, fg = _canvas()
    _centered(d, 1, hint, F_MED, fg)
    _centered(d, 21, tally_text(counts), F_SMALL, fg)
    return img


def screen_unknown():
    img, d, fg = _canvas()
    _centered(d, 1, "Not R/O/Y/G", F_MED, fg)
    _centered(d, 21, "try another one", F_SMALL, fg)
    return img


def screen_countdown(color, seconds_left):
    img, d, fg = _canvas()
    f = fit_font(color.upper(), C.OLED_W - 36, 20)
    l, t, r, b = d.textbbox((0, 0), color.upper(), font=f)
    d.text((2 - l, 1 - t), color.upper(), font=f, fill=fg)
    d.text((2, 21), "drop in...", font=F_SMALL, fill=fg)
    # countdown digit in a box on the right
    d.rectangle((C.OLED_W - 30, 0, C.OLED_W - 1, C.OLED_H - 1), outline=fg)
    digit = str(seconds_left)
    l, t, r, b = d.textbbox((0, 0), digit, font=F_BIG)
    d.text((C.OLED_W - 15 - (r - l) // 2 - l, (C.OLED_H - (b - t)) // 2 - t), digit, font=F_BIG, fill=fg)
    return img


def screen_drop(color):
    img, d, fg = _canvas(invert=True)   # inverted = flashes white so people notice
    _centered(d, 1, "DROP NOW!", fit_font("DROP NOW!", C.OLED_W - 6, 20), fg)
    _centered(d, 22, f"-> {color.upper()} bin", F_SMALL, fg)
    return img


def screen_done(color, n):
    img, d, fg = _canvas()
    _centered(d, 1, f"{color.upper()} #{n}", F_MED, fg)
    _centered(d, 21, "next Skittle!", F_SMALL, fg)
    return img


def screen_tally(counts):
    img, d, fg = _canvas()
    d.text((4, 0), f"R {counts['red']:>3}", font=F_MED, fill=fg)
    d.text((68, 0), f"O {counts['orange']:>3}", font=F_MED, fill=fg)
    d.text((4, 17), f"Y {counts['yellow']:>3}", font=F_MED, fill=fg)
    d.text((68, 17), f"G {counts['green']:>3}", font=F_MED, fill=fg)
    return img


def screen_message(line1, line2=""):
    img, d, fg = _canvas()
    _centered(d, 1, line1, F_MED, fg)
    if line2:
        _centered(d, 21, line2, F_SMALL, fg)
    return img


# ==========================================================================
# Servos / flaps
# ==========================================================================
class Gates:
    """3 servos on the SparkFun Servo pHAT (pi_servo_hat, like Lab 4/pi_servo_hat_test.py).
    The pHAT makes the PWM in hardware, so the servos hold still without jitter."""

    def __init__(self, sim=False):
        self.sim = sim
        self.current = None
        if sim:
            self.hat = None
            return
        import pi_servo_hat
        self.hat = pi_servo_hat.PiServoHat()
        self.hat.restart()

    @property
    def channels(self):
        """Which pHAT channel each flap is on. servo_channels.json (from --find-servos) wins over config.py."""
        path = os.path.join(HERE, SERVO_MAP_FILE)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return dict(C.SERVO_CHANNELS)

    def move(self, name, angle):
        ch = self.channels[name]
        if self.hat is not None:
            self.hat.move_servo_position(ch, angle)
        print(f"[servo] {name} (ch {ch}) -> {angle}")

    def move_channel(self, ch, angle):
        if self.hat is not None:
            self.hat.move_servo_position(ch, angle)

    def _apply(self, angles):
        for name in self.channels:
            self.move(name, angles.get(name, C.HOME[name]))

    def stage(self, color, n):
        """Stage 1 tips the top flap; stage 2 tips the second-level flap (left or right)."""
        route = C.ROUTES[color]
        names = [k for k in route if (k in FIRST_STAGE) == (n == 1)]
        for name in names:
            self.move(name, route[name])
        self.current = color

    def home(self):
        self._apply(C.HOME)
        self.current = None

    def close(self):
        self.home()
        time.sleep(C.SERVO_SETTLE_S)


# ==========================================================================
# Sorter state machine
# ==========================================================================
IDLE, COUNTDOWN, DROP, STAGE1, STAGE2, CLEAR = "IDLE", "COUNTDOWN", "DROP", "TOP_FLAP", "SECOND_FLAP", "CLEAR"

# Timing for the drop sequence. Set these in config.py to override.
DROP_WAIT_S = getattr(C, "DROP_WAIT_S", 2.0)      # after "DROP NOW!": time for the person to drop it in
STAGE_DELAY_S = getattr(C, "STAGE_DELAY_S", 1.5)  # top flap tips, wait this long, then the second flap tips
SORT_HOLD_S = getattr(C, "SORT_HOLD_S", 1.5)      # second flap holds this long before everything goes home
FIRST_STAGE = getattr(C, "FIRST_STAGE", ["top"])


class Sorter:
    def __init__(self, screens, gates, centers):
        self.screens, self.gates, self.centers = screens, gates, centers
        self.counts = {c: 0 for c in C.COLORS}
        self.history = deque(maxlen=C.STABLE_FRAMES)
        self.state = IDLE
        self.color = None
        self.t_state = 0.0
        self.empty_frames = 0
        self.last_label = None

    def _go(self, state, now):
        print(f"[state] {self.state} -> {state}" + (f" ({self.color})" if self.color else ""))
        self.state, self.t_state = state, now

    def step(self, frame, now):
        """Process one camera frame. Returns (label, hue, coverage) for the preview overlay."""
        hue, cov = measure(frame)
        label = classify(hue, self.centers)
        self.last_label = label
        elapsed = now - self.t_state

        if self.state == IDLE:
            self.history.append(label)
            stable = (len(self.history) == self.history.maxlen
                      and len(set(self.history)) == 1 and label is not None)
            if stable and label != "unknown":
                self.color = label                 # servos stay put until after the countdown
                self._go(COUNTDOWN, now)
            elif stable and label == "unknown":
                self._show(screen_unknown(), "unknown")
            elif label is None:
                self._show(screen_idle(self.counts, "Show a Skittle"), ("idle", tuple(self.counts.values())))
            else:
                self._show(screen_idle(self.counts, "Hold still..."), ("hold", tuple(self.counts.values())))

        elif self.state == COUNTDOWN:
            left = C.COUNTDOWN_S - elapsed
            if left <= 0:
                self._go(DROP, now)
                self._show(screen_drop(self.color), ("drop", self.color))
            else:
                n = int(np.ceil(left))
                self._show(screen_countdown(self.color, n), ("cd", self.color, n))

        elif self.state == DROP:
            # Person drops the Skittle onto the top flap; nothing moves yet.
            self._show(screen_drop(self.color), ("drop", self.color))
            if elapsed >= DROP_WAIT_S:
                self.gates.stage(self.color, 1)   # top flap tips
                self._go(STAGE1, now)

        elif self.state == STAGE1:
            self._show(screen_message(self.color.upper(), "sorting..."), ("s1", self.color))
            if elapsed >= STAGE_DELAY_S:
                self.gates.stage(self.color, 2)   # second flap (left or right) tips
                self._go(STAGE2, now)

        elif self.state == STAGE2:
            if elapsed >= SORT_HOLD_S:
                self.gates.home()
                self.counts[self.color] += 1
                print(f"[sort] {self.color} -> total {self.counts[self.color]}  |  {tally_text(self.counts)}")
                self.empty_frames = 0
                self._go(CLEAR, now)

        elif self.state == CLEAR:
            # Wait until the camera's box is empty so the same Skittle isn't counted twice.
            self._show(screen_done(self.color, self.counts[self.color]), ("done", self.color, self.counts[self.color]))
            self.empty_frames = self.empty_frames + 1 if label is None else 0
            if self.empty_frames >= C.CLEAR_FRAMES:
                self.history.clear()
                self.color = None
                self._go(IDLE, now)

        if len(self.screens) > 1:
            self.screens[1].show(screen_tally(self.counts), ("tally", tuple(self.counts.values())))
        return label, hue, cov

    def _show(self, img, key):
        self.screens[0].show(img, key)


# ==========================================================================
# Preview window helpers
# ==========================================================================
BGR = {"red": (40, 40, 230), "orange": (0, 140, 255), "yellow": (0, 220, 240),
       "green": (60, 200, 60), "unknown": (200, 200, 200), None: (160, 160, 160)}


def draw_preview(frame, label, hue, cov, sorter, screens):
    x0, y0, x1, y1 = roi_box(frame)
    out = frame.copy()
    cv2.rectangle(out, (x0, y0), (x1, y1), BGR.get(label, (255, 255, 255)), 2)
    txt = f"{label or '-'}  hue={hue:.1f}" if hue is not None else f"-  coverage={cov:.2f}"
    cv2.putText(out, txt, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(out, sorter.state, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    # mirror the OLED(s) under the camera image
    rows = [out]
    for s in screens:
        o = np.array(s.image.convert("L"))
        o = cv2.resize(o, (out.shape[1], out.shape[1] * C.OLED_H // C.OLED_W), interpolation=cv2.INTER_NEAREST)
        o = cv2.cvtColor(o, cv2.COLOR_GRAY2BGR)
        o[(o[..., 0] > 0)] = (255, 200, 120)   # OLED-ish blue
        rows.append(o)
    return np.vstack(rows)


# ==========================================================================
# Modes
# ==========================================================================
def make_screens(sim):
    screens = []
    for i, s in enumerate(C.OLEDS):
        try:
            screens.append(Oled(s["address"], s.get("mux_channel"), sim=sim))
        except Exception as e:   # keep running even if a screen is unplugged
            print(f"[oled] screen {i} not available ({e}); using a virtual one")
            screens.append(Oled(sim=True))
    return screens


def run(args):
    centers = load_centers()
    gates = Gates(sim=args.sim)   # first: its restart() also frees I2C 0x70 for a Qwiic Mux
    gates.home()
    screens = make_screens(args.sim)
    cap = open_camera(args.camera)
    sorter = Sorter(screens, gates, centers)
    print("Running. Ctrl+C to stop." + ("  (press q in the window to quit)" if args.preview else ""))
    fails = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                fails += 1
                if fails > 30:
                    screens[0].show(screen_message("Camera error", "check USB"), "camerr")
                    sys.exit("Camera stopped returning frames.")
                time.sleep(0.05)
                continue
            fails = 0
            label, hue, cov = sorter.step(frame, time.monotonic())
            if args.preview:
                cv2.imshow("Skittle sorter", draw_preview(frame, label, hue, cov, sorter, screens))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        print("\nFinal tally: " + tally_text(sorter.counts))
        gates.close()
        for s in screens:
            s.clear()
        cap.release()
        cv2.destroyAllWindows()


def calibrate(args):
    """Hold each color in the box, press Enter, it samples ~2 s and saves the hue."""
    screens = make_screens(args.sim)
    cap = open_camera(args.camera)
    result = {}
    print("\nCalibration: hold each Skittle in the middle of the camera view,"
          "\nunder the same lighting you'll use for sorting.\n")
    for color in C.COLORS:
        while True:
            screens[0].show(screen_message(f"Show {color.upper()}", "then press Enter"), ("cal", color))
            input(f"  Hold a {color.upper()} Skittle in the box and press Enter... ")
            for _ in range(5):           # flush frames buffered while we waited
                cap.read()
            hues, covs = [], []
            for _ in range(60):
                ok, frame = cap.read()
                if not ok:
                    continue
                hue, cov = measure(frame)
                covs.append(cov)
                if hue is not None:
                    hues.append(hue)
            if len(hues) < 20:
                print(f"    Only saw a Skittle in {len(hues)}/60 frames (coverage ~{np.mean(covs):.2f}). "
                      f"Move it closer / into the box, or lower MIN_SAT/MIN_COVERAGE. Try again.")
                continue
            h = circular_mean_hue(hues)
            spread = float(np.mean([hue_dist(x, h) for x in hues]))
            result[color] = round(h, 1)
            print(f"    {color}: hue {h:.1f} (jitter ±{spread:.1f})")
            break

    names = list(result)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            gap = hue_dist(result[a], result[b])
            if gap < 6:
                print(f"  ! {a} and {b} are only {gap:.1f} hue apart, so they may get mixed up. "
                      f"Use brighter, even, white light (no yellow room light) and calibrate again.")
    path = os.path.join(HERE, C.CALIBRATION_FILE)
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved {path}")
    screens[0].show(screen_message("Calibrated!", "run sorter.py"), "caldone")
    cap.release()


def test_servos(args):
    """Run the real drop sequence for each color, without the camera."""
    gates = Gates(sim=args.sim)
    print(f"Using channels: {gates.channels}")
    try:
        gates.home()
        for color in C.COLORS:
            input(f"Press Enter to run the {color.upper()} sequence... ")
            gates.stage(color, 1)
            time.sleep(STAGE_DELAY_S)
            gates.stage(color, 2)
            time.sleep(SORT_HOLD_S)
            gates.home()
    finally:
        gates.close()


def find_servos(args):
    """Wiggle one channel at a time and ask which flap moved. Saves servo_channels.json."""
    gates = Gates(sim=args.sim)
    names = {"t": "top", "l": "left", "r": "right"}
    found = {}
    for ch in range(args.channels):
        while True:
            print(f"\nWiggling channel {ch}...")
            for a in (60, 30, 90, 30, 90, 60):
                gates.move_channel(ch, a)
                time.sleep(0.35)
            ans = input("Which flap moved? [t]op / [l]eft / [r]ight / [n]one / [a]gain: ").strip().lower()[:1]
            if ans == "a":
                continue
            if ans in names:
                found[names[ans]] = ch
            break
    missing = [n for n in ("top", "left", "right") if n not in found]
    if missing:
        print(f"\nDidn't find: {', '.join(missing)}. Check the plugs (brown/black wire to the outside edge, "
              f"USB-C power on the pHAT) and run --find-servos again.")
        return
    path = os.path.join(HERE, SERVO_MAP_FILE)
    with open(path, "w") as f:
        json.dump(found, f, indent=2)
    print(f"\nSaved {path}: {found}\nNow run:  python sorter.py --test-servos")


def main():
    p = argparse.ArgumentParser(description="Raspberry Pi Skittle sorter")
    p.add_argument("--calibrate", action="store_true", help="learn hue of each color")
    p.add_argument("--test-servos", action="store_true", help="run each color's flap sequence")
    p.add_argument("--find-servos", action="store_true", help="figure out which channel each flap is on")
    p.add_argument("--channels", type=int, default=3, help="how many channels --find-servos checks")
    p.add_argument("--preview", action="store_true", help="show camera window (needs a desktop)")
    p.add_argument("--sim", action="store_true", help="no OLED / servos attached (virtual hardware)")
    p.add_argument("--camera", type=int, default=C.CAMERA_INDEX)
    args = p.parse_args()
    if args.calibrate:
        calibrate(args)
    elif args.test_servos:
        test_servos(args)
    elif args.find_servos:
        find_servos(args)
    else:
        run(args)


if __name__ == "__main__":
    main()