"""The Monster Under the Bed: Lab 5 Part 2.

A camera under the bed watches the floor beside it. Every trip out of bed at night
makes the monster angrier. In the morning it tells you how many times you got up.

    python overnight.py                 # the real thing: voice, camera, PiTFT, Piper, Qwen
    python overnight.py --demo          # short timings for testing and the class demo
    python overnight.py --wake 7:00     # also treat "feet on the floor for 2 min after 7:00" as morning

The three moments (Parts G, H, I):
  before bed  say "I'm going to sleep" (or type s, or press the PiTFT top button).
              The monster says "Okay, one minute!" and counts down 60 s while you get in bed.
              Then it photographs the empty floor and starts watching.
  asleep      every 5 s: are there feet on the floor? A trip only counts after 15 s of feet,
              and ends after 20 s without. Each trip makes the monster angrier on screen.
  awake       say "I'm awake" (or type a, or press the bottom button) with your feet on the
              floor. The monster gives its verdict out loud and on screen, then fades out.

Keyboard commands (type + Enter, works over ssh and in tmux):
  s  going to sleep      a  I'm awake      f  toggle fake feet (with --fake-feet)      q  quit

Everything stays on the Pi. Logs: night_log.jsonl (same format as overnight.py, so
morning.py --log night_log.jsonl still works) and nights.jsonl (one summary per night).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import queue
import re
import sys
import threading
import time
from pathlib import Path

import numpy as np

import monster_screens as screens

HERE = Path(__file__).resolve().parent
LAB3 = HERE.parent / "Lab 3"
SAMPLE_RATE = 16000


# --------------------------------------------------------------------------- helpers

def now() -> dt.datetime:
    return dt.datetime.now()


def clock(t: dt.datetime) -> str:
    """1:12 AM"""
    return t.strftime("%I:%M %p").lstrip("0")


def short_clock(t: dt.datetime) -> str:
    """1:12 (what we let Qwen say, and what we check its answer against)"""
    return t.strftime("%I:%M").lstrip("0")


def anger_level(trips: list[dict]) -> int:
    """The monster's face, from the number of trips only (computed in code, never by the model):
    0 asleep, 1 one eye open, 2 both eyes open, 3+ rage face."""
    return min(len(trips), 3)


# --------------------------------------------------------------------------- hardware (each part falls back gracefully)

class Screen:
    """The Adafruit MiniPiTFT (ST7789, 240x135), same setup as Lab 2 and Lab 3.
    Also writes the current screen to monster_screen.png so you can watch it over ssh/VNC."""

    def __init__(self, enabled: bool = True, window: bool = False) -> None:
        self.disp = None
        self.backlight = None
        self.window = window
        self.last = None
        import os
        if window and os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("DISPLAY"):
            os.environ["DISPLAY"] = ":0"       # Pi OS Wayland desktop: OpenCV's window goes through XWayland
        if not enabled:
            return
        try:
            import board
            import digitalio
            import adafruit_rgb_display.st7789 as st7789

            self.disp = st7789.ST7789(
                board.SPI(), cs=digitalio.DigitalInOut(board.D5),
                dc=digitalio.DigitalInOut(board.D25), rst=None, baudrate=64000000,
                width=135, height=240, x_offset=53, y_offset=40)
            self.backlight = digitalio.DigitalInOut(board.D22)
            self.backlight.switch_to_output(value=True)
        except Exception as e:
            print(f"[warn] PiTFT not available ({e}); writing monster_screen.png instead", flush=True)

    def show(self, image) -> None:
        if image.tobytes() == self.last:
            return
        self.last = image.tobytes()
        if self.disp:
            self.disp.image(image, 90)
        image.save(HERE / "monster_screen.png")
        if self.window:
            import cv2
            cv2.imshow("monster", cv2.cvtColor(np.array(image.resize((480, 270))), cv2.COLOR_RGB2BGR))
            cv2.waitKey(1)

    def pump(self) -> None:
        """OpenCV windows only redraw while waitKey runs, so call this often."""
        if self.window:
            import cv2
            cv2.waitKey(1)

    def wait(self, seconds: float) -> None:
        """Like time.sleep, but keeps the window alive."""
        end = time.time() + seconds
        while time.time() < end:
            self.pump()
            time.sleep(0.05)

    def light(self, on: bool) -> None:
        if self.backlight:
            self.backlight.value = on


class Buttons:
    """PiTFT buttons: top (D23) = going to sleep, bottom (D24) = I'm awake. Optional."""

    def __init__(self, events: queue.Queue, enabled: bool = True) -> None:
        self.pins = []
        if not enabled:
            return
        try:
            import board
            import digitalio
            for pin in (board.D23, board.D24):
                b = digitalio.DigitalInOut(pin)
                b.switch_to_input(pull=digitalio.Pull.UP)
                self.pins.append(b)
            threading.Thread(target=self._run, args=(events,), daemon=True).start()
        except Exception as e:
            print(f"[warn] buttons not available ({e})", flush=True)

    def _run(self, events: queue.Queue) -> None:
        was = [True, True]
        while True:
            for i, b in enumerate(self.pins):
                v = b.value
                if was[i] and not v:                      # pressed (active low)
                    events.put(("sleep", "button") if i == 0 else ("awake", "button"))
                was[i] = v
            time.sleep(0.05)


