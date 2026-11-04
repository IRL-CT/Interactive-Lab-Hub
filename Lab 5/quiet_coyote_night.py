#!/usr/bin/env python3
"""
The whole bedtime story in one command: quiet coyote hands the night over, night_watch
takes it from there - and quiet coyote again, in the morning, hands it back.

    python quiet_coyote_night.py                        # ask for a bedtime, then hand over
    python quiet_coyote_night.py --at 22:45             # music starts 15 min before 22:45
    python quiet_coyote_night.py --at now               # rehearse right now
    python quiet_coyote_night.py --mouth-check          # is the camera seeing a face at all?
    python quiet_coyote_night.py --camera-rotation 0    # camera not mounted upside down?
    python quiet_coyote_night.py --led-test             # does the button LED pulse?
    python quiet_coyote_night.py --at now --skip-gesture --skip-night   # only phase 1 wiring
    python quiet_coyote_night.py --at now --night-duration 60 \
        --session rehearsal                            # a one-minute fake night

    # a real night, detached (this Pi has no tmux installed - see AGENTS.md);
    # --no-night-preview there: sampling only, no window and no camera stream all night
    nohup python3 quiet_coyote_night.py --at 22:45 --no-night-preview \
        >> logs/goodnight.log 2>&1 &

Two phases, one reason to be one file
-------------------------------------
Phase 1 (quiet_coyote_p1.py): the room is ours - "Peaceful_Mind.wav" plays softly, the
camera watches the hand, and the user ends the day by *doing* something rather than by
tapping a menu: hold the quiet-coyote gesture for --hold seconds. That gesture is the
consent. Then the music stops, a voice says good night, the button's red LED starts
pulsing, and the night is officially being recorded.

Phase 2 (night_watch.py): the snore listener and the mouth sampler log the night, and the
*same gesture ends it*. Show quiet coyote again for --morning-hold seconds and the night
stops: the LED goes out, the log is closed properly, and the device says "Good morning."

Session folders
---------------
Every run owns a folder, so two nights never mix:

    logs/2026-10-29_2245/
    ├── night_log.jsonl      # what morning.py reads
    ├── session.json         # settings, argv, and why the night ended
    └── snores/              # WAV clips, only when the microphone triggered

The name is the time the run started (--session NAME overrides it, --log/--dir override
the two paths inside it, --log-root moves the parent). The morning read is then
`python3 morning.py --log logs/2026-10-29_2245/night_log.jsonl`.

How phase 2 is run, and why it changed
--------------------------------------
night_watch used to run as a child process, which was tidier for isolation - but the
morning gesture has to look at the camera, and a camera has exactly one owner. A second
process would find /dev/video0 busy, and stopping/restarting night_watch every few seconds
to peek would drop the audio, the one signal that cannot be interrupted. So night_watch's
loop, log, panel and snore engine now run *in this process*, unmodified, and only its
camera thread class is subclassed (BedtimeMouthSampler) to add the hand question. The
camera still has one owner, the log still has one writer, and the three things that decide
a night (SnoreMachine, NightLog, MouthSampler) are still night_watch's own code.

The voice (Piper, now installed in this venv)
--------------------------------------------
`uv pip install piper-tts` was needed for a natural cue; the neural voice
`en_US-lessac-medium` is downloaded once into voices/ (63 MB) and synthesised into
goodnight.wav / goodmorning.wav / goodmorning_analysis.wav at 22050 Hz, about 1.5x real
time on this Pi 5 - so every cue is made before the music starts, never at the gesture.
Each WAV has a .json sidecar recording the text/voice/pace that produced it: change any
of them (or install Piper after the fact, as here) and the cue is rebuilt instead of
replaying the old eSpeak robot. eSpeak stays as the fallback, and a tone is the last
resort, so a cue is never silent.

Three cues, one of them about waiting: the good night at the hand-over, the good morning
that ends the night, and then - as `sleep_report.py` starts - "Good morning, I am
analyzing your sleep log last night, should take about 90 seconds". The report is not
instant (score, then Qwen, then Piper on a Pi 5), and a minute and a half of silence after
"Good morning" is indistinguishable from a crash. The cue therefore plays *before* the
report runs, and only when a report will actually run (`--no-report` skips it): announcing
an analysis that never happens would be its own kind of lie.

What each fix taught us (do not re-break these)
-----------------------------------------------
* **LED.** Three things were wrong at once: the qwiic_button library was not installed,
  the address was assumed to be 0x6B while sparkfun-qwiic-button 2.x defaults to 0x6F,
  and `LED_config(brightness, 3000, 0, 1)` asks for a cycle with *no off time* and a
  single brightness step - a steady light, not a pulse. Worse, `LED_on(brightness)`
  writes cycle_time = 0 and cancels the pulse again (and the old call passed no argument,
  so it raised and the error was swallowed). The fix: probe the address (given address,
  library default, then a full bus scan comparing the DEV_ID register), then write one
  heartbeat. The current version goes further: the lamp *breathes* - 4 s in, 6 s out,
  a cosine envelope written over I2C ten times a second, ~6 breaths a minute, which is
  the slow end of the range breathing exercises use to settle someone down. The
  firmware's own heartbeat is not used for that: it ramps between two values on a fixed
  schedule with an edge at each end, and a light next to a bed should not blink at you.
  `--led-test 10` breathes for ten seconds without running a whole workflow, and
  `--led-breath-in/--led-breath-out` change the rhythm.
* **Camera windows stay open.** The night shift's window is on by default now, because
  the only way to tell a shut mouth from a camera pointed at the wrong thing is to look
  at it. `--no-night-preview` restores sampling-only for a real night.
* **A log full of "mouth_closed".** `--mouth-check 10` prints live MAR with the lip
  markers on screen before any night runs: on this setup closed reads ~0.0-0.1 and open
  ~0.3-0.6, so a camera that never crosses 0.25 has a framing problem, not a threshold
  problem. Two other causes are fixed below: night_watch's median over three samples 10 s
  apart erased exactly the short open-mouth stretches (now `--smooth 1`), and a face that
  is half out of frame or under a blanket yields jitter (`user_leave`, then a tiny MAR) -
  which is why the log keeps `user_leave` distinct from a closed mouth.
* **The morning gesture needs its own rhythm.** The mouth is a minute-scale state (one
  sample per --cam-interval); a hand is a second-scale event. So the sampler reads a frame
  every 0.5 s and runs Hands on about one per second (~40 ms each on this Pi 5), while MAR
  stays on its slower schedule. The first --morning-grace seconds are ignored, so the
  bedtime gesture cannot leak through and end the night immediately; two seconds of hold
  is required, so a hand crossing the lens cannot either.
* **The camera hangs upside down.** The one on the shelf above the pillow is mounted
  rotated, so a raw frame shows an inverted room - and MediaPipe then reports a hand or a
  mouth that is not where it looks on screen. Every frame is therefore rotated 180 degrees
  at capture time (`upright()`), including the frames night_watch's own camera thread
  reads (it is handed an `_UprightCamera` proxy instead of the raw cap, so its sampling
  loop and its preview stream stay night_watch's code). `--camera-rotation 0` turns the
  flip off; the value used is written to session.json as `camera_rotation`.
* **The night's start and end** are written into the same JSONL as extra lines
  ("night watch started after quiet coyote", "quiet coyote at the camera - the night
  ended, good morning"), so the morning report knows which hours belong to this run, how
  it was ended, and can say so honestly.

The morning reveal (sleep_report.py)
-----------------------------------
Once the good-morning cue has played, the finished session folder is handed to
`sleep_report.py`: it computes the score and the percentages from the log (arithmetic,
no model), draws the four lines on the Mini PiTFT, and has Qwen write - and Piper speak -
a note grounded in this night's numbers. It runs as a child process because it takes the
panel from the boot screen, holds it for `--hold` seconds and gives it back, which is its
own job and not this process's. `--no-report` stops after the cue; `--report-args` passes
anything through, e.g. `--report-args "--hold 300 --no-speak"`. The report only runs when
the night ended with quiet coyote - a Ctrl-C rehearsal has no morning to reveal.

Privacy is unchanged from night_watch.py: no frame is ever saved, a frame is reduced to
one number (the mouth aspect ratio) and dropped, and nothing here is a diagnosis - at
most "possible snoring".

Keys: q in the bedtime or mouth-check window cancels. During the night, night_watch's own
keys apply (q quit, m save a clip, c look now); the hand ends the night properly.
"""
import argparse
import datetime
import importlib.util
import json
import math
import os
import pathlib
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")   # MediaPipe is chatty on stderr

