#!/usr/bin/env python3
"""Lab 3 voice recorder starter. Put this file in the Lab 3 directory.

Run: python voice_camera.py
Keyboard-only check: python voice_camera.py --no-voice
Commands (type and Enter, or speak): start recording, pause recording,
resume recording, end recording, video library, up, down, play video, back,
help. Type quit to exit. Ctrl-C also saves the current session when possible.

Videos are SILENT. They are streamed to disk at 640x480 / 15 fps / H.264.
Menus and silent video playback use the ST7789 135x240 PiTFT directly over
SPI, including over SSH. GPIO23 = up, GPIO24 = down; either button stops
playback. Reset is None, as required to free GPIO24 on the Mini PiTFT.
The chip-select pin defaults to GPIO5 to match your working example.
Use --no-screen for terminal-only diagnosis; --cs-pin 8 selects CE0.

Speech uses the same packages/models as the lab, with one tiny.en model.
Listening pauses during recognition and spoken feedback (no barge-in).
Use --no-tts for screen/terminal-only feedback. No new Python packages.
Temporary segments survive errors under videos/.sessions for recovery.
Each session is limited to 300 wall-clock seconds including pauses, by
default. Low storage also stops the session; no existing videos are deleted.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import queue
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

LAB_DIR = Path(__file__).resolve().parent
ICON_BACKGROUND = "white"
HELP = ("Commands: start recording, pause recording, resume recording, "
        "end recording, video library, up, down, play video, back. "
        "Type quit to exit.")


def stop_process(proc):
    """Ask FFmpeg to finalize the container, then escalate only if stuck."""
    if proc.poll() is not None:
        return
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)


def valid_video(path):
    if not path.is_file() or path.stat().st_size == 0:
        return False
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=nb_frames", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=10)
    if result.returncode:
        return False
    streams = json.loads(result.stdout).get("streams", [])
    return bool(streams) and int(streams[0].get("nb_frames", "0")) > 0


class Recorder:
    def __init__(self, args):
        self.args = args
        self.root = args.videos.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.session = None
        self.proc = None
        self.log_handle = None
        self.current = None
        self.parts = []
        self.started = 0

    def check_space(self):
        if shutil.disk_usage(self.root).free < self.args.reserve_mb * 1024**2:
            raise RuntimeError("Low storage. Free some space before recording.")

    def start_segment(self):
        self.check_space()
        if self.session is None:
            stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            self.name = f"{stamp}_{uuid.uuid4().hex[:8]}"
            self.session = self.root / ".sessions" / self.name
            self.session.mkdir(parents=True)
            self.started = time.monotonic()
        self.current = self.session / f"part_{len(self.parts):03d}.mp4"
        log_path = self.session / f"part_{len(self.parts):03d}.log"
        # Test-source mode exercises the real encoder without webcam hardware.
        source = (["-re", "-f", "lavfi", "-i", "testsrc2=size=640x480:rate=30"]
                  if self.args.test_source else
                  ["-f", "v4l2", "-input_format", "mjpeg", "-video_size",
                   "640x480", "-framerate", "30", "-i", self.args.camera])
        remaining = max(1, self.args.max_seconds - (time.monotonic() - self.started))
        command = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-filter_threads", "1", "-n"]
        command += source + ["-t", str(remaining), "-an", "-vf", "fps=15",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf",
                             "28", "-threads", "2", "-pix_fmt", "yuv420p",
                             str(self.current)]
        self.log_handle = log_path.open("w")
        try:
            self.proc = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                         stdout=subprocess.DEVNULL,
                                         stderr=self.log_handle, start_new_session=True)
            time.sleep(0.25)
            if self.proc.poll() is not None:
                raise RuntimeError(f"Camera capture failed. See {log_path}")
        except Exception:
            self.log_handle.close()
            self.log_handle = None
            self.proc = None
            raise

    def stop_segment(self):
        if self.proc is None:
            return
        try:
            stop_process(self.proc)
        finally:
            if self.log_handle:
                self.log_handle.close()
            self.proc = None
            self.log_handle = None
        if not valid_video(self.current):
            raise RuntimeError(f"No usable frames. Segment/log retained in {self.session}")
        self.parts.append(self.current)

    def finish(self):
        self.stop_segment()
        if not self.parts:
            raise RuntimeError(f"No usable recording. Check {self.session}")
        final = self.root / f"{self.name}.mp4"
        if len(self.parts) == 1:
            shutil.copyfile(self.parts[0], self.session / "complete.mp4")
        else:
            listing = self.session / "concat.txt"
            listing.write_text("".join(f"file '{p.name}'\n" for p in self.parts))
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", "-f",
                 "concat", "-safe", "1", "-i", str(listing), "-c", "copy",
                 "-movflags", "+faststart", str(self.session / "complete.mp4")],
                capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise RuntimeError(f"Joining failed: {result.stderr[-500:]} "
                                   f"Segments retained in {self.session}")
        complete = self.session / "complete.mp4"
        if not valid_video(complete):
            raise RuntimeError(f"Saved file failed validation. Check {self.session}")
        if final.exists():
            raise RuntimeError(f"Destination already exists: {final}")
        complete.rename(final)
        shutil.rmtree(self.session)  # Only this newly generated session folder.
        self.session = None
        self.parts = []
        return final


class VideoPlayer:
    """FFmpeg decodes at real-time speed; keep only the most recent RGB frame."""
    def __init__(self, path, width, height, fps):
        self.frames = queue.Queue(maxsize=1)
        self.finished = threading.Event()
        self.closed = threading.Event()
        self.frame_bytes = width * height * 3
        self.error = None
        vf = (f"fps={fps},format=rgb24,scale={width}:{height}:force_original_aspect_ratio=decrease,"
              f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black")
        self.proc = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-filter_threads", "1", "-re", "-i", str(path),
             "-an", "-vf", vf, "-threads", "1", "-f", "rawvideo", "-pix_fmt",
             "rgb24", "pipe:1"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, start_new_session=True)
        threading.Thread(target=self.read_frames, daemon=True).start()

    def read_frames(self):
        try:
            while not self.closed.is_set():
                data = self.proc.stdout.read(self.frame_bytes)
                if len(data) != self.frame_bytes:
                    break
                try:
                    self.frames.put_nowait(data)
                except queue.Full:
                    try:
                        self.frames.get_nowait()
                    except queue.Empty:
                        pass
                    try:
                        self.frames.put_nowait(data)
                    except queue.Full:
                        pass
            code = self.proc.wait()
            if code and not self.closed.is_set():
                self.error = f"Video decode failed (FFmpeg exit {code})."
        finally:
            self.finished.set()

    def close(self):
        self.closed.set()
        stop_process(self.proc)
        self.finished.wait(timeout=3)
        self.proc.stdout.close()


class Screen:
    """Same Adafruit/Pillow display interface as the user's animation script."""
    def __init__(self, args):
        import board
        import digitalio
        from PIL import Image, ImageDraw, ImageFont
        import adafruit_rgb_display.st7789 as st7789

        self.Image, self.ImageDraw = Image, ImageDraw
        self.pins = []
        self.cs = digitalio.DigitalInOut(getattr(board, f"D{args.cs_pin}"))
        self.dc = digitalio.DigitalInOut(board.D25)
        self.pins.extend([self.cs, self.dc])
        self.disp = st7789.ST7789(board.SPI(), cs=self.cs, dc=self.dc, rst=None,
                                  baudrate=24000000, width=135, height=240,
                                  x_offset=53, y_offset=40, rotation=args.rotation)
        self.width, self.height = ((240, 135) if args.rotation % 180 else (135, 240))
        self.backlight = digitalio.DigitalInOut(board.D22)
        self.backlight.switch_to_output(value=True)
        self.pins.append(self.backlight)
        self.buttons = []
        for number in ((24, 23) if args.swap_buttons else (23, 24)):
            pin = digitalio.DigitalInOut(getattr(board, f"D{number}"))
            pin.switch_to_input(pull=digitalio.Pull.UP)
            self.pins.append(pin)
            self.buttons.append(pin)
        self.raw = [True, True]
        self.stable = [True, True]
        self.changed_at = [time.monotonic(), time.monotonic()]
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
            self.title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except OSError:
            self.font = self.title_font = ImageFont.load_default()
        self.last_view = None
        self.icons = {}

    def icon(self, name):
        """Load a LAB_DIR picture once, scaled to fit and centered on the PiTFT."""
        if name in self.icons:
            return self.icons[name]
        path = LAB_DIR / name
        image = None
        if path.is_file():
            try:
                with self.Image.open(path) as opened:
                    source = opened.convert("RGBA")
                scale = min(self.width / source.width, self.height / source.height)
                size = (max(1, round(source.width * scale)),
                        max(1, round(source.height * scale)))
                scaled = source.resize(size, self.Image.Resampling.LANCZOS)
                canvas = self.Image.new("RGB", (self.width, self.height), ICON_BACKGROUND)
                canvas.paste(scaled, ((self.width - size[0]) // 2,
                                      (self.height - size[1]) // 2), scaled)
                image = canvas
            except Exception as exc:
                print(f"Screen image {name} unusable: {exc}", flush=True)
        self.icons[name] = image
        return image

    def poll_buttons(self):
        now = time.monotonic()
        presses = []
        for i, button in enumerate(self.buttons):
            raw = button.value
            if raw != self.raw[i]:
                self.raw[i] = raw
                self.changed_at[i] = now
            if raw != self.stable[i] and now - self.changed_at[i] >= 0.04:
                self.stable[i] = raw
                if not raw:
                    presses.append("up" if i == 0 else "down")
        return presses

    def fit(self, draw, text, font, max_width):
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return text
        while text and draw.textbbox((0, 0), text + "...", font=font)[2] > max_width:
            text = text[:-1]
        return text + "..."

    def render(self, app):
        if app.mode == "playing" and app.player:
            try:
                frame = app.player.frames.get_nowait()
                self.disp.image(self.Image.frombytes("RGB", (self.width, self.height), frame))
            except queue.Empty:
                pass
            self.last_view = None
            return
        icon = self.icon(app.icon) if app.icon else None
        if icon is not None:
            self.disp.image(icon)
            self.last_view = None
            return
        elapsed = int(time.monotonic() - app.recorder.started) if app.recorder.session else 0
        view = (app.mode, app.voice_phase, app.message, elapsed,
                tuple(p.name for p in app.files), app.selected)
        if view == self.last_view:
            return
        image = self.Image.new("RGB", (self.width, self.height), "#101820")
        draw = self.ImageDraw.Draw(image)
        title = {"ready": "VOICE CAMERA", "recording": "RECORDING",
                 "paused": "PAUSED", "library": "VIDEO LIBRARY"}.get(app.mode, app.mode.upper())
        color = "#ff5555" if app.mode == "recording" else "#60d5ff"
        draw.text((5, 5), title, fill=color, font=self.title_font)
        draw.text((5, 26), self.fit(draw, app.voice_phase, self.font, self.width - 10),
                  fill="white", font=self.font)
        if app.mode == "library":
            if not app.files:
                draw.text((5, 51), "No videos yet", fill="white", font=self.font)
            rows = max(1, (self.height - 95) // 25)
            first = max(0, min(app.selected - rows // 2, len(app.files) - rows))
            for row, index in enumerate(range(first, min(first + rows, len(app.files)))):
                y = 48 + row * 25
                selected = index == app.selected
                if selected:
                    draw.rectangle((2, y, self.width - 3, y + 22), fill="#60d5ff")
                text = f"{index + 1}. {app.files[index].stem}"
                draw.text((5, y + 4), self.fit(draw, text, self.font, self.width - 10),
                          fill="#101820" if selected else "white", font=self.font)
            draw.text((5, self.height - 40), "Buttons: up / down", fill="white", font=self.font)
            draw.text((5, self.height - 24), 'Say "play video" or "back"', fill="white", font=self.font)
        else:
            if app.recorder.session:
                draw.text((5, 50), f"Session: {elapsed // 60:02d}:{elapsed % 60:02d}",
                          fill="white", font=self.font)
            words = app.message.split()
            lines, line = [], ""
            for word in words:
                candidate = (line + " " + word).strip()
                if draw.textbbox((0, 0), candidate, font=self.font)[2] > self.width - 10:
                    if line:
                        lines.append(line)
                    line = word
                else:
                    line = candidate
            if line:
                lines.append(line)
            for i, line in enumerate(lines[:max(1, (self.height - 106) // 16)]):
                draw.text((5, 74 + i * 16), self.fit(draw, line, self.font, self.width - 10),
                          fill="white", font=self.font)
            draw.text((5, self.height - 24), 'Say "help" for commands', fill="#60d5ff", font=self.font)
        self.disp.image(image)
        self.last_view = view

    def close(self):
        self.backlight.value = False
        for pin in reversed(self.pins):
            pin.deinit()


class Voice:
    def __init__(self, args, events, stopped):
        self.args, self.events, self.stopped = args, events, stopped
        self.enabled = threading.Event()
        self.enabled.set()
        self.epoch = 0

    def post(self, kind, payload, epoch=None):
        try:
            self.events.put_nowait((kind, payload, epoch))
        except queue.Full:
            pass  # Keep memory bounded rather than accumulating old commands.

    def run(self):
        try:
            import numpy as np
            import sounddevice as sd
            import sherpa_onnx
            from faster_whisper import WhisperModel

            config = sherpa_onnx.VadModelConfig()
            config.silero_vad.model = str(self.args.vad_model)
            config.silero_vad.min_silence_duration = self.args.min_silence
            config.silero_vad.min_speech_duration = 0.25
            config.silero_vad.max_speech_duration = 5.0
            config.sample_rate = 16000
            config.num_threads = 1
            vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=10)
            window = config.silero_vad.window_size
            model = WhisperModel(self.args.model, device="cpu", compute_type="int8",
                                 cpu_threads=2, num_workers=1)
            self.post("notice", "Voice ready. Speak a command, then wait for feedback.")
            while not self.stopped.is_set():
                if not self.enabled.wait(timeout=0.1):
                    continue
                epoch = self.epoch
                vad.reset()
                buffer = np.empty(0, dtype=np.float32)
                utterance = None
                self.post("phase", "Listening")
                with sd.InputStream(channels=1, dtype="float32", samplerate=16000,
                                    device=self.args.mic_device) as stream:
                    while (not self.stopped.is_set() and self.enabled.is_set()
                           and epoch == self.epoch):
                        chunk, overflowed = stream.read(1600)
                        if overflowed:
                            vad.reset()
                            buffer = np.empty(0, dtype=np.float32)
                            continue
                        buffer = np.concatenate([buffer, chunk.reshape(-1)])
                        while len(buffer) >= window:
                            vad.accept_waveform(buffer[:window])
                            buffer = buffer[window:]
                        if not vad.empty():
                            utterance = np.array(vad.front.samples, dtype=np.float32)
                            vad.pop()
                            break
                if utterance is None or epoch != self.epoch or self.stopped.is_set():
                    continue
                self.post("phase", "Thinking")
                segments, _ = model.transcribe(utterance, beam_size=1, language="en",
                                               condition_on_previous_text=False)
                text = " ".join(s.text.strip() for s in segments)
                if text and epoch == self.epoch and self.enabled.is_set():
                    self.post("voice", text, epoch)
        except Exception as exc:
            self.post("notice", f"Voice unavailable: {exc}. Keyboard controller still works.")


class App:
    def __init__(self, args):
        self.args = args
        self.events = queue.Queue(maxsize=8)
        self.stopped = threading.Event()
        self.voice = Voice(args, self.events, self.stopped)
        self.recorder = Recorder(args)
        self.mode = "ready"
        self.files = []
        self.selected = 0
        self.player = None
        self.monitor_failed = False
        self.icon = None
        self.message = 'Say "start recording" or "video library".'
        self.voice_phase = "Keyboard controller" if args.no_voice else "Loading voice model"
        self.screen = None if args.no_screen else Screen(args)
        self.tts = None if args.no_tts else (shutil.which("espeak-ng") or shutil.which("espeak"))

    def say(self, message):
        print(f"[{self.mode}] {message}", flush=True)
        self.message = message
        phase_before = self.voice_phase
        if self.tts:
            self.voice_phase = "Speaking"
        if self.screen:
            self.screen.render(self)
        self.voice.enabled.clear()
        self.voice.epoch += 1
        try:
            if self.tts:
                subprocess.run([self.tts, "-s", "165", message],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=12)
        except (OSError, subprocess.TimeoutExpired):
            print("Speech output failed; use the terminal feedback.", flush=True)
        finally:
            if self.tts:
                time.sleep(0.2)
            self.voice_phase = ("Keyboard controller" if self.args.no_voice or
                                phase_before == "Keyboard controller" else
                                ("Loading voice model" if phase_before == "Loading voice model"
                                 else "Listening"))
            self.voice.enabled.set()

    def show_library(self):
        self.files = sorted(self.recorder.root.glob("*.mp4"), reverse=True)
        self.selected = min(self.selected, max(0, len(self.files) - 1))
        if not self.files:
            print("No completed videos yet.", flush=True)
        else:
            # Display just five rows, regardless of the number of saved videos.
            first = max(0, self.selected - 2)
            for i in range(first, min(first + 5, len(self.files))):
                print(f"{'>' if i == self.selected else ' '} {i + 1}: {self.files[i].name}",
                      flush=True)

    def stop_player(self):
        if self.player is not None:
            self.player.close()
            self.player = None
            self.voice.enabled.set()

    def command(self, text, source):
        cmd = re.sub(r"[^a-z0-9 ]", "", text.lower())
        cmd = " ".join(cmd.split())
        cmd = re.sub(r"^please | please$", "", cmd)
        cmd = {"start": "start recording", "pause": "pause recording",
               "resume": "resume recording", "end": "end recording",
               "stop recording": "end recording", "library": "video library",
               "play": "play video", "play recording": "resume recording",
               "help settings": "help"}.get(cmd, cmd)
        print(f"{source}: {text}", flush=True)
        before = self.mode
        outcome = "accepted"
        try:
            if cmd == "quit" and source == "keyboard":
                self.stopped.set()
            elif cmd == "help":
                self.say(HELP)
            elif cmd == "start recording" and self.mode in ("ready", "library"):
                self.stop_player()
                if self.recorder.session is not None:
                    raise RuntimeError("Previous session needs recovery; restart the app first.")
                self.recorder.start_segment()
                self.monitor_failed = False
                self.mode = "recording"
                self.icon = "record.webp"
                self.say("Recording started.")
            elif cmd == "pause recording" and self.mode == "recording":
                self.recorder.stop_segment()
                self.mode = "paused"
                self.icon = "pause_button.png"
                self.say("Recording paused.")
            elif cmd == "resume recording" and self.mode == "paused":
                self.recorder.start_segment()
                self.monitor_failed = False
                self.mode = "recording"
                self.icon = "record.webp"
                self.say("Recording resumed.")
            elif cmd == "end recording" and self.mode in ("recording", "paused"):
                path = self.recorder.finish()
                self.mode = "ready"
                self.monitor_failed = False
                self.icon = None
                print(f"Saved file: {path}", flush=True)
                self.say("Video saved. Say video library to watch it.")
            elif cmd == "video library" and self.mode in ("ready", "library"):
                self.stop_player()
                self.mode = "library"
                self.icon = None
                self.say("Video library. Use up and down, then play video.")
                self.show_library()
            elif cmd in ("up", "down") and self.mode == "library":
                self.selected = max(0, min(self.selected + (1 if cmd == "down" else -1),
                                           len(self.files) - 1))
                self.show_library()
            elif cmd == "play video" and self.mode == "library" and self.files:
                if self.screen is None:
                    self.say("Playback needs the PiTFT. Relaunch without no screen.")
                    print(f"Selected file: {self.files[self.selected]}", flush=True)
                else:
                    self.stop_player()
                    self.say("Playing video. Say back, or press either button to stop.")
                    self.player = VideoPlayer(self.files[self.selected], self.screen.width,
                                              self.screen.height, self.args.playback_fps)
                    self.mode = "playing"
            elif cmd == "back" and self.mode in ("playing", "library"):
                was_playing = self.mode == "playing"
                self.stop_player()
                self.mode = "library" if was_playing else "ready"
                self.icon = None
                self.say("Video library." if was_playing else "Ready.")
                if was_playing:
                    self.show_library()
            else:
                outcome = "unavailable"
                self.say("Command unavailable here. " +
                         ("End recording before opening the library." if
                          self.mode in ("recording", "paused") else "Say help settings for commands."))
        except Exception as exc:
            self.monitor_failed = True
            if self.recorder.session and self.recorder.proc is None:
                self.mode = "paused"
                self.icon = "pause_button.png"
            self.say(f"Error: {exc}")
            outcome = "error"
        entry = {"time_utc": datetime.now(timezone.utc).isoformat(), "source": source,
                 "heard": text, "command": cmd, "before": before, "after": self.mode,
                 "outcome": outcome, "feedback": self.message}
        with (self.recorder.root / "interactions.jsonl").open("a") as log:
            log.write(json.dumps(entry) + "\n")

    def keyboard(self):
        for line in sys.stdin:
            if self.stopped.is_set():
                break
            self.events.put(("keyboard", line.strip(), None))

    def tick(self):
        if self.player and self.player.finished.is_set() and self.player.frames.empty():
            error = self.player.error
            self.stop_player()
            self.mode = "library"
            self.say(error or "Playback finished. Video library.")
            self.show_library()
        if self.mode in ("recording", "paused") and not self.monitor_failed:
            rec = self.recorder
            low_space = shutil.disk_usage(rec.root).free < self.args.reserve_mb * 1024**2
            expired = time.monotonic() - rec.started >= self.args.max_seconds
            exited = rec.proc is not None and rec.proc.poll() is not None
            if low_space or expired or exited:
                self.say("Stopping recording: storage, time limit, or capture stopped.")
                self.command("end recording", "system")

    def run(self):
        print(HELP, flush=True)
        self.say("Ready. Say start recording, or type a command and press Enter.")
        threading.Thread(target=self.keyboard, daemon=True).start()
        if not self.args.no_voice:
            threading.Thread(target=self.voice.run, daemon=True).start()
        last_check = 0
        try:
            while not self.stopped.is_set():
                try:
                    kind, payload, epoch = self.events.get(timeout=0.1)
                    if kind == "notice":
                        print(payload, flush=True)
                        if payload.startswith("Voice unavailable"):
                            self.voice_phase = "Keyboard controller"
                            self.message = payload
                    elif kind == "phase":
                        self.voice_phase = payload
                    elif kind != "voice" or epoch == self.voice.epoch:
                        self.command(payload, kind)
                except queue.Empty:
                    pass
                if self.screen:
                    for button_command in self.screen.poll_buttons():
                        if self.mode == "library":
                            self.command(button_command, "button")
                        elif self.mode == "playing":
                            self.command("back", "button")
                    self.screen.render(self)
                if time.monotonic() - last_check >= 1:
                    self.tick()
                    last_check = time.monotonic()
        except KeyboardInterrupt:
            print("\nStopping...", flush=True)
        finally:
            self.stopped.set()
            self.voice.enabled.clear()
            self.stop_player()
            if self.recorder.session:
                try:
                    print(f"Saved on exit: {self.recorder.finish()}", flush=True)
                except Exception as exc:
                    print(f"Could not finish recording: {exc}. Temporary files retained.",
                          flush=True)
            if self.screen:
                self.screen.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-voice", action="store_true")
    parser.add_argument("--no-tts", action="store_true")
    parser.add_argument("--no-screen", action="store_true", help="terminal-only diagnostic mode")
    parser.add_argument("--cs-pin", type=int, default=5,
                        help="GPIO chip select: 5 matches your example; 8 is official CE0")
    parser.add_argument("--swap-buttons", action="store_true")
    parser.add_argument("--rotation", type=int, choices=(0, 90, 180, 270), default=0)
    parser.add_argument("--playback-fps", type=int, default=10)
    parser.add_argument("--camera", default="/dev/video0")
    parser.add_argument("--videos", type=Path, default=LAB_DIR / "videos")
    parser.add_argument("--model", default="base.en")
    parser.add_argument("--vad-model", type=Path,
                        default=LAB_DIR / "models" / "silero_vad.onnx")
    parser.add_argument("--min-silence", type=float, default=0.5)
    parser.add_argument("--mic-device", type=int, help="sounddevice input device index")
    parser.add_argument("--max-seconds", type=float, default=300)
    parser.add_argument("--reserve-mb", type=int, default=256)
    parser.add_argument("--test-source", action="store_true",
                        help="record a synthetic test pattern instead of the webcam")
    args = parser.parse_args()
    if (args.max_seconds <= 0 or args.reserve_mb < 0 or args.min_silence <= 0
            or not 1 <= args.playback_fps <= 30):
        parser.error("Time limits must be positive; reserve-mb must be nonnegative.")
    for name in ("ffmpeg", "ffprobe"):
        if not shutil.which(name):
            parser.error(f"{name} missing; install FFmpeg first.")
    if not args.no_voice and not args.vad_model.is_file():
        parser.error(f"VAD model missing: {args.vad_model}. Run the lab setup first.")
    try:
        App(args).run()
    except (ImportError, RuntimeError, OSError) as exc:
        sys.exit(f"Startup/runtime error: {exc}. Use --no-screen to diagnose without PiTFT.")


if __name__ == "__main__":
    main()