def growl_sound(seconds: float = 1.2, rate: int = 22050, loud: float = 1.0) -> np.ndarray:
    """A monster growl made from scratch: a low wobbling buzz (~70 Hz) with a rattle and
    some rumble noise, faded in and out. Returns float32 audio in -1..1."""
    t = np.arange(int(seconds * rate)) / rate
    f0 = 68 + 14 * np.sin(2 * np.pi * 0.9 * t)                 # pitch wobbles
    phase = np.cumsum(f0) / rate
    buzz = 2 * (phase % 1) - 1                                  # sawtooth: harsh like a throat
    rattle = 0.55 + 0.45 * np.sin(2 * np.pi * 24 * t)           # the "rrrr" flutter
    noise = np.random.default_rng().normal(0, 1, len(t))
    rumble = np.convolve(noise, np.ones(40) / 40, mode="same") * 3
    sound = (buzz * rattle + 0.5 * rumble)
    sound = np.convolve(sound, np.ones(6) / 6, mode="same")      # take the fizz off the top
    env = np.minimum(1, t / 0.15) * np.minimum(1, (seconds - t) / 0.35)
    sound = sound * env
    return (sound / (np.abs(sound).max() + 1e-9) * 0.9 * loud).astype(np.float32)


def _shape(sound: np.ndarray, rate: int, peaks: list[tuple[float, float, float]],
           low: float = 0, high: float = 1e9) -> np.ndarray:
    """Filter in the frequency domain: keep low..high Hz and boost resonances (freq, width, gain),
    which is what a throat or mouth does to a raw sound."""
    spec = np.fft.rfft(sound)
    f = np.fft.rfftfreq(len(sound), 1 / rate)
    gain = ((f >= low) & (f <= high)).astype(float) * 0.15
    for freq, width, g in peaks:
        gain += g * np.exp(-((f - freq) / width) ** 2)
    return np.fft.irfft(spec * gain, n=len(sound))


def _wobble(n: int, rate: int, speed: float, rng) -> np.ndarray:
    """A slow random curve between 0 and 1, so the sound isn't machine-steady."""
    pts = rng.uniform(0, 1, int(n / rate * speed) + 3)
    return np.interp(np.linspace(0, len(pts) - 1, n), np.arange(len(pts)), pts)


def snarl_sound(seconds: float = 1.4, rate: int = 22050) -> np.ndarray:
    """An animal growl: an irregular pulse train (a throat vibrating ~60 times a second,
    never exactly evenly) plus breath noise, shaped by throat resonances."""
    rng = np.random.default_rng()
    n = int(seconds * rate)
    out = np.zeros(n)
    i = 0
    while i < n:                                    # one pulse per vocal-fold flap, with jitter
        period = rate / rng.uniform(48, 75)
        width = int(period * 0.3)
        if i + width < n:
            out[i:i + width] += np.hanning(width) * rng.uniform(0.6, 1.0)
        i += int(period)
    breath = rng.normal(0, 0.35, n)
    raw = out + breath * (0.4 + 0.6 * _wobble(n, rate, 6, rng))
    voiced = _shape(raw, rate, [(320, 120, 1.0), (750, 200, 0.7), (1900, 400, 0.25)], 40, 3500)
    t = np.arange(n) / rate
    env = np.minimum(1, t / 0.12) * np.minimum(1, (seconds - t) / 0.4) * (0.6 + 0.4 * _wobble(n, rate, 9, rng))
    s = voiced * env
    return (s / (np.abs(s).max() + 1e-9) * 0.9).astype(np.float32)


def hiss_sound(seconds: float = 1.1, rate: int = 22050) -> np.ndarray:
    """A cat hiss: a sharp burst of breathy noise, mostly high frequencies, that tails off."""
    rng = np.random.default_rng()
    n = int(seconds * rate)
    noise = rng.normal(0, 1, n)
    s = _shape(noise, rate, [(3200, 900, 1.0), (6000, 1500, 0.8), (1500, 500, 0.25)], 1200, 10000)
    t = np.arange(n) / rate
    env = np.minimum(1, t / 0.03) * np.exp(-t / (seconds * 0.55)) * (0.75 + 0.25 * _wobble(n, rate, 14, rng))
    s = s * env
    return (s / (np.abs(s).max() + 1e-9) * 0.85).astype(np.float32)