import cv2

import handtrackmod as htm
import night_watch as nw          # phase 2 reuses its loop, log, panel and snore engine
from mouth_open import annotate, detect, mp_face_mesh, resolve_display

# ------------------------------------------------------------------------ settings

BASE_DIR = pathlib.Path(__file__).resolve().parent
MUSIC_FILE = BASE_DIR / "Peaceful_Mind.wav"
VOICE_FILE = BASE_DIR / "goodnight.wav"
VOICE_DIR = BASE_DIR / "voices"                # Piper voices live here once downloaded
VOICE_MODEL = "en_US-lessac-medium"
NIGHT_WATCH = BASE_DIR / "night_watch.py"
REPORT_SCRIPT = BASE_DIR / "sleep_report.py"    # the morning reveal (score + panel + note)
LOG_DIR = BASE_DIR / "logs"                    # every log and clip this workflow writes

CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_SETTLE_SECONDS = 1.0     # let V4L2 hand the camera over to the child process

# The camera is mounted hanging from the shelf above the pillow, so every frame arrives
# upside down. Rotating at the moment of capture (not in each consumer) keeps one truth:
# MediaPipe sees an upright hand, Face Mesh sees an upright mouth, and the preview window,
# the drawn text and the lip/hand markers all land where the user actually is. --camera-
# rotation 0 turns the flip off for a camera that is the right way up.
CAMERA_ROTATION = 180           # degrees to rotate each frame: 180 or 0

MUSIC_VOLUME = 50
MUSIC_LEAD_MINUTES = 15
GESTURE_HOLD_SECONDS = 0.5      # quiet_coyote_p1.py's value; --hold overrides it
GOODNIGHT_TEXT = "Okay, good night."
MORNING_TEXT = "Good morning."
MORNING_FILE = BASE_DIR / "goodmorning.wav"

# The morning report is not instant: sleep_report.py scores the log, then waits for Qwen
# and Piper. Silence for 90 s reads as a crash, so the wait is announced *before* it
# starts - the user hears that the device is working, how long it will take, and does not
# tap the button again. Prepared before the night like every other cue, for the same
# reason: synthesis takes seconds, and a cue that arrives after the fact is not a cue.
MORNING_ANALYSIS_TEXT = ("Good morning, I am analyzing your sleep log last night, "
                         "should take about 90 seconds")
MORNING_ANALYSIS_FILE = BASE_DIR / "goodmorning_analysis.wav"

# Quiet coyote again, in the morning: the same hand that handed the night over ends it.
# The camera is read every 0.5 s (cheap) and the hand detector runs on one of those
# frames per second (Hands costs ~40 ms on this Pi 5), so a two second hold is seen
# within about a second - long enough not to fire on a hand that merely crosses the
# lens, short enough for a half-asleep person.
MORNING_HOLD_SECONDS = 2.0
MORNING_GRACE_SECONDS = 15.0    # ignore the hand that just finished the bedtime gesture
HAND_INTERVAL = 1.0             # seconds between hand-detector runs
HAND_TICK = 0.5                 # seconds between camera reads in sampling mode

# The lamp breathes: 4 s in, 6 s out, one breath every 10 s - the slow end of the
# range breathing exercises use to settle someone down (~6 breaths a minute), which is
# the point of a light next to a bed. The envelope is computed here rather than left to
# the button's firmware "heartbeat": the firmware only ramps between two brightnesses on
# a fixed schedule, and the earlier attempt at it (cycle 3000 ms, off_time 0, one step)
# came out as a steady LED. A cosine in/out curve, written 10 times a second over I2C,
# costs nothing and is a breath instead of a blink. Inhale is shorter than exhale on
# purpose: that is the relaxing direction.
LED_BRIGHTNESS = 30             # of 255: dim enough to sleep next to, bright enough to see
LED_BREATH_IN = 4.0             # seconds to brighten
LED_BREATH_OUT = 6.0            # seconds to dim
LED_TICK = 0.1                  # seconds between brightness writes
LED_ADDRESS = None              # auto: library default, then a bus scan

GESTURE_WINDOW = "quiet coyote - hold to start the night"
MOUTH_WINDOW = "mouth check - point me at the pillow"

STOP = False                    # set by SIGTERM: the waiting phases have to notice too


def log(message):
    """print() with flush: every line still arrives when stdout is a nohup log."""
    print(message, flush=True)


def check_stop():
    """Turn a SIGTERM into the same path Ctrl-C takes.

    Without this, SIGTERM would only be forwarded to a child that does not exist yet and
    the script would happily keep sleeping until bedtime.
    """
    if STOP:
        raise KeyboardInterrupt


# --------------------------------------------------------------------------- audio

def start_music(path, volume):
    """Loop the bedtime music in the background, the way quiet_coyote_p1.py did."""
    return subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error",
         "-loop", "0", "-volume", str(volume), str(path)],
        stdin=subprocess.DEVNULL,
    )


def stop_process(process, grace=3.0):
    """Stop a player or a child politely, then firmly. Returns its exit code."""
    if process is None:
        return None
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    return process.returncode


def piper_model(voice, voice_dir):
    """Where a Piper voice's .onnx lives: voices/en_US-lessac-medium.onnx."""
    return pathlib.Path(voice_dir) / f"{voice}.onnx"


def ensure_piper_voice(voice, voice_dir):
    """Download the Piper voice once (~60 MB) and return its .onnx path, or None.

    piper-tts 1.8 takes a *model file*, not a voice name, so the model has to exist on
    disk. Fetching it here, before the music starts, keeps the download out of the
    gesture (the first evening costs ~10 s, every other evening costs nothing).
    """
    onnx = piper_model(voice, voice_dir)
    if onnx.is_file():
        return onnx
    if importlib.util.find_spec("piper") is None:
        return None
    log(f"     downloading the Piper voice {voice} into {voice_dir}/ (one time) ...")
    try:
        result = subprocess.run([sys.executable, "-m", "piper.download_voices", voice,
                                 "--data-dir", str(voice_dir)],
                                capture_output=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"     voice download failed: {exc}")
        return None
    if result.returncode == 0 and onnx.is_file():
        return onnx
    detail = (result.stderr or result.stdout or b"").decode(errors="replace").strip()
    log(f"     voice download failed: {detail.splitlines()[-1] if detail else 'no output'}")
    return None


def voice_commands(text, wav, voice=VOICE_MODEL, voice_dir=VOICE_DIR,
                   length_scale=1.05, text_file=None):
    """The synthesisers to try, best first: Piper, then eSpeak.

    Piper is the natural-sounding one (neural voice, ~1.5x real time on this Pi 5);
    eSpeak stays as the fallback so the cue is never missing, only uglier. The text goes
    through a file because piper-tts 1.8 has no positional-text argument.
    """
    onnx = piper_model(voice, voice_dir)
    commands = []
    if onnx.is_file():
        modern = [sys.executable, "-m", "piper", "-m", str(onnx), "-f", str(wav),
                  "--length-scale", str(length_scale), "--sentence-silence", "0.25"]
        if text_file is not None:
            modern += ["-i", str(text_file)]
        commands.append((modern, f"piper {voice}"))
        # piper-tts 1.2 style: voice name plus the text after `--`.
        commands.append(([sys.executable, "-m", "piper", "-m", voice,
                          "-f", str(wav), "--", text], f"piper {voice} (legacy)"))
    if shutil.which("piper") and onnx.is_file():
        commands.append((["piper", "-m", str(onnx), "-f", str(wav), "--", text],
                         "piper (binary)"))
    for exe in ("espeak-ng", "espeak"):
        if shutil.which(exe):
            commands.append(([exe, "-s", "150", "-w", str(wav), text], exe))
    return commands


