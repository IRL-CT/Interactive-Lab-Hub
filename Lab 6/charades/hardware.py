"""
Telephone Charades: the parts of one player's Pi. Everything has a fallback, so the game runs
on a Pi with missing parts (and on a laptop for testing):

  Button   Qwiic Button (Lab 4)  ->  Mini PiTFT buttons A/B (Lab 2)  ->  Enter key / laptop page
  Screen   Mini PiTFT (Lab 2)    ->  terminal
  Camera   USB webcam (Lab 5)    ->  --fake-camera (drawn frames, for testing)
  Mic      USB mic + faster-whisper (Lab 3)  ->  type the guess on the laptop page
  Voice    Piper (Lab 3)  ->  espeak  ->  silence
  Beeps    aplay  ->  silence

Button code adapted from Lab 4 (tipsy_tulip.py) and Lab 5 (Desk Curfew).
"""
import importlib.util
import io
import math
import os
import pathlib
import queue
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import wave

HERE = pathlib.Path(__file__).resolve().parent          # .../Lab 6/charades
LAB6 = HERE.parent
HUB = LAB6.parent                                        # .../Interactive-Lab-Hub
LONG_PRESS = 1.0


# ============================================================================ button


class Button:
    """wait(timeout) returns 'tap', 'hold' or None.

    Qwiic Button : tap, or hold for 1 s
    PiTFT        : button A (top) = tap, button B (bottom) = hold
    keyboard     : Enter = tap, 'h' + Enter = hold (works over ssh)
    """

    def __init__(self, choice="auto"):
        self.kind, self.qwiic, self.a, self.b = "keyboard", None, None, None
        self.keyboard = sys.stdin.isatty()
        if choice in ("auto", "qwiic"):
            try:
                import qwiic_button
                btn = qwiic_button.QwiicButton()
                if btn.begin():
                    self.qwiic, self.kind = btn, "qwiic"
                    btn.LED_off()
                elif choice == "qwiic":
                    print("(Qwiic Button not found: i2cdetect -y 1 should show 6f)")
            except Exception as err:
                if choice == "qwiic":
                    print(f"(Qwiic Button didn't start: {err})")
        if self.kind == "keyboard" and choice in ("auto", "pitft"):
            try:
                import board
                import digitalio
                self.a = digitalio.DigitalInOut(board.D23)
                self.b = digitalio.DigitalInOut(board.D24)
                self.a.switch_to_input(pull=digitalio.Pull.UP)
                self.b.switch_to_input(pull=digitalio.Pull.UP)
                self.kind = "pitft"
            except Exception as err:
                if choice == "pitft":
                    print(f"(PiTFT buttons didn't start: {err})")
        if self.kind == "keyboard" and not self.keyboard:
            self.kind = "page"
            print("Button: none (use the buttons on the laptop page)")
        else:
            extra = " + Enter key" if self.keyboard and self.kind != "keyboard" else ""
            print(f"Button: {self.kind}{extra}")

    def hints(self):
        return {"qwiic": ("tap", "hold"), "pitft": ("top btn", "bottom btn"),
                "keyboard": ("Enter", "h+Enter"), "page": ("click", "click")}[self.kind]

    def _key(self):
        if not self.keyboard:
            return None
        if select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline().strip().lower()
            return "hold" if line in ("h", "hold", "ok", "s", "send") else "tap"
        return None

    def wait(self, timeout=None):
        end = None if timeout is None else time.time() + timeout
        while end is None or time.time() < end:
            k = self._key()
            if k:
                return k
            if self.qwiic is not None:
                try:
                    if self.qwiic.is_button_pressed():
                        t0 = time.time()
                        while self.qwiic.is_button_pressed():
                            time.sleep(0.02)
                            if time.time() - t0 >= LONG_PRESS:
                                self.led(80)          # bright flash: you can let go now
                        return "hold" if time.time() - t0 >= LONG_PRESS else "tap"
                except OSError:
                    pass
            if self.a is not None:
                for pin, kind in ((self.a, "tap"), (self.b, "hold")):
                    if not pin.value:
                        while not pin.value:
                            time.sleep(0.02)
                        return kind
            time.sleep(0.02)
        return None

    def led(self, brightness):
        if self.qwiic is not None:
            try:
                self.qwiic.LED_on(brightness) if brightness else self.qwiic.LED_off()
            except Exception:
                pass

    def pulse(self):
        """Your turn: the button LED pulses."""
        if self.qwiic is not None:
            try:
                self.qwiic.LED_config(60, 1200, 300)
            except Exception:
                self.led(60)