def huh_tone(rate: int = 22050) -> np.ndarray:
    """Fallback 'huh?' when Piper is missing: a short rising hum."""
    t = np.arange(int(0.45 * rate)) / rate
    f = 160 + 220 * (t / t[-1]) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / rate) * np.minimum(1, t / 0.05) * np.minimum(1, (t[-1] - t) / 0.1)
    return (0.6 * s).astype(np.float32)


class Voice:
    """Piper (same voice as Lab 3), played slower and lower so it sounds like a monster,
    plus the trip sounds: 1st 'Huh?', 2nd a growl, 3rd+ 'Grrrr!' and a bigger growl.
    Put your own recordings in sounds/trip1.wav, trip2.wav, trip3.wav to replace them."""

    def __init__(self, voice_path: Path, enabled: bool, speaking: threading.Event) -> None:
        self.voice = None
        self.sd = None
        self.speaking = speaking
        if not enabled:
            return
        try:
            import sounddevice as sd
            self.sd = sd
        except Exception as e:
            print(f"[warn] no audio output ({e}); printing speech instead", flush=True)
            return
        try:
            from piper import PiperVoice
            self.voice = PiperVoice.load(str(voice_path))
        except Exception as e:
            print(f"[warn] Piper not available ({e}); printing speech, trip sounds still play", flush=True)

    def _synth(self, text: str) -> tuple[np.ndarray, int]:
        """Piper speech as float32 audio, at the slowed 'monster' sample rate."""
        audio, rate = [], 22050
        for chunk in self.voice.synthesize(text):
            audio.append(np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16))
            rate = chunk.sample_rate
        pcm = np.concatenate(audio).astype(np.float32) / 32768
        return pcm, int(rate * 0.82)          # playing it slow drops the pitch: monster voice

    def _play(self, audio: np.ndarray, rate: int, volume: float) -> None:
        if self.sd is None:
            return
        self.speaking.set()                    # the ears ignore the mic while we make noise
        try:
            pcm = np.clip(audio * volume, -1, 1)
            self.sd.play((pcm * 32767).astype(np.int16), samplerate=rate)
            self.sd.wait()
        except Exception as e:
            print(f"[warn] could not play sound ({e})", flush=True)
        finally:
            time.sleep(0.4)
            self.speaking.clear()

    def say(self, text: str, volume: float = 1.0) -> None:
        print(f"  MONSTER: {text}", flush=True)
        if self.voice is None:
            return
        try:
            pcm, rate = self._synth(text)
        except Exception as e:
            print(f"[warn] could not synthesize speech ({e})", flush=True)
            return
        self._play(pcm, rate, volume)

    def trip_sound(self, n: int, volume: float) -> None:
        """The monster notices your feet: n is which trip this is."""
        n = min(n, 3)
        label = {1: "Huh?", 2: "*snarl*", 3: "*HISS* + *snarl*"}[n]
        print(f"  MONSTER (trip {n}): {label}", flush=True)
        if self.sd is None:
            return
        custom = HERE / "sounds" / f"trip{n}.wav"
        if custom.exists():                                 # your own recording wins
            import wave
            with wave.open(str(custom)) as w:
                rate, ch = w.getframerate(), w.getnchannels()
                data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
            if ch > 1:
                data = data.reshape(-1, ch).mean(axis=1)
            self._play(data, rate, volume)
            return
        rate = 22050
        try:
            if n == 1:
                audio, rate = self._synth("Huh?") if self.voice else (huh_tone(rate), rate)
            elif n == 2:
                audio = snarl_sound(1.4, rate)                       # an animal growl
            else:
                audio = np.concatenate([hiss_sound(1.1, rate),       # cat hiss, then a long snarl
                                        np.zeros(int(0.15 * rate), np.float32),
                                        snarl_sound(1.8, rate)])
        except Exception as e:
            print(f"[warn] could not make trip sound ({e})", flush=True)
            return
        self._play(audio, rate, volume * (1.2 if n == 3 else 1.0))


def parse_command(text: str) -> str | None:
    """Only two phrases matter. Anything else (including whisper's hallucinated 'Thank you.') is ignored."""
    t = text.lower()
    if re.search(r"\b(i'?m awake|awake|i'?m up|good morning|getting up|woke up)\b", t):
        return "awake"
    if re.search(r"\b(going to sleep|go to sleep|going to bed|goodnight|good night|sleep)\b", t):
        return "sleep"
    return None