def voice_stamp(text, voice, length_scale):
    """What the cached WAV was built from, so a better engine is not ignored forever.

    Without this the eSpeak WAV made before Piper was installed would be reused on every
    later evening - the exact reason the cue still sounded robotic after the upgrade.
    """
    return {"text": text, "voice": voice, "length_scale": round(length_scale, 3)}


def cached_voice(wav, stamp_path, stamp):
    """The cached cue, but only if it was made from the same text and voice."""
    wav, stamp_path = pathlib.Path(wav), pathlib.Path(stamp_path)
    if not wav.is_file() or wav.stat().st_size == 0:
        return None
    try:
        previous = json.loads(stamp_path.read_text())
    except (OSError, ValueError):
        return None                     # unknown provenance: synthesise again
    # Only compare the keys we asked about: the file also records which engine won.
    if {key: previous.get(key) for key in stamp} != stamp:
        return None
    return wav


def prepare_voice(text, wav, stamp_path=None, voice=VOICE_MODEL,
                  voice_dir=VOICE_DIR, length_scale=1.05, force=False):
    """Return a WAV holding the good-night cue, or None if nothing could say it.

    Synthesised before the music starts, never at the moment of the gesture: Piper on a
    Pi 5 takes seconds, and a cue that arrives five seconds after the hand is not a cue.
    The cache is keyed on text + voice + pace, so switching to Piper (or changing
    --cue-text) rebuilds it instead of replaying the old robot. Synthesis goes to a
    temporary file first, so a failed --revoice cannot destroy a good cue.
    """
    wav = pathlib.Path(wav)
    stamp_path = (pathlib.Path(stamp_path) if stamp_path
                  else wav.with_suffix(".json"))     # goodnight.wav <-> goodnight.json
    stamp = voice_stamp(text, voice, length_scale)
    hit = cached_voice(wav, stamp_path, stamp)
    if hit is not None and not force:
        return hit, f"cached {hit.name}"

    onnx = ensure_piper_voice(voice, voice_dir)
    if onnx is None:
        log("     piper voice unavailable; the cue will use eSpeak instead")

    tmp = wav.with_name(wav.stem + ".tmp" + wav.suffix)
    text_file = wav.with_name(wav.stem + ".tmp.txt")
    text_file.write_text(text + "\n", encoding="utf-8")
    try:
        for cmd, name in voice_commands(text, tmp, voice, voice_dir, length_scale,
                                        text_file):
            try:
                result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True,
                                        timeout=300)
            except (OSError, subprocess.TimeoutExpired) as exc:
                log(f"     {name} failed: {exc}")
                continue
            if result.returncode == 0 and tmp.is_file() and tmp.stat().st_size > 0:
                tmp.replace(wav)
                stamp["engine"] = name
                stamp_path.write_text(json.dumps(stamp, indent=2))
                return wav, name
            detail = (result.stderr or result.stdout or b"")\
                .decode(errors="replace").strip()
            log(f"     {name} failed: {detail.splitlines()[-1] if detail else 'no output'}")
    finally:
        tmp.unlink(missing_ok=True)     # a half-written file must not become the cue
        text_file.unlink(missing_ok=True)
    return None, "no synthesiser"


def play_cue(wav):
    """Say good night. Returns 'voice', 'beep' or 'silent'.

    The cue is the contract of phase 1 ("the device heard me"), so no speech synthesiser
    is not an excuse for silence: a short tone still tells the user the hand-over was
    accepted.
    """
    if wav is not None and pathlib.Path(wav).is_file():
        player = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", str(wav)],
            stdin=subprocess.DEVNULL)
        try:
            if player.wait() == 0:
                return "voice"
        finally:
            stop_process(player)
        log("     could not play the good-night file; falling back to a tone")

    tone = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error",
         "-f", "lavfi", "-i", "sine=frequency=660:duration=0.6"],
        stdin=subprocess.DEVNULL)
    try:
        return "beep" if tone.wait() == 0 else "silent"
    finally:
        stop_process(tone)


# ----------------------------------------------------------------------------- LED

class NightLamp:
    """The red LED on the Lab 4 Qwiic button: it breathes while the night runs.

    Three things were wrong before this class was rewritten, and all three made the LED
    look dead:

      * `qwiic_button` was not installed, so nothing happened at all;
      * the address was assumed to be 0x6B (the old firmware default), while
        sparkfun-qwiic-button 2.x ships with 0x6F - so the button was never found;
      * `LED_config(brightness, 3000, 0, 1)` asks the firmware for a 3000 ms cycle with
        *no* off time and a single brightness step, which is a steady light, not a pulse.
        `LED_on(brightness)` is worse: it writes cycle_time = 0, turning the pulse off
        again (and it needs an argument, which the old copy-pasted call did not pass).

    The breathing itself is computed here, not by the firmware: the button's "heartbeat"
    ramps between two values on a fixed schedule, and what this job wants is a body's
    rhythm - 4 s in, 6 s out, ~6 breaths a minute, brightness following a cosine so there
    is no edge anywhere. That is 10 one-byte I2C writes a second, and it is the difference
    between a light that blinks at you and one that breathes next to you.
    Still best-effort: no library or no button prints one warning with the addresses that
    were probed, and the night carries on.
    """

    def __init__(self, brightness=LED_BRIGHTNESS, breath_in=LED_BREATH_IN,
                 breath_out=LED_BREATH_OUT, address=None, enabled=True,
                 i2c_driver=None):
        self.brightness = brightness
        self.breath_in = max(0.5, breath_in)
        self.breath_out = max(0.5, breath_out)
        self.wanted_address = address
        self.enabled = enabled
        self.i2c_driver = i2c_driver     # a fake driver is how this is tested
        self.button = None
        self.address = None
        self.pulsing = False             # "the lamp is doing something"
        self.thread = None
        self.stop_flag = threading.Event()
        self.probed = []
        self.why_not = None if enabled else "disabled (--no-led)"
        if enabled:
            self._open()

    def _open(self):
        try:
            import qwiic_button                      # optional dependency
        except Exception as exc:
            self.why_not = f"qwiic_button not importable ({exc})"
            return
        try:
            button = qwiic_button.QwiicButton(i2c_driver=self.i2c_driver)
            found = self._find(button, qwiic_button.QwiicButton.DEV_ID)
        except Exception as exc:
            self.why_not = f"{type(exc).__name__}: {exc}"
            return
        if found is None:
            self.why_not = ("no Qwiic button answered on I2C-1 (looked at "
                            f"0x{button.address:02x} and scanned 0x08-0x77; "
                            "`i2cdetect -y 1` should show the button)")
            return
        self.button, self.address = found, found.address

    def _find(self, button, dev_id):
        """Return a QwiicButton bound to an address that really answers.

        The address depends on the firmware and on what a previous lab changed, so this
        checks the one we were given, then the library default, then walks the bus and
        compares the device-ID register. A wrong address is otherwise indistinguishable
        from an unplugged cable, which is exactly what made "the LED does not work" so
        hard to read.
        """
        candidates = []
        if self.wanted_address is not None:
            candidates.append(int(str(self.wanted_address), 0))
        if button.address not in candidates:
            candidates.append(button.address)
        candidates += [a for a in range(0x08, 0x78) if a not in candidates]

        for address in candidates:
            if address == 0x37:                  # reserved by the I2C spec
                continue
            try:
                if not button._i2c.isDeviceConnected(address):
                    continue
                self.probed.append(address)
                if button._i2c.readByte(address, button.ID) == dev_id:
                    button.address = address
                    return button
            except Exception:
                self.probed.append(address)
                continue
        return None

    def describe(self):
        """One line the log can keep: which button, which firmware, which rhythm."""
        if self.button is None:
            return self.why_not or "no LED"
        try:
            version = self.button.get_firmware_version()
            firmware = f"firmware {version >> 8}.{version & 0xFF}"
        except Exception:
            firmware = "firmware unknown"
        return (f"button 0x{self.address:02x} ({firmware}), breathing "
                f"{self.breath_in:g}s in / {self.breath_out:g}s out, peak "
                f"{self.brightness}/255")

    @property
    def active(self):
        return self.button is not None

    def level(self, elapsed):
        """Brightness 0..1 at a moment in the breath: cosine in, cosine out.

        Cosine rather than a straight ramp: a linear fade has corners at the top and
        bottom that the eye reads as a blink, while a cosine eases in and out the way a
        chest moves. Inhale 4 s, exhale 6 s - longer out than in is the calming direction.
        """
        cycle = self.breath_in + self.breath_out
        t = elapsed % cycle
        if t < self.breath_in:
            return 0.5 - 0.5 * math.cos(math.pi * t / self.breath_in)
        return 0.5 + 0.5 * math.cos(math.pi * (t - self.breath_in) / self.breath_out)

    def _set(self, value):
        """Write one brightness byte. The pulse stays at zero: we own the ramp now."""
        value = max(0, min(255, int(value)))
        if value == getattr(self, "_level", None):
            return
        self._level = value
        try:
            # LED_BRIGHTNESS register, straight - LED_config would rewrite four
            # registers ten times a second for the same effect.
            self.button._i2c.writeByte(self.address, self._led_reg, value)
        except Exception:
            try:
                self.button.LED_on(value)      # = LED_config(value, 0, 0, 1)
            except Exception:
                pass

    def start_breathing(self):
        """Begin breathing. Returns True when a real button is doing it."""
        if not self.enabled:
            log("red LED disabled (--no-led).")
            return False
        if self.button is None:
            log(f"warning: red LED unavailable: {self.why_not}")
            return False
        import qwiic_button
        self._led_reg = qwiic_button.QwiicButton.LED_BRIGHTNESS
        try:
            self.button.LED_config(0, 0, 0)     # steady mode: no firmware pulse on top
        except Exception as exc:
            self.why_not = f"LED_config failed ({exc})"
            log(f"warning: {self.why_not}")
            return False
        self.pulsing = True
        self._level = None
        self.stop_flag.clear()
        self.thread = threading.Thread(target=self._breathe, name="lamp-breath",
                                       daemon=True)
        self.thread.start()
        log(f"red LED breathing - {self.describe()}")
        return True

    def _breathe(self):
        started = time.monotonic()
        while not self.stop_flag.wait(LED_TICK):
            self._set(round(self.brightness * self.level(time.monotonic() - started)))

    # the old name, so --led-test and the night path read the same
    pulse = start_breathing

    def off(self):
        self.stop_flag.set()
        thread, self.thread = self.thread, None
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        self.pulsing = False
        if self.button is None:
            return
        try:
            self.button.LED_off()               # zeroes every LED register
        except Exception:
            pass