# ============================================================================ screen


def _font(name, size):
    from PIL import ImageFont
    for path in (f"/usr/share/fonts/truetype/dejavu/{name}", name):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def fit_text(draw, text, width, height, max_size=40, min_size=12, bold=True):
    """Largest font size at which `text`, word-wrapped, fits in width x height. Returns (font, lines)."""
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    words = text.split() or [""]
    for size in range(max_size, min_size - 1, -2):
        font = _font(name, size)
        lines, line = [], ""
        for w in words:
            trial = f"{line} {w}".strip()
            if draw.textlength(trial, font=font) <= width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = w
        lines.append(line)
        line_h = size * 1.15
        if len(lines) * line_h <= height and all(draw.textlength(ln, font=font) <= width for ln in lines):
            return font, lines
    return _font(name, min_size), lines[:3]


class TerminalScreen:
    name = "terminal"

    def __init__(self):
        self.last = None

    def show(self, top, body, bottom="", mood="info"):
        if (top, body, bottom) != self.last:
            self.last = (top, body, bottom)
            print(f"[screen] {top} | {body} | {bottom}", flush=True)

    def off(self):
        pass


class PitftScreen:
    """Mini PiTFT 240x135 (Lab 2): a grey top line, big auto-fitting text, a coloured bottom bar."""
    name = "PiTFT"
    COLORS = {"info": (70, 70, 70), "act": (220, 80, 30), "guess": (40, 110, 220),
              "wait": (110, 70, 170), "ok": (0, 150, 70), "rec": (200, 20, 20), "reveal": (200, 150, 0)}

    def __init__(self):
        import board
        import digitalio
        import adafruit_rgb_display.st7789 as st7789
        from PIL import Image, ImageDraw
        self.disp = st7789.ST7789(
            board.SPI(), cs=digitalio.DigitalInOut(board.D5), dc=digitalio.DigitalInOut(board.D25),
            rst=None, baudrate=64000000, width=135, height=240, x_offset=53, y_offset=40)
        self.backlight = digitalio.DigitalInOut(board.D22)
        self.backlight.switch_to_output()
        self.backlight.value = True
        self.Image, self.ImageDraw = Image, ImageDraw
        self.W, self.H = 240, 135
        self.last = None

    def show(self, top, body, bottom="", mood="info"):
        if (top, body, bottom, mood) == self.last:
            return
        self.last = (top, body, bottom, mood)
        self.disp.image(render_screen(top, body, bottom, mood), 90)

    def off(self):
        self.disp.image(self.Image.new("RGB", (self.W, self.H)), 90)
        self.backlight.value = False


def render_screen(top, body, bottom="", mood="info", size=(240, 135)):
    """The PiTFT picture as a PIL image (also used by the tests to check that the text fits)."""
    from PIL import Image, ImageDraw
    W, H = size
    color = PitftScreen.COLORS.get(mood, PitftScreen.COLORS["info"])
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    tf, tlines = fit_text(d, top, W - 16, 18, max_size=14, min_size=10)
    d.text((8, 3), tlines[0], font=tf, fill=(160, 160, 160))
    font, lines = fit_text(d, body, W - 12, 70)
    line_h = font.size * 1.15
    y = 22 + (70 - len(lines) * line_h) / 2
    for ln in lines:
        d.text(((W - d.textlength(ln, font=font)) / 2, y), ln, font=font, fill=(255, 255, 255))
        y += line_h
    d.rectangle((0, H - 34, W, H), fill=color)
    bf, blines = fit_text(d, bottom, W - 12, 30, max_size=18, min_size=11, bold=False)
    d.text(((W - d.textlength(blines[0], font=bf)) / 2, H - 28), blines[0], font=bf, fill=(255, 255, 255))
    return img