class Ears:
    """Silero VAD + faster-whisper, the Lab 3 listen.py pipeline, running in the background.
    It ignores the microphone while the monster is talking so it doesn't hear itself."""

    def __init__(self, events: queue.Queue, speaking: threading.Event, vad_path: Path,
                 model: str, enabled: bool) -> None:
        self.events = events
        self.speaking = speaking
        if not enabled:
            return
        try:
            import sherpa_onnx
            import sounddevice as sd
            from faster_whisper import WhisperModel
            print("loading speech recognition...", flush=True)
            self.sd = sd
            self.recognizer = WhisperModel(model, device="cpu", compute_type="int8")
            config = sherpa_onnx.VadModelConfig()
            config.silero_vad.model = str(vad_path)
            config.silero_vad.min_silence_duration = 0.6
            config.silero_vad.min_speech_duration = 0.25
            config.sample_rate = SAMPLE_RATE
            self.vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
            self.window = config.silero_vad.window_size
            threading.Thread(target=self._run, daemon=True).start()
        except Exception as e:
            print(f"[warn] microphone/speech recognition not available ({e}); "
                  "use the keyboard (s / a) or the PiTFT buttons", flush=True)

    def _run(self) -> None:
        buffer = np.empty(0, dtype=np.float32)
        with self.sd.InputStream(channels=1, dtype="float32", samplerate=SAMPLE_RATE) as stream:
            while True:
                chunk, _ = stream.read(int(0.1 * SAMPLE_RATE))
                if self.speaking.is_set():                 # don't listen to ourselves
                    buffer = np.empty(0, dtype=np.float32)
                    if hasattr(self.vad, "reset"):
                        self.vad.reset()
                    continue
                buffer = np.concatenate([buffer, chunk.reshape(-1)])
                while len(buffer) > self.window:
                    self.vad.accept_waveform(buffer[:self.window])
                    buffer = buffer[self.window:]
                while not self.vad.empty():
                    utterance = np.array(self.vad.front.samples, dtype=np.float32)
                    self.vad.pop()
                    segments, _ = self.recognizer.transcribe(utterance, beam_size=1, language="en")
                    heard = " ".join(s.text.strip() for s in segments).strip()
                    if not heard:
                        continue
                    cmd = parse_command(heard)
                    print(f"  heard: {heard!r} -> {cmd or 'ignored'}", flush=True)
                    if cmd:
                        self.events.put((cmd, "voice"))


def keyboard(events: queue.Queue) -> None:
    """Type s / a / f / q + Enter. Handy over ssh and for testing without a mic."""
    for line in sys.stdin:
        c = line.strip().lower()
        if c in ("s", "sleep"):
            events.put(("sleep", "keyboard"))
        elif c in ("a", "awake"):
            events.put(("awake", "keyboard"))
        elif c == "f":
            events.put(("fake_feet", "keyboard"))
        elif c in ("q", "quit"):
            events.put(("quit", "keyboard"))


# --------------------------------------------------------------------------- the sensor