# ------------------------------------------------------------------------- gesture

def quiet_coyote_detected(landmarks):
    """The quiet-coyote test, copied from quiet_coyote_p1.py.

    Copied rather than imported on purpose: that file builds a QwiicButton at module
    level and raises when none answers, so importing it would make a missing button a
    hard failure here. The rules are unchanged - thumb tip (4) away from the index tip
    (8), index away from middle (12), middle and ring (16) close, ring away from pinky
    (20), thumb across to the ring finger - measured in pixels of the 640x480 frame,
    exactly as before.
    """
    if len(landmarks) < 21:
        return False

    points = {landmark[0]: (landmark[1], landmark[2]) for landmark in landmarks}
    required_ids = (4, 8, 12, 16, 20)
    if not all(index in points for index in required_ids):
        return False

    def distance(first, second):
        first_x, first_y = points[first]
        second_x, second_y = points[second]
        return math.hypot(second_x - first_x, second_y - first_y)

    return (
        distance(4, 8) > 100
        and distance(8, 12) > 100
        and distance(12, 16) < 100
        and distance(16, 20) > 100
        and distance(4, 16) < 100
    )


def upright(frame):
    """Turn a captured frame the right way up, per CAMERA_ROTATION.

    Called on every frame this file reads and, through _UprightCamera, on every frame
    night_watch's camera thread reads - so the gesture, the mouth measurement and the
    picture in the window all describe the same orientation.
    """
    if CAMERA_ROTATION == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    return frame


class _UprightCamera:
    """Proxy around cv2.VideoCapture whose read() returns upright frames.

    night_watch's MouthSampler owns its capture loop (two of them: sampling and preview)
    and reads `cap.read()` directly. Rather than copy those loops here - where they would
    drift apart from night_watch's - the subclass wraps the cap once, so both rhythms get
    the rotated picture for free and the grab()/release()/properties still reach the real
    device through __getattr__.
    """

    def __init__(self, cap):
        self._cap = cap

    def read(self):
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return ok, frame
        return True, upright(frame)

    def __getattr__(self, name):
        return getattr(self._cap, name)