def make_screen(choice="auto"):
    if choice in ("auto", "pitft"):
        try:
            s = PitftScreen()
            print("Screen: PiTFT")
            return s
        except ImportError as err:
            print(f"(PiTFT: missing library '{err.name}')")
        except OSError as err:
            if "busy" in str(err).lower():
                print("(PiTFT is busy: run  sudo systemctl stop piscreen.service  and start again)")
            else:
                print(f"(PiTFT didn't start: {err})")
        except Exception as err:
            print(f"(PiTFT didn't start: {err})")
    print("Screen: terminal only")
    return TerminalScreen()


# ============================================================================ camera


class Camera:
    """USB webcam -> a short clip of small JPEG frames (320x240, so each fits in one MQTT message)."""

    def __init__(self, index=0, size=(320, 240), quality=70):
        import cv2
        self.cv2, self.index, self.size, self.quality = cv2, index, size, quality
        self.cap = None
        self.ok = True
        print(f"Camera: webcam {index}")

    def open(self):
        if self.cap is None:
            self.cap = self.cv2.VideoCapture(self.index)
            self.cap.set(self.cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(self.cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if not self.cap.isOpened():
                self.cap = None
                raise RuntimeError("no webcam (is it plugged in? is another program using it?)")

    def warm(self, seconds, on_frame=None):
        """Keep reading during the countdown, so the exposure has settled when recording starts.
        on_frame gets a small JPEG about 8 times a second: the live preview on the laptop."""
        end, last = time.time() + seconds, 0
        while time.time() < end:
            ok, img = self.cap.read()
            if ok and on_frame and time.time() - last >= 0.12:
                last = time.time()
                jpg = self._encode(img)
                if jpg:
                    on_frame(jpg)

    MAX_BYTES = 6500     # keep every MQTT message small (~9 KB once base64), whatever the scene looks like

    def _encode(self, img):
        img = self.cv2.resize(img, self.size)
        q = self.quality
        while True:
            ok, buf = self.cv2.imencode(".jpg", img, [self.cv2.IMWRITE_JPEG_QUALITY, q])
            if not ok:
                return None
            if len(buf) <= self.MAX_BYTES or q <= 30:
                return buf.tobytes()
            q -= 10

    def frame(self):
        self.cap.grab()
        ok, img = self.cap.read()
        return self._encode(img) if ok else None

    def record(self, seconds, fps, on_progress=None, on_frame=None):
        frames, step = [], 1.0 / fps
        t0 = time.time()
        while time.time() - t0 < seconds:
            t = time.time()
            jpg = self.frame()
            if jpg:
                frames.append(jpg)
                if on_frame:
                    on_frame(jpg)
            if on_progress:
                on_progress(time.time() - t0)
            time.sleep(max(0, step - (time.time() - t)))
        return frames

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None


class FakeCamera:
    """Draws frames instead of filming: a stick figure waving and a caption. For testing without a webcam,
    and for the bots (who 'act' by showing a hangman version of their text)."""
    ok = True

    def __init__(self, label="FAKE CAMERA", size=(320, 240), fast=False, quiet=False):
        self.label, self.size, self.fast = label, size, fast
        if not quiet:
            print("Camera: fake (drawn frames)")

    def open(self):
        pass

    def warm(self, seconds, on_frame=None):
        steps = 1 if self.fast else max(1, int(seconds / 0.12))
        for i in range(steps):
            if on_frame:
                on_frame(draw_frame(i, steps, "LIVE PREVIEW", self.size))
            if not self.fast:
                time.sleep(seconds / steps)

    def close(self):
        pass

    def record(self, seconds, fps, on_progress=None, on_frame=None, caption=None):
        n = max(1, int(seconds * fps))
        self.takes = getattr(self, "takes", 0) + 1         # number the takes, so a redo looks different
        frames = []
        for i in range(n):
            frames.append(draw_frame(i, n, caption or f"{self.label} · take {self.takes}", self.size))
            if on_frame:
                on_frame(frames[-1])
            if on_progress:
                on_progress(i / fps)
            if not self.fast:
                time.sleep(1.0 / fps)
        return frames


def draw_frame(i, n, caption, size=(320, 240)):
    from PIL import Image, ImageDraw
    w, h = size
    img = Image.new("RGB", size, (30, 34, 60))
    d = ImageDraw.Draw(img)
    cx, top = w // 2, 50
    arm = math.sin(i / max(1, n - 1) * math.pi * 4) * 40
    d.ellipse((cx - 18, top, cx + 18, top + 36), outline=(250, 250, 250), width=4)
    d.line((cx, top + 36, cx, top + 110), fill=(250, 250, 250), width=4)
    d.line((cx, top + 60, cx - 45, top + 60 - arm), fill=(250, 200, 60), width=4)
    d.line((cx, top + 60, cx + 45, top + 60 + arm), fill=(250, 200, 60), width=4)
    d.line((cx, top + 110, cx - 30, top + 160), fill=(250, 250, 250), width=4)
    d.line((cx, top + 110, cx + 30, top + 160), fill=(250, 250, 250), width=4)
    font, lines = fit_text(d, caption, w - 20, 40, max_size=20, min_size=10)
    y = 6
    for ln in lines[:2]:
        d.text(((w - d.textlength(ln, font=font)) / 2, y), ln, font=font, fill=(255, 255, 255))
        y += font.size + 2
    d.text((8, h - 18), f"{i + 1}/{n}", font=_font("DejaVuSans.ttf", 11), fill=(160, 160, 190))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70)
    return buf.getvalue()


def make_camera(fake=False, index=0):
    if fake:
        return FakeCamera()
    try:
        return Camera(index)
    except ImportError:
        print("(no OpenCV: pip install opencv-python-headless) -> using the fake camera")
        return FakeCamera()


# ============================================================================ mic + speech to text


class Mic:
    """Record a few seconds with arecord, transcribe with faster-whisper (tiny.en, as in Lab 3)."""

    def __init__(self, enabled=True, device="default", model="tiny.en"):
        self.device, self.model_name = device, model
        self.model, self.error = None, None
        self.available = False
        if not enabled:
            print("Mic: off (type guesses on the laptop page)")
            return
        if shutil.which("arecord") is None:
            print("Mic: none (arecord not found) -> type guesses on the laptop page")
            return
        if importlib.util.find_spec("faster_whisper") is None:
            print("Mic: none (faster-whisper not installed, see README) -> type guesses on the laptop page")
            return
        self.available = True
        self.ready = threading.Event()
        threading.Thread(target=self._load, daemon=True).start()
        print(f"Mic: {device}, speech-to-text {model} (loading in the background)")

    def _load(self):
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
        except Exception as err:
            self.error = str(err)
            self.available = False
            print(f"(speech-to-text failed to load: {err}) -> type guesses on the laptop page")
        self.ready.set()

    def listen(self, seconds=4):
        """Returns the transcribed text, '' if nothing was understood, or None if the mic failed."""
        if not self.available:
            return None
        path = os.path.join(tempfile.gettempdir(), "charades_guess.wav")
        cmd = ["arecord", "-q", "-D", self.device, "-f", "S16_LE", "-r", "16000", "-c", "1", "-d", str(seconds), path]
        try:
            subprocess.run(cmd, check=True, timeout=seconds + 5)
        except Exception as err:
            print(f"(mic recording failed: {err}; check  arecord -l  and --mic-device)")
            return None
        self.ready.wait(60)
        if self.model is None:
            return None
        segments, _ = self.model.transcribe(path, beam_size=1, language="en", vad_filter=True)
        text = " ".join(s.text.strip() for s in segments).strip()
        return text.strip(" .!?").strip()


class FakeMic:
    available = True

    def __init__(self, answers=None, fast=False, quiet=False):
        self.answers = list(answers or ["a dancing robot", "swimming", "someone very confused"])
        self.fast = fast
        if not quiet:
            print("Mic: fake (pretends you said something)")

    def listen(self, seconds=4):
        if not self.fast:
            time.sleep(min(seconds, 1))
        return self.answers[int(time.time()) % len(self.answers)]


# ============================================================================ voice + beeps


def _voice_dirs():
    return [LAB6 / "voices", HUB / "Lab 3" / "voices", HUB / "Lab 3" / "speech-scripts", HUB / "Lab 5" / "voices"]


class Voice:
    """Says things without blocking the game (a worker thread with a queue)."""

    def __init__(self, enabled=True, model="en_US-lessac-medium"):
        self.cmd, self.ok = None, False
        self.q = queue.Queue()
        if not enabled:
            print("Voice: off")
            return
        if shutil.which("aplay") is None:
            print("Voice: none (aplay not found)")
            return
        voice_dir = next((d for d in _voice_dirs() if (d / f"{model}.onnx").exists()), None)
        if importlib.util.find_spec("piper") is not None and voice_dir is not None:
            self.cmd = ("piper", [sys.executable, "-m", "piper", "--model", model, "--data-dir", str(voice_dir), "--output-raw", "--"])
            print(f"Voice: Piper {model} ({voice_dir})")
        elif shutil.which("espeak-ng") or shutil.which("espeak"):
            self.cmd = ("espeak", [shutil.which("espeak-ng") or shutil.which("espeak"), "-s", "160"])
            print("Voice: espeak (install Piper for a nicer voice, see README)")
        else:
            print("Voice: none (no Piper voice file and no espeak, see README)")
            return
        self.ok = True
        threading.Thread(target=self._worker, daemon=True).start()

    def say(self, text):
        if self.ok:
            self.q.put(text)

    def _worker(self):
        while True:
            text = self.q.get()
            try:
                kind, base = self.cmd
                if kind == "piper":
                    p = subprocess.Popen(base + [text], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                    subprocess.run(["aplay", "-q", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
                                   stdin=p.stdout, stderr=subprocess.DEVNULL, timeout=60)
                    p.wait(timeout=10)
                else:
                    subprocess.run(base + [text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
            except Exception as err:
                print(f"(voice failed: {err})")


class Sounds:
    """Short beeps made on the fly: tick (countdown), go (recording starts), done (sent), turn (your turn)."""
    TONES = {"tick": [(880, 0.12)], "go": [(1320, 0.35)], "done": [(660, 0.1), (990, 0.18)],
             "turn": [(523, 0.12), (659, 0.12), (784, 0.2)], "stop": [(990, 0.1), (660, 0.18)]}

    def __init__(self, enabled=True):
        self.ok = enabled and shutil.which("aplay") is not None
        self.files = {}
        if self.ok:
            d = pathlib.Path(tempfile.mkdtemp(prefix="charades_"))
            for name, tones in self.TONES.items():
                self.files[name] = d / f"{name}.wav"
                self._write(self.files[name], tones)

    @staticmethod
    def _write(path, tones, rate=22050):
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            for freq, dur in tones:
                n = int(rate * dur)
                for i in range(n):
                    env = min(1, i / 300, (n - i) / 300)
                    w.writeframes(struct.pack("<h", int(12000 * env * math.sin(2 * math.pi * freq * i / rate))))

    def play(self, name):
        if self.ok and name in self.files:
            subprocess.Popen(["aplay", "-q", str(self.files[name])], stderr=subprocess.DEVNULL)