class FeetDetector:
    """Are there feet on the floor beside the bed?

    YOLO has no "foot" class, so two signals are combined:
      1. change: how much of the floor region differs from the empty-floor photo taken
         when the countdown ended (slippers left there are part of the baseline).
      2. yolo: a low-confidence "person" box inside the floor region (legs often get one).
    feet = enough change OR a person box. If almost the whole region changes at once,
    that's a light being switched on, not feet: the baseline is re-taken instead.
    If the picture is too dark, the answer is None ("can't see"), never "no feet".
    """

    def __init__(self, camera: int, roi: tuple[float, float, float, float], change_area: float,
                 pixel_diff: int, dark_level: float, use_yolo: bool, yolo_conf: float) -> None:
        import cv2
        self.cv2 = cv2
        self.roi = roi
        self.change_area = change_area
        self.pixel_diff = pixel_diff
        self.dark_level = dark_level
        self.yolo_conf = yolo_conf
        self.baseline = None
        self.cap = cv2.VideoCapture(camera)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not self.cap.isOpened():
            raise SystemExit("no webcam found: is it plugged in? (or use --fake-feet to test without one)")
        self.model = None
        if use_yolo:
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(HERE / "yolo26n_ncnn_model"))
            except Exception as e:
                print(f"[warn] YOLO not available ({e}); using floor change only", flush=True)

    def frame(self):
        for _ in range(4):                 # the webcam buffers frames; skip the stale ones
            self.cap.grab()
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("no frame from the webcam")
        return frame

    def _floor(self, frame):
        h, w = frame.shape[:2]
        x0, y0, x1, y1 = self.roi
        crop = frame[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
        gray = self.cv2.cvtColor(crop, self.cv2.COLOR_BGR2GRAY)
        return self.cv2.GaussianBlur(gray, (21, 21), 0).astype(np.float32)

    def take_baseline(self) -> float:
        """Average a few frames of the empty floor. Returns its brightness."""
        frames = [self._floor(self.frame()) for _ in range(5)]
        self.baseline = np.mean(frames, axis=0)
        return float(self.baseline.mean())

    def look(self) -> dict:
        frame = self.frame()
        floor = self._floor(frame)
        bright = float(floor.mean())
        result = {"feet": None, "change": 0.0, "yolo": 0.0, "bright": round(bright, 1), "frame": frame}
        if bright < self.dark_level:
            return result                                  # can't see: say so
        if self.baseline is None:
            self.baseline = floor
        changed = float((np.abs(floor - self.baseline) > self.pixel_diff).mean())
        result["change"] = round(changed, 3)
        if changed > 0.7:                                  # a light went on/off: re-learn the empty floor
            self.baseline = floor
            result["change"] = 0.0
            result["relit"] = True
            changed = 0.0
        if self.model is not None:
            h, w = frame.shape[:2]
            x0, y0, x1, y1 = self.roi
            r = self.model.predict(frame, imgsz=320, conf=self.yolo_conf, classes=[0], verbose=False)[0]
            for box in r.boxes:
                bx0, by0, bx1, by1 = box.xyxy[0].tolist()
                cx, cy = (bx0 + bx1) / 2 / w, (by0 + by1) / 2 / h
                if x0 <= cx <= x1 and y0 <= cy <= y1:
                    result["yolo"] = max(result["yolo"], round(float(box.conf), 2))
        result["feet"] = changed > self.change_area or result["yolo"] > 0
        if not result["feet"]:                             # follow slow light changes (sunrise)
            self.baseline = 0.95 * self.baseline + 0.05 * floor
        return result


class FakeFeet:
    """Stands in for the camera: type f + Enter to put your 'feet' on the floor or lift them."""

    def __init__(self) -> None:
        self.feet = False

    def toggle(self) -> None:
        self.feet = not self.feet
        print(f"  [fake] feet {'ON the floor' if self.feet else 'off the floor'}", flush=True)

    def take_baseline(self) -> float:
        return 100.0

    def look(self) -> dict:
        return {"feet": self.feet, "change": 1.0 if self.feet else 0.0, "yolo": 0.0, "bright": 100.0,
                "frame": None}


# --------------------------------------------------------------------------- trips

class TripTracker:
    """Turns a stream of feet / no-feet readings into trips.

    A trip starts when feet have been on the floor for min_trip seconds (shifting in bed
    or dangling a foot doesn't count) and ends after end_gap seconds without feet (one
    missed detection doesn't split a trip in two). 'Can't see' readings change nothing.
    """

    def __init__(self, min_trip: float, end_gap: float) -> None:
        self.min_trip, self.end_gap = min_trip, end_gap
        self.trips: list[dict] = []
        self.run_start: dt.datetime | None = None      # first sighting of the current run of feet
        self.last_feet: dt.datetime | None = None
        self.in_trip = False

    def update(self, t: dt.datetime, feet: bool | None) -> str | None:
        if feet is None:
            return None
        if feet:
            if self.run_start is None:
                self.run_start = t
            self.last_feet = t
            if not self.in_trip and (t - self.run_start).total_seconds() >= self.min_trip:
                self.in_trip = True
                return "trip_start"
        elif self.run_start is not None and (t - self.last_feet).total_seconds() >= self.end_gap:
            ended = None
            if self.in_trip:
                secs = max(1, round((self.last_feet - self.run_start).total_seconds()))
                self.trips.append({"start": self.run_start, "end": self.last_feet, "seconds": secs})
                ended = "trip_end"
            self.run_start, self.last_feet, self.in_trip = None, None, False
            return ended
        return None

    def feet_for(self, t: dt.datetime) -> float:
        """How long the current run of feet has lasted (0 if no feet right now)."""
        if self.run_start is None:
            return 0.0
        return (t - self.run_start).total_seconds()

    def feet_recently(self, t: dt.datetime, within: float) -> bool:
        return self.last_feet is not None and (t - self.last_feet).total_seconds() <= within


# --------------------------------------------------------------------------- the morning

def facts_text(trips: list[dict]) -> str:
    n = len(trips)
    if n == 0:
        return "0 trips\nquiet night"
    times = ", ".join(clock(t["start"]) for t in trips[:3]) + (" ..." if n > 3 else "")
    minutes = max(1, round(sum(t["seconds"] for t in trips) / 60))
    return f"{n} trip{'s' * (n != 1)}\n{times}\n{minutes} min on my floor"


NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]


def template_line(trips: list[dict]) -> str:
    """What the monster says if Qwen is missing, slow, or gets the facts wrong."""
    n = len(trips)
    if n == 0:
        return "You never left the bed. I slept like a baby. A scary baby."
    first = short_clock(trips[0]["start"])
    if n == 1:
        return f"One trip, at {first}. I opened one eye. Don't make me open both. Grrr."
    word = NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else str(n)
    return f"{word.capitalize()} trips last night, starting at {first}. My floor is not a hallway. Grrr!"


def check_line(line: str, trips: list[dict]) -> bool:
    """Qwen only phrases; code checks. The line must state the right number of trips and
    may not mention any time that isn't a real trip time (Part D: it invents things)."""
    n = len(trips)
    low = line.lower()
    word = NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else str(n)
    extra = {1: "|once", 2: "|twice"}.get(n, "")
    has_count = bool(re.search(rf"\b({n}|{word}{extra})\b", low)) or (n == 0 and re.search(r"\b(no|never|zero|not once)\b", low))
    if not has_count:
        return False
    allowed = {short_clock(t["start"]) for t in trips} | {short_clock(t["end"]) for t in trips}
    for found in re.findall(r"\b\d{1,2}:\d{2}\b", line):
        if found.lstrip("0") not in allowed:
            return False
    for other in range(0, 11):                      # a different trip count anywhere is also wrong
        if other != n and re.search(rf"\b{NUMBER_WORDS[other]} trips?\b|\b{other} trips?\b", low):
            return False
    return True