def wait_for_quiet_coyote(camera_index, hold, preview, music_process=None):
    """Hold the camera open until quiet coyote is held long enough.

    Returns True when the user has handed the night over, False if they cancelled. The
    window (only with --gesture-preview) is drawn here, in the main thread: OpenCV's Qt
    backend silently refuses to map a window created from a worker thread, which is the
    trap AGENTS.md warns about - so this loop has no worker thread at all.

    The camera and the MediaPipe graph are closed in `finally`, because the child
    process is about to want the camera and the same model.
    """
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(
            "Could not open the camera. Check its connection and close other "
            "programs using it, or pass --camera INDEX."
        )

    detector = None
    started = None
    try:
        detector = htm.handDetector(detectionCon=0.7)

        while True:
            check_stop()
            if music_process is not None and music_process.poll() is not None:
                raise RuntimeError(
                    "Music playback stopped unexpectedly. Check the music file and "
                    "the audio output."
                )

            success, frame = cap.read()
            if not success or frame is None:
                raise RuntimeError("Could not read a frame from the camera.")
            frame = upright(frame)          # the camera hangs upside down

            frame = detector.findHands(frame, draw=preview)
            landmarks = detector.findPosition(frame, draw=False)
            pose = quiet_coyote_detected(landmarks)
            held = 0.0 if started is None else time.monotonic() - started

            if pose:
                if started is None:
                    started = time.monotonic()
                    log("quiet coyote detected - keep holding ...")
                if held >= hold:
                    log(f"quiet coyote held {held:.1f} s - the night is yours.")
                    return True
            elif started is not None:
                log("pose lost - show quiet coyote again.")
                started = None

            if preview:
                hint = (f"holding {held:.1f} / {hold:.1f} s" if started is not None
                        else "show quiet coyote")
                for text, y, colour in (
                        (hint, 28, (0, 255, 0) if started is not None else (60, 220, 255)),
                        ("q = cancel", CAMERA_HEIGHT - 14, (200, 200, 200))):
                    cv2.putText(frame, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                (0, 0, 0), 4, cv2.LINE_AA)
                    cv2.putText(frame, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                colour, 1, cv2.LINE_AA)
                cv2.imshow(GESTURE_WINDOW, frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    log("q pressed - the night was not handed over.")
                    return False
    finally:
        if detector is not None:
            try:
                detector.hands.close()   # free the model before the child builds one
            except Exception:
                pass
        cap.release()
        if preview:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass


def mouth_check(camera_index, seconds, threshold, preview):
    """Aimed at the pillow: does Face Mesh actually see a face, and does the mouth move?

    This exists because a log full of `mouth_closed 0.02` has three very different
    explanations and the numbers alone cannot tell them apart: the camera is pointed
    somewhere else, the face is half out of frame or under a blanket, or the mouth really
    is shut all night. Forty lines of live MAR plus the lip markers on the picture settle
    it in ten seconds, before a whole night is spent recording nothing.

    The guidance it prints is the one that matters: a closed mouth reads ~0.0-0.1 on
    this setup, an open one ~0.3-0.6, so if opening the mouth barely moves the number the
    camera needs to be closer / more frontal, not the threshold lowered.
    """
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"Could not open camera {camera_index} for the mouth check.")

    readings = []
    faces = 0
    frames = 0
    tty = sys.stdout.isatty()
    last_print = 0.0
    try:
        with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True,
                                   min_detection_confidence=0.5,
                                   min_tracking_confidence=0.5,
                                   static_image_mode=False) as face_mesh:
            log(f"mouth check: {seconds:.0f} s on camera {camera_index}. "
                f"Open and close your mouth a few times; q quits.")
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                success, frame = cap.read()
                if not success or frame is None:
                    raise RuntimeError("Could not read a frame from the camera.")
                frame = upright(frame)      # the camera hangs upside down
                frames += 1
                mar, landmarks = detect(frame, face_mesh)
                if mar is not None:
                    faces += 1
                    readings.append(mar)
                verdict = "no face" if mar is None else (
                    "open" if mar > threshold else "closed")
                num = "  --  " if mar is None else f"{mar:6.3f}"
                line = (f"{datetime.datetime.now():%H:%M:%S}  MAR {num}  {verdict:<6}  "
                        f"faces {faces}/{frames}")
                if tty:
                    print("\r" + line + "   ", end="", flush=True)
                elif time.monotonic() - last_print >= 2.0:
                    last_print = time.monotonic()
                    print(line, flush=True)
                if preview:
                    shown = annotate(frame, mar, landmarks, threshold,
                                     "mouth check")
                    cv2.imshow(MOUTH_WINDOW, shown)
                    if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                        break
                else:
                    time.sleep(0.2)          # Face Mesh does not need every frame
    finally:
        cap.release()
        if preview:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

    print(flush=True)
    if not readings:
        log(f"no face found in {frames} frames: the camera is pointed at the wrong "
            f"thing, or the room is too dark for Face Mesh.")
        return 1

    readings.sort()
    seen = len(readings)
    median = readings[seen // 2]
    log(f"face in {seen}/{frames} frames, MAR min {readings[0]:.3f} / median "
        f"{median:.3f} / max {readings[-1]:.3f}, threshold {threshold:.2f}")
    if readings[-1] < threshold:
        log("the mouth never crossed the threshold. If you did open it, move the camera "
            "closer to the pillow and look more head-on; only lower "
            "--mouth-threshold if a deliberately open mouth still reads low.")
    else:
        log("an open mouth was seen - the mouth numbers in the night log mean "
            "something. Keep this framing.")
    return 0


# ------------------------------------------------------------- the morning gesture

class MorningGesture:
    """The sleeper's "I am awake" signal: quiet coyote, once, for a couple of seconds.

    Kept apart from the nightly mouth sampling because it answers a different question at
    a different rhythm: the mouth is a minute-scale state read every --cam-interval, the
    hand is a second-scale gesture, so it is looked for about once a second on whatever
    frame the camera produced anyway. Two seconds of hold is required, so a hand that
    merely crosses the lens cannot end the night, and the first --morning-grace seconds
    are ignored so the bedtime gesture itself cannot fall through into this one.
    """

    def __init__(self, hold=MORNING_HOLD_SECONDS, grace=MORNING_GRACE_SECONDS,
                 enabled=True, on_hit=None):
        self.hold = hold
        self.grace = grace
        self.enabled = enabled
        self.on_hit = on_hit
        self.hit = threading.Event()        # read by the wrapper and by the panel poll
        self.at = None                      # wall clock, for the log line
        self.held_s = 0.0                   # how long it was actually held
        self.held_since = None
        self.detector = None
        self.error = None
        self.looks = 0
        self.started = time.monotonic()
        self._last_look = 0.0

    @property
    def active(self):
        return self.enabled and self.error is None

    def look(self, frame, draw=False):
        """Run the hand detector on one frame. Returns (pose_seen, held_seconds)."""
        if not self.active or self.hit.is_set():
            return False, 0.0
        now = time.monotonic()
        if now - self.started < self.grace or now - self._last_look < HAND_INTERVAL:
            return False, 0.0
        self._last_look = now
        try:
            if self.detector is None:
                self.detector = htm.handDetector(detectionCon=0.7)
            self.detector.findHands(frame, draw=draw)
            landmarks = self.detector.findPosition(frame, draw=False)
        except Exception as exc:           # a broken graph must not kill the night
            self.error = f"{type(exc).__name__}: {exc}"
            return False, 0.0
        self.looks += 1
        pose = quiet_coyote_detected(landmarks)
        if not pose:
            self.held_since = None
            if draw:
                self._write(frame, "morning: show quiet coyote to end the night",
                            (200, 200, 200))
            return False, 0.0
        if self.held_since is None:
            self.held_since = now
        held = now - self.held_since
        if draw:
            self._write(frame, f"morning: holding {held:.1f} / {self.hold:.1f} s",
                        (0, 255, 0))
        if held >= self.hold:
            self.at = time.time()           # wall clock: monotonic must not reach the log
            self.held_s = held
            self.hit.set()
            if not sys.stdout.isatty():
                # In a terminal night_watch's curses panel owns the screen; printing
                # there would scribble over it. The panel is about to close anyway.
                log(f"quiet coyote held {held:.1f} s - good morning.")
            if self.on_hit is not None:
                self.on_hit()
        return True, held

    @staticmethod
    def _write(frame, text, colour):
        """Draw on the preview frame; nothing is stored, the picture is only shown."""
        h = frame.shape[0]
        cv2.putText(frame, text, (12, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, text, (12, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    colour, 1, cv2.LINE_AA)

    def close(self):
        if self.detector is not None:
            try:
                self.detector.hands.close()
            except Exception:
                pass
            self.detector = None

    def summary(self):
        if not self.enabled:
            return "morning gesture disabled"
        if self.error:
            return f"morning gesture failed: {self.error}"
        if self.hit.is_set():
            return f"morning gesture: quiet coyote after {self.looks} looks"
        return f"morning gesture: never shown ({self.looks} looks)"


class BedtimeMouthSampler(nw.MouthSampler):
    """night_watch's camera thread, plus one extra question per frame: quiet coyote?

    The camera has exactly one owner, and that owner already has the frames, so this is
    the only place where the morning gesture can be seen without a second process trying
    to open /dev/video0 behind night_watch's back. Everything else - the MAR measurement,
    the sampling rhythm, the retry when the camera disappears - stays night_watch's.

    Two rhythms run on the one open camera: the mouth on night_watch's --cam-interval
    (a minute-scale state), the hand about once a second (a second-scale gesture). With
    the preview window open night_watch streams instead of sampling, and then every shown
    frame is also a chance to see the hand - which is why the gesture is easiest to watch
    in the window.
    """

    morning = None              # a MorningGesture, set before the night starts

    def _watch(self, cap):
        """night_watch's camera loop, on upright frames.

        The cap is wrapped rather than the two loops copied, so night_watch's sampling
        rhythm and its preview stream both keep working unchanged (see _UprightCamera).
        """
        super()._watch(_UprightCamera(cap))

    def _measure(self, frame, face_mesh):
        super()._measure(frame, face_mesh)
        if self.morning is not None:
            # draw=self.preview: in preview mode this frame *is* the picture, so the
            # hand and the hold progress appear in the window.
            self.morning.look(frame, draw=self.preview)

    def _sample(self, cap, face_mesh):
        """night_watch's 10 s mouth rhythm, with cheap hand looks in between."""
        next_mouth = time.monotonic()
        while not self.stop_flag.is_set():
            if self.wake.is_set():             # 'c' in the panel: look at the mouth now
                self.wake.clear()
                next_mouth = time.monotonic()
            if self.stop_flag.wait(HAND_TICK):
                return
            for _ in range(2):                 # the camera buffers a few stale frames
                cap.grab()
            ok, frame = cap.read()
            if not ok:
                return
            if time.monotonic() >= next_mouth:
                self._measure(frame, face_mesh)
                next_mouth = time.monotonic() + self.interval
            elif self.morning is not None:
                self.morning.look(frame)


# ------------------------------------------------------------------------ handoff

def iso(timestamp):
    """NightLog's timestamp shape, so both writers agree on the log format."""
    return datetime.datetime.fromtimestamp(timestamp).isoformat(timespec="seconds")


def append_log(log_path, entry):
    """Add one line to the JSONL morning.py reads. Never fatal.

    A full disk or a bad path must not cancel the night; the warning goes to the console
    and the measurement continues.
    """
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", buffering=1) as fp:
            fp.write(json.dumps(entry) + "\n")
        return True
    except OSError as exc:
        log(f"warning: could not write {log_path} ({exc})")
        return False


def write_session(session_dir, payload):
    """A small breadcrumb beside the JSONL: which run this folder is.

    night_log.jsonl answers "what happened"; this answers "with what settings, and why
    did it stop" - the question you ask a week later when the report reads oddly.
    """
    try:
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "session.json").write_text(json.dumps(payload, indent=2) + "\n")
        return True
    except OSError as exc:
        log(f"warning: could not write session.json ({exc})")
        return False


def run_sleep_report(log_path, extra_args=""):
    """Hand the finished night to sleep_report.py: score, Mini PiTFT panel, spoken note.

    A child process on purpose: it is a one-shot CLI that takes the display from the boot
    screen (systemctl stop/start piscreen), speaks through Piper and holds the panel for
    --hold seconds, and none of that belongs inside the process that just closed a night.
    """
    if not REPORT_SCRIPT.is_file():
        log(f"warning: sleep_report.py not found next to this script: {REPORT_SCRIPT}")
        return None
    cmd = [sys.executable, str(REPORT_SCRIPT), "--log", str(log_path)]
    cmd += shlex.split(extra_args or "")
    log("morning report: " + " ".join(shlex.quote(part) for part in cmd))
    try:
        return subprocess.run(cmd, cwd=str(BASE_DIR)).returncode
    except OSError as exc:
        log(f"warning: could not run sleep_report.py ({exc})")
        return None


def night_argv(args, log_path, clip_dir):
    """night_watch.py's arguments, built from this script's options."""
    argv = ["--log", str(log_path), "--dir", str(clip_dir),
            "--camera", str(args.camera),
            "--preview" if args.night_preview else "--no-preview",
            # Median over 1 sample: night_watch's default of 3 samples 10 s apart throws
            # away exactly the short open-mouth stretches that make a mouth event.
            "--smooth", str(args.smooth)]
    if args.no_camera:
        argv.append("--no-camera")
    if args.cam_interval is not None:
        argv += ["--cam-interval", str(args.cam_interval)]
    if args.mouth_threshold is not None:
        argv += ["--mouth-threshold", str(args.mouth_threshold)]
    if args.night_duration is not None:
        argv += ["--duration", str(args.night_duration)]
    argv += shlex.split(args.night_args or "")
    return argv


def run_night_shift(args, log_path, clip_dir, morning, lamp):
    """Run night_watch's night loop *in this process*, with a hand as the stop button.

    It used to be a child process, which was tidier for isolation - but the morning
    gesture has to look at the camera, and a camera has exactly one owner. A second
    process would find /dev/video0 busy, and stopping/restarting night_watch every few
    seconds to peek at the camera would drop the audio, which is the one signal that
    cannot be interrupted. So night_watch's loop, log, panel and snore engine run here
    unmodified, and only its camera thread class is subclassed (see
    BedtimeMouthSampler) to add the hand question.
    """
    argv = night_argv(args, log_path, clip_dir)
    log("handing over to night watch (in this process):")
    log("  night_watch.py " + " ".join(shlex.quote(part) for part in argv))

    saved_argv = sys.argv
    saved_sampler = nw.MouthSampler
    saved_handlers = {sig: signal.getsignal(sig)
                      for sig in (signal.SIGINT, signal.SIGTERM)}
    nw.stop = False                       # night_watch reads this global every loop
    BedtimeMouthSampler.morning = morning
    nw.MouthSampler = BedtimeMouthSampler
    sys.argv = [str(NIGHT_WATCH)] + argv
    try:
        return nw.main()
    except Exception as exc:              # never leave the lamp on and the log open
        log(f"error: night watch failed: {type(exc).__name__}: {exc}")
        return 2
    finally:
        sys.argv = saved_argv
        nw.MouthSampler = saved_sampler
        BedtimeMouthSampler.morning = None
        for sig, handler in saved_handlers.items():   # night_watch installed its own
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                pass


def forward_term(signum, frame):
    """kill -TERM must end the waiting phases instead of leaving us asleep until bedtime.

    During the night the handler is night_watch's own (it installs one when its loop
    starts) and that sets night_watch's stop flag, which closes the log properly.
    """
    global STOP
    STOP = True


# ------------------------------------------------------------------------- schedule

def wait_for_start(at, lead_minutes):
    """Sleep until music time, or start immediately.

    `--at now` - or no --at with no terminal attached, which is every nohup run - starts
    at once, because nobody will be there to type a bedtime.
    """
    if at is None:
        if not sys.stdin.isatty():
            log("no --at and no terminal to ask, so starting now.")
            return
        while True:
            answer = input("\nEnter bedtime in 24-hour time, such as 23:00.\n"
                           "Enter 'now' to start immediately: ").strip()
            if answer:
                at = answer
                break

    if at.strip().lower() == "now":
        log("Starting now.")
        return

    try:
        clock = datetime.datetime.strptime(at.strip(), "%H:%M").time()
    except ValueError:
        raise SystemExit(f"--at wants HH:MM or 'now', not {at!r}")

    now = datetime.datetime.now()
    bedtime = datetime.datetime.combine(now.date(), clock)
    if bedtime <= now:                  # a bedtime that has passed means tomorrow
        bedtime += datetime.timedelta(days=1)
    music_time = bedtime - datetime.timedelta(minutes=lead_minutes)

    log(f"pi time now:  {now:%Y-%m-%d %H:%M}")
    log(f"bedtime:      {bedtime:%Y-%m-%d %H:%M}")
    log(f"music starts: {music_time:%Y-%m-%d %H:%M}")
    if music_time <= now:
        log("that time has already passed, so the music starts now.")
        return

    log("waiting. Ctrl-C cancels.")
    while datetime.datetime.now() < music_time:
        check_stop()
        time.sleep(0.5)


# ----------------------------------------------------------------------------- main

def build_parser():
    """The command line, split into the two phases so --help reads like the workflow."""
    parser = argparse.ArgumentParser(
        description="Quiet-coyote hand-over, then a night of snore and mouth watching.")
    phase1 = parser.add_argument_group("phase 1 - the hand-over")
    phase1.add_argument("--at", metavar="HH:MM|now",
                        help="bedtime; music starts --lead minutes before it "
                             "(default: ask, or 'now' when there is no terminal)")
    phase1.add_argument("--lead", type=float, default=MUSIC_LEAD_MINUTES,
                        help="minutes of music before bedtime (default 15)")
    phase1.add_argument("--music", default=str(MUSIC_FILE), help="the bedtime track")
    phase1.add_argument("--volume", type=int, default=MUSIC_VOLUME,
                        help="ffplay volume, 0-100 (default 50)")
    phase1.add_argument("--hold", type=float, default=GESTURE_HOLD_SECONDS,
                        help="seconds quiet coyote must be held (default 0.5)")
    phase1.add_argument("--gesture-preview", dest="gesture_preview", default=None,
                        action="store_true",
                        help="show the bedtime camera (default: when an X display exists)")
    phase1.add_argument("--no-gesture-preview", dest="gesture_preview",
                        action="store_false", help="never open a window")
    phase1.add_argument("--skip-gesture", action="store_true",
                        help="no music, no hand: go straight to the night shift")
    phase1.add_argument("--cue-text", default=GOODNIGHT_TEXT,
                        help="what the device says once the hand-over is accepted")
    phase1.add_argument("--voice", default=str(VOICE_FILE),
                        help="cached speech file (default goodnight.wav)")
    phase1.add_argument("--voice-model", default=VOICE_MODEL,
                        help=f"Piper voice (default {VOICE_MODEL}); downloaded once into "
                             f"voices/")
    phase1.add_argument("--voice-dir", default=str(VOICE_DIR),
                        help="where Piper voices are kept (default voices/)")
    phase1.add_argument("--voice-pace", type=float, default=1.05,
                        help="Piper length scale: >1 is slower and calmer (default 1.05)")
    phase1.add_argument("--revoice", action="store_true",
                        help="re-synthesise the cue even if the cache matches")
    phase1.add_argument("--no-led", action="store_true", help="never touch the button LED")
    phase1.add_argument("--led-brightness", type=int, default=LED_BRIGHTNESS,
                        help=f"peak LED brightness, 0-255 (default {LED_BRIGHTNESS})")
    phase1.add_argument("--led-breath-in", type=float, default=LED_BREATH_IN,
                        help=f"seconds to brighten (default {LED_BREATH_IN:g})")
    phase1.add_argument("--led-breath-out", type=float, default=LED_BREATH_OUT,
                        help=f"seconds to dim; longer than in is the calming direction "
                             f"(default {LED_BREATH_OUT:g})")
    phase1.add_argument("--led-address", default=None, metavar="0xNN",
                        help="button I2C address (default: library default, then scan)")
    phase1.add_argument("--led-test", type=float, nargs="?", const=8.0, default=None,
                        metavar="SECONDS",
                        help="pulse the LED for N seconds (default 8) and quit: the "
                             "fastest way to check the wiring")
    phase1.add_argument("--mouth-check", type=float, nargs="?", const=10.0, default=None,
                        metavar="SECONDS",
                        help="watch the mouth for N seconds (default 10) and quit: is the "
                             "camera really seeing the face?")
    phase1.add_argument("--skip-night", action="store_true",
                        help="stop after the good-night cue (tests phase 1 only)")

    morning = parser.add_argument_group("morning - the same hand ends the night")
    morning.add_argument("--morning-gesture", dest="morning_gesture",
                         action="store_true", default=True,
                         help="quiet coyote at the camera ends the night and says good "
                              "morning (default)")
    morning.add_argument("--no-morning-gesture", dest="morning_gesture",
                         action="store_false",
                         help="only Ctrl-C ends the night")
    morning.add_argument("--morning-hold", type=float, default=MORNING_HOLD_SECONDS,
                         help="seconds quiet coyote must be held to end the night "
                              f"(default {MORNING_HOLD_SECONDS:g})")
    morning.add_argument("--morning-text", default=MORNING_TEXT,
                         help="what the device says when the night ends "
                              f"(default {MORNING_TEXT!r})")
    morning.add_argument("--morning-voice", default=str(MORNING_FILE),
                         help="cached speech file for the morning cue "
                              "(default goodmorning.wav)")
    morning.add_argument("--morning-analysis-text", default=MORNING_ANALYSIS_TEXT,
                         help="what it says while sleep_report.py works: the wait has to "
                              "be announced or it reads as a crash (default: "
                              f"{MORNING_ANALYSIS_TEXT!r})")
    morning.add_argument("--morning-analysis-voice",
                         default=str(MORNING_ANALYSIS_FILE),
                         help="cached speech file for the analysis cue "
                              "(default goodmorning_analysis.wav)")
    morning.add_argument("--report", dest="report", action="store_true", default=True,
                         help="after saying good morning, run sleep_report.py for the "
                              "score, the panel and the spoken note (default)")
    morning.add_argument("--no-report", dest="report", action="store_false",
                         help="stop after the good-morning cue")
    morning.add_argument("--report-args", default="",
                         help='extra sleep_report.py arguments, quoted, e.g. '
                              '"--hold 300 --no-speak"')

    phase2 = parser.add_argument_group("phase 2 - the night shift")
    phase2.add_argument("--camera", type=int, default=CAMERA_INDEX,
                        help="webcam index for both phases (default 0)")
    phase2.add_argument("--camera-rotation", type=int, choices=(0, 180),
                        default=CAMERA_ROTATION,
                        help="rotate every camera frame before it is measured: 180 when "
                             "the camera hangs upside down (default), 0 for a camera "
                             "that is the right way up")
    phase2.add_argument("--no-camera", action="store_true",
                        help="start night_watch.py audio-only")
    phase2.add_argument("--cam-interval", type=float,
                        help="seconds between mouth samples (night_watch default: 10)")
    phase2.add_argument("--mouth-threshold", type=float,
                        help="MAR above which the mouth counts as open (default 0.25)")
    phase2.add_argument("--smooth", type=int, default=1,
                        help="median over the last N camera samples (default 1: an open "
                             "mouth shorter than N x --cam-interval would be erased)")
    phase2.add_argument("--night-duration", type=float,
                        help="stop the night shift after N seconds (a rehearsal)")
    phase2.add_argument("--night-preview", dest="night_preview", action="store_true",
                        default=True,
                        help="keep night_watch.py's camera window open (default; use "
                             "--no-night-preview for the real night)")
    phase2.add_argument("--no-night-preview", dest="night_preview", action="store_false",
                        help="no night camera window: sampling only, less CPU and heat")
    phase2.add_argument("--night-args", default="",
                        help='extra night_watch.py arguments, quoted, e.g. "-v"')
    phase2.add_argument("--log", default=None,
                        help="JSONL log that morning.py reads "
                             "(default <session>/night_log.jsonl)")
    phase2.add_argument("--dir", default=None,
                        help="where snore WAV clips go (default <session>/snores/)")
    phase2.add_argument("--log-root", default=str(LOG_DIR),
                        help="folder that holds one sub-folder per night (default logs/)")
    phase2.add_argument("--session", default=None, metavar="NAME",
                        help="session folder name (default: the time the run started, "
                             "e.g. 2026-10-29_2245)")
    return parser


def main():
    global CAMERA_ROTATION
    args = build_parser().parse_args()
    CAMERA_ROTATION = args.camera_rotation     # upright() reads it on every frame

    signal.signal(signal.SIGTERM, forward_term)

    music = pathlib.Path(args.music)
    if not music.is_absolute():
        music = BASE_DIR / music
    voice_path = pathlib.Path(args.voice)
    if not voice_path.is_absolute():
        voice_path = BASE_DIR / voice_path
    morning_path = pathlib.Path(args.morning_voice)
    if not morning_path.is_absolute():
        morning_path = BASE_DIR / morning_path
    voice_dir = pathlib.Path(args.voice_dir)
    if not voice_dir.is_absolute():
        voice_dir = BASE_DIR / voice_dir
    # ---- one folder per night: logs/<when-the-run-started>/{night_log.jsonl,snores/}
    root = pathlib.Path(args.log_root)
    if not root.is_absolute():
        root = BASE_DIR / root
    session = args.session or datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    session_dir = (root / session).resolve()
    log_path = pathlib.Path(args.log).resolve() if args.log else session_dir / "night_log.jsonl"
    clip_dir = pathlib.Path(args.dir).resolve() if args.dir else session_dir / "snores"

    # ---- prerequisites, checked before waiting until bedtime
    if not args.skip_gesture:
        if not music.is_file():
            raise SystemExit(f"music file not found: {music}")
        if shutil.which("ffplay") is None:
            raise SystemExit("missing ffplay. Run: sudo apt install ffmpeg")
    if not args.skip_night and not NIGHT_WATCH.is_file():
        raise SystemExit(f"night_watch.py not found next to this script: {NIGHT_WATCH}")

    # ---- gesture window: only when asked for and possible
    display = resolve_display(None, no_window=args.gesture_preview is False)
    preview = display is not None and args.gesture_preview is not False
    if args.gesture_preview and not preview:
        log("no X display found, so the bedtime camera stays headless.")

    lamp = NightLamp(brightness=args.led_brightness, breath_in=args.led_breath_in,
                     breath_out=args.led_breath_out, address=args.led_address,
                     enabled=not args.no_led)

    # ---- quiet coyote again, in the morning: the hand is the stop button
    morning = MorningGesture(hold=args.morning_hold,
                             enabled=args.morning_gesture)

    def morning_signal():
        """Runs in night_watch's camera thread the moment the gesture completes."""
        lamp.off()          # the light goes out with the gesture, not a second later
        nw.stop = True      # night_watch's loop reads this global and closes its log

    morning.on_hit = morning_signal

    # ---- two one-shot checks, both before any music or waiting
    if args.led_test is not None:
        if lamp.pulse():
            log(f"pulsing for {args.led_test:.0f} s - look at the button.")
            time.sleep(args.led_test)
        else:
            log("no LED to test. Wiring: button -- Qwiic cable -- Pi 5 Qwiic port (I2C-1); "
                "`i2cdetect -y 1` should show 6f.")
        lamp.off()
        return 0 if lamp.active else 1

    if args.mouth_check is not None:
        try:
            return mouth_check(args.camera, args.mouth_check,
                               args.mouth_threshold or 0.25, preview)
        except RuntimeError as exc:
            log(f"error: {exc}")
            return 2

    music_process = None

    try:
        if args.skip_gesture:
            log("--skip-gesture: no music and no hand, going straight to night watch.")
            cue = "skipped"
        else:
            log(f"preparing the good-night cue ({args.cue_text!r}) ...")
            voice, how = prepare_voice(args.cue_text, voice_path,
                                       voice=args.voice_model, voice_dir=voice_dir,
                                       length_scale=args.voice_pace,
                                       force=args.revoice)
            if voice is None:
                log("     no speech synthesiser worked; the cue will be a tone")
            else:
                log(f"     cue ready from {how}: {voice.name}")

            wait_for_start(args.at, args.lead)

            music_process = start_music(music, args.volume)
            log(f"\nmusic is playing at volume {args.volume}.")
            if args.skip_night:
                log("show quiet coyote to stop it. Press Ctrl-C to quit.")
            else:
                log("show quiet coyote to stop the music and start the night.")
                log("(q in the window, or Ctrl-C, cancels.)")

            confirmed = wait_for_quiet_coyote(args.camera, args.hold, preview,
                                             music_process)
            code = stop_process(music_process)
            music_process = None
            log(f"music stopped (exit code {code}).")

            if not confirmed:
                log("the night was not handed over - nothing was recorded.")
                return 1

            cue = play_cue(voice)
            log(f"audio cue: good night ({cue}).")
            lamp.pulse()

            # The gesture loop has released the camera and closed its model; give V4L2 a
            # moment so the child does not find the device busy and run audio-only.
            time.sleep(CAMERA_SETTLE_SECONDS)

        if args.skip_night:
            log("--skip-night: stopping after phase 1.")
            return 0

        log(f"preparing the good-morning cue ({args.morning_text!r}) ...")
        morning_voice, morning_how = prepare_voice(
            args.morning_text, morning_path, voice=args.voice_model,
            voice_dir=voice_dir, length_scale=args.voice_pace, force=args.revoice)
        if morning_voice is None:
            log("     no speech synthesiser worked; the morning cue will be a tone")

        # The "this takes about 90 seconds" cue, made now rather than in the morning for
        # the same reason as the others. It is only ever played when a report will run,
        # because announcing an analysis that is not going to happen would be a lie.
        analysis_path = pathlib.Path(args.morning_analysis_voice)
        if not analysis_path.is_absolute():
            analysis_path = BASE_DIR / analysis_path
        analysis_voice = None
        if args.report:
            log(f"preparing the analysis cue ({args.morning_analysis_text!r}) ...")
            analysis_voice, analysis_how = prepare_voice(
                args.morning_analysis_text, analysis_path, voice=args.voice_model,
                voice_dir=voice_dir, length_scale=args.voice_pace,
                force=args.revoice)
            if analysis_voice is None:
                log("     no speech synthesiser worked; this cue will be a tone")

        if args.log is None or args.dir is None:
            log(f"session folder: {session_dir}")
        if log_path.exists():
            log(f"warning: {log_path} already has entries; this run appends to it "
                f"(use --session NAME for a fresh folder)")
        session_info = {
            "session": session,
            "started": iso(time.time()),
            "argv": sys.argv[1:],
            "log": str(log_path),
            "clips": str(clip_dir),
            "camera": args.camera,
            "camera_rotation": CAMERA_ROTATION,
            "no_camera": args.no_camera,
            "cam_interval": args.cam_interval,
            "mouth_threshold": args.mouth_threshold,
            "smooth": args.smooth,
            "night_preview": args.night_preview,
            "voice_model": args.voice_model,
            "morning_gesture_enabled": args.morning_gesture,
            "morning_hold": args.morning_hold,
            "led": lamp.describe(),
        }
        write_session(log_path.parent, session_info)

        append_log(log_path, {
            "t": iso(time.time()),
            "reading": "night watch started after quiet coyote",
            "event": "handoff", "cue": cue, "led": lamp.pulsing,
        })
        if args.no_camera and morning.enabled:
            log("warning: --no-camera, so no hand can be seen: only Ctrl-C ends the night.")

        rc = run_night_shift(args, log_path, clip_dir, morning, lamp)

        woke_up = morning.hit.is_set()
        if woke_up:
            append_log(log_path, {
                "t": iso(morning.at or time.time()),
                "reading": "quiet coyote at the camera - the night ended, good morning",
                "event": "morning", "held_s": round(morning.held_s, 1),
            })
        append_log(log_path, {
            "t": iso(time.time()),
            "reading": ("night watch stopped after quiet coyote (good morning)"
                        if woke_up else f"night watch stopped (exit {rc})"),
            "event": "handoff_end", "exit": rc, "morning": woke_up,
        })
        log(f"night watch finished with exit code {rc}; {morning.summary()}.")
        session_info.update({"ended": iso(time.time()), "exit": rc,
                             "morning_result": morning.summary()})
        write_session(log_path.parent, session_info)

        report_rc = None
        if woke_up:
            log(f"audio cue: {args.morning_text!r}")
            log(f"  played ({play_cue(morning_voice)}).")
            if args.report:
                # Announce the wait before the wait: sleep_report.py scores the log,
                # then waits for Qwen and Piper, and 90 s of silence sounds broken.
                log(f"audio cue: {args.morning_analysis_text!r}")
                log(f"  played ({play_cue(analysis_voice)}).")
                report_rc = run_sleep_report(log_path, args.report_args)
                log(f"morning report finished (exit {report_rc}).")
                session_info.update({"report_exit": report_rc})
                write_session(log_path.parent, session_info)
        log("the lamp is out. Read the night with:")
        log(f"  python3 morning.py --log {log_path}")
        return 0 if rc == 0 else rc

    except KeyboardInterrupt:
        log("\nStopped by user.")
        return 130
    except RuntimeError as exc:
        log(f"error: {exc}")
        return 2
    finally:
        stop_process(music_process)
        lamp.off()
        if preview:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