def ask_qwen(trips: list[dict], level: int, llm: str, timeout: float) -> tuple[str, str]:
    """Returns (line, source) where source is 'qwen' or 'template'."""
    n = len(trips)
    times = ", ".join(short_clock(t["start"]) for t in trips) or "none"
    minutes = round(sum(t["seconds"] for t in trips) / 60)
    prompt = f"""You are a grumpy little monster who lives under a bed and watches the floor at night.
The person just woke up. These are the ONLY facts you know about last night:
- times they got out of bed: {n}
- when: {times}
- minutes their feet were on your floor: {minutes}
- your mood: {screens.LEVEL_NAMES[level]}

Say one or two short sentences to them in a grumpy monster voice.
You must say the number {n}. Do not mention any time that is not listed. No emojis, no quotes."""
    try:
        import requests
        r = requests.post("http://localhost:11434/api/generate", json={
            "model": llm, "prompt": prompt, "think": False, "stream": False,
            "options": {"temperature": 0.7, "num_predict": 60},
        }, timeout=timeout)
        r.raise_for_status()
        line = r.json()["response"].strip().strip('"').replace("*", "")
        line = " ".join(line.split())
        if line and check_line(line, trips):
            return line, "qwen"
        print(f"  [qwen line rejected by the fact check] {line!r}", flush=True)
    except Exception as e:
        print(f"  [qwen unavailable: {e}]", flush=True)
    return template_line(trips), "template"


# --------------------------------------------------------------------------- the monster

class Monster:
    def __init__(self, args) -> None:
        self.args = args
        self.events: queue.Queue = queue.Queue()
        self.speaking = threading.Event()
        self.screen = Screen(enabled=not args.no_screen, window=args.window)
        self.voice = Voice(Path(args.voice), enabled=not args.no_voice, speaking=self.speaking)
        Buttons(self.events, enabled=not args.no_screen)
        Ears(self.events, self.speaking, Path(args.vad), args.whisper, enabled=not args.no_ears)
        threading.Thread(target=keyboard, args=(self.events,), daemon=True).start()
        if args.fake_feet:
            self.detector = FakeFeet()
        else:
            roi = tuple(float(v) for v in args.roi.split(","))
            self.detector = FeetDetector(args.camera, roi, args.change_area, args.pixel_diff,
                                         args.dark, not args.no_yolo, args.yolo_conf)
        self.log = open(HERE / args.log, "a")
        Path(HERE / "snaps").mkdir(exist_ok=True)
        self.state = "idle"

    # ---- logging
    def write(self, entry: dict) -> None:
        entry = {"t": now().isoformat(timespec="seconds"), **entry}
        self.log.write(json.dumps(entry) + "\n")
        self.log.flush()

    def last_night(self) -> list[dict]:
        path = HERE / "nights.jsonl"
        if not path.exists():
            return []
        lines = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        return lines[-1:] if lines else []

    # ---- the three moments
    def bedtime(self) -> None:
        """Part G: 'I'm going to sleep' -> 'Okay, one minute!' -> countdown -> watch."""
        self.screen.light(True)
        prev = self.last_night()
        note = ""
        if prev:
            n = prev[0]["trips"]
            note = f"last night: {n} trip{'s' * (n != 1)}"
        wait = "one minute" if self.args.countdown >= 60 else f"{int(self.args.countdown)} seconds"
        self.voice.say(f"Okay, {wait}! Get in bed and keep your feet up.")
        self.write({"event": "bedtime"})
        end = time.time() + self.args.countdown
        while time.time() < end:
            left = int(end - time.time()) + 1
            self.screen.show(screens.countdown(left, note))
            if self._cancel_requested():
                return
            self.screen.wait(0.25)
        bright = self.detector.take_baseline()           # the empty floor, slippers and all
        self.write({"event": "watching", "floor_brightness": round(bright, 1)})
        if bright < self.args.dark:
            print("[warn] the floor is too dark for the camera; turn on the light under the bed", flush=True)
        self.voice.say("I'm watching.", volume=0.5)
        self.watch()

    def _cancel_requested(self) -> bool:
        try:
            cmd, _ = self.events.get_nowait()
        except queue.Empty:
            return False
        if cmd == "fake_feet" and isinstance(self.detector, FakeFeet):
            self.detector.toggle()
        if cmd == "quit":
            raise KeyboardInterrupt
        if cmd == "awake":                                # changed your mind during the countdown
            self.voice.say("Fine. Never mind.")
            self.write({"event": "cancelled"})
            self.screen.show(screens.idle())
            self.screen.light(False)
            return True
        return False

    def watch(self) -> None:
        """Part H: look every few seconds, track trips, react on screen, quietly."""
        a = self.args
        tracker = TripTracker(a.min_trip, a.end_gap)
        last_reading, last_look, last_beat = None, 0.0, time.time()
        awake_until = None            # "I'm awake" heard, waiting for feet to confirm
        feet_now = False
        wake_time = None
        if a.wake:
            h, m = (int(x) for x in a.wake.split(":"))
            wake_time = (h, m)

        while True:
            # ---- commands
            self.screen.pump()
            try:
                cmd, source = self.events.get(timeout=0.1)
            except queue.Empty:
                cmd, source = None, None
            if cmd == "quit":
                raise KeyboardInterrupt
            if cmd == "fake_feet" and isinstance(self.detector, FakeFeet):
                self.detector.toggle()
                last_look = 0                               # look right away
            if cmd == "awake":
                self.write({"event": "heard_awake", "source": source})
                awake_until = time.time() + 60
                last_look = 0

            # ---- look at the floor
            if time.time() - last_look >= a.interval:
                last_look = time.time()
                t = now()
                try:
                    r = self.detector.look()
                except Exception as e:
                    print("hiccup:", e, flush=True)
                    continue
                feet_now = bool(r["feet"])
                reading = "can't see" if r["feet"] is None else ("feet" if r["feet"] else "no feet")
                if reading != last_reading:
                    self.write({"reading": reading, "change": r["change"], "yolo": r["yolo"], "bright": r["bright"]})
                    print(f"{t:%H:%M:%S} {reading}  (change {r['change']:.3f}, yolo {r['yolo']:.2f}, "
                          f"bright {r['bright']:.0f})", flush=True)
                    last_reading = reading
                if r.get("relit"):
                    self.write({"event": "light_changed"})
                event = tracker.update(t, r["feet"])
                if event == "trip_start":
                    self.write({"event": "trip_start", "since": tracker.run_start.isoformat(timespec="seconds")})
                    if a.snaps and r["frame"] is not None:
                        import cv2
                        cv2.imwrite(str(HERE / "snaps" / f"trip-{t:%Y%m%d-%H%M%S}.jpg"), r["frame"])
                    # show the new face first, then make the noise
                    count = len(tracker.trips) + 1
                    self.screen.show(screens.night(min(count, 3), True, count))
                    past_wake = wake_time is not None and (t.hour, t.minute) >= wake_time and t.hour < 12
                    if not a.silent and not past_wake:          # no growl for getting up in the morning
                        self.voice.trip_sound(count, a.night_volume)
                        self.write({"event": "trip_sound", "trip": count})
                elif event == "trip_end":
                    trip = tracker.trips[-1]
                    self.write({"event": "trip_end", "start": trip["start"].isoformat(timespec="seconds"),
                                "seconds": trip["seconds"], "trips_so_far": len(tracker.trips),
                                "anger": anger_level(tracker.trips)})
                    print(f"  trip {len(tracker.trips)}: {clock(trip['start'])}, {trip['seconds']} s", flush=True)

                # ---- is it morning?
                t = now()
                morning = False
                if awake_until is not None:
                    if feet_now or tracker.feet_recently(t, 30):
                        morning = True
                        self.write({"event": "awake_confirmed", "by": "voice + feet"})
                    elif time.time() > awake_until:
                        self.voice.say("I didn't see your feet. Go back to sleep.", volume=0.5)
                        awake_until = None
                    elif cmd == "awake":
                        self.voice.say("Prove it. Put your feet on the floor.", volume=0.6)
                if (not morning and wake_time and (t.hour, t.minute) >= wake_time and t.hour < 12
                        and tracker.feet_for(t) >= a.auto_morning):
                    morning = True
                    self.write({"event": "awake_confirmed", "by": f"feet for {a.auto_morning:.0f} s after {a.wake}"})
                if morning:
                    # the walk that ends the night is the wake-up, not a trip
                    if tracker.in_trip:
                        self.write({"event": "trip_dropped", "why": "this was getting up for the day"})
                    self.morning(tracker.trips)
                    return

                # ---- the monster reacts (screen only: no noise at night)
                if r["feet"] is None:
                    self.screen.show(screens.dark())
                else:
                    # the trip in progress counts: on your 1st trip one eye opens as soon as it counts
                    count = len(tracker.trips) + (1 if tracker.in_trip else 0)
                    self.screen.show(screens.night(min(count, 3), feet_now, count))

            if time.time() - last_beat > 600:
                self.write({"alive": True})
                last_beat = time.time()

    def morning(self, trips: list[dict]) -> None:
        """Part I: the computed facts on screen at once, then the monster's line out loud, then fade."""
        level = anger_level(trips)
        facts = facts_text(trips)
        self.screen.light(True)
        self.screen.show(screens.thinking(level, facts))
        print("\n" + facts.replace("\n", " | "), flush=True)
        t0 = time.time()
        line, source = ask_qwen(trips, level, self.args.model, self.args.qwen_timeout)
        took = time.time() - t0
        self.screen.show(screens.morning(level, facts, line))
        self.voice.say(line)
        summary = {
            "night": now().date().isoformat(), "trips": len(trips), "anger": screens.LEVEL_NAMES[level],
            "times": [clock(t["start"]) for t in trips], "seconds": [t["seconds"] for t in trips],
            "line": line, "line_source": source, "qwen_seconds": round(took, 1),
        }
        self.write({"event": "morning", **summary})
        with open(HERE / "nights.jsonl", "a") as f:
            f.write(json.dumps(summary) + "\n")
        (HERE / "morning_report.txt").write_text(f"{facts}\n\n{line}\n")
        print(f"[{source}, {took:.1f} s]\n", flush=True)
        self.screen.wait(self.args.show_for)
        for b in (0.8, 0.6, 0.4, 0.25, 0.12, 0.05):       # fade out until bedtime
            self.screen.show(screens.morning(level, facts, line, brightness=b))
            self.screen.wait(self.args.fade / 6)
        self.screen.show(screens.idle())
        self.screen.light(False)

    # ---- daytime
    def run(self) -> None:
        self.screen.show(screens.idle())
        self.screen.light(False)
        print("monster ready. Say \"I'm going to sleep\" (or type s + Enter). q + Enter quits.", flush=True)
        while True:
            self.screen.pump()
            try:
                cmd, source = self.events.get(timeout=0.1)
            except queue.Empty:
                continue
            if cmd == "quit":
                return
            if cmd == "fake_feet" and isinstance(self.detector, FakeFeet):
                self.detector.toggle()
            if cmd == "sleep":
                print(f"[{source}] going to sleep", flush=True)
                self.bedtime()
                print("monster ready for tonight.", flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--demo", action="store_true",
                   help="short timings: 10 s countdown, look every 1 s, trips after 3 s")
    p.add_argument("--countdown", type=float, default=60, help="seconds to get into bed")
    p.add_argument("--interval", type=float, default=5, help="seconds between looks")
    p.add_argument("--min-trip", type=float, default=15, help="seconds of feet before it counts as a trip")
    p.add_argument("--end-gap", type=float, default=20, help="seconds without feet before a trip ends")
    p.add_argument("--wake", help="HH:MM: after this, feet on the floor for --auto-morning seconds = morning")
    p.add_argument("--auto-morning", type=float, default=120)
    p.add_argument("--show-for", type=float, default=30, help="seconds to show the verdict before fading")
    p.add_argument("--fade", type=float, default=6, help="seconds the fade-out takes")
    # sensor
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--roi", default="0,0.2,1,1", help="floor region x0,y0,x1,y1 as fractions of the frame")
    p.add_argument("--change-area", type=float, default=0.04, help="fraction of the floor that must change")
    p.add_argument("--pixel-diff", type=int, default=25, help="how different a pixel must be to count as changed")
    p.add_argument("--dark", type=float, default=15, help="floor brightness below this = can't see")
    p.add_argument("--yolo-conf", type=float, default=0.25)
    p.add_argument("--no-yolo", action="store_true", help="floor change only")
    p.add_argument("--fake-feet", action="store_true", help="no camera: type f + Enter to toggle feet")
    p.add_argument("--no-snaps", dest="snaps", action="store_false", help="don't save a photo per trip")
    # voice, screen, model
    p.add_argument("--no-ears", action="store_true", help="no microphone: keyboard/buttons only")
    p.add_argument("--no-voice", action="store_true", help="print instead of speaking")
    p.add_argument("--night-volume", type=float, default=0.6, help="volume of the trip sounds (0-1)")
    p.add_argument("--silent", action="store_true", help="no trip sounds at night (screen only)")
    p.add_argument("--no-screen", action="store_true")
    p.add_argument("--window", action="store_true", help="also show the screen in a window (VNC)")
    p.add_argument("--whisper", default="tiny.en")
    p.add_argument("--vad", default=str(LAB3 / "models" / "silero_vad.onnx"))
    p.add_argument("--voice", default=str(LAB3 / "voices" / "en_US-lessac-medium.onnx"))
    p.add_argument("--model", default="qwen3.5:0.8b")
    p.add_argument("--qwen-timeout", type=float, default=90)
    p.add_argument("--log", default="night_log.jsonl")
    args = p.parse_args()
    if args.demo:
        args.countdown, args.interval, args.min_trip, args.end_gap = 10, 1, 3, 4
        args.show_for, args.auto_morning = 15, 20
    try:
        Monster(args).run()
    except KeyboardInterrupt:
        pass
    print("bye.")


if __name__ == "__main__":
    main()
