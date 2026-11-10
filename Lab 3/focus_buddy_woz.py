"""Focus Buddy Wizard-of-Oz prototype for Raspberry Pi Lab 3 Part 2.

The participant speaks to the Pi. With --qwiic-button, they press the red
button to begin and its LED indicates device state. A hidden wizard chooses
the next response in this SSH terminal. Speech recognition suggests a
transcript; the wizard may correct it. Run with --no-screen only while
diagnosing the display.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parent
SAMPLE_RATE = 16000
VERSION = "2026.10.04.1"
NUMBER_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
    10: "ten", 15: "fifteen", 20: "twenty", 25: "twenty-five",
    30: "thirty", 40: "forty", 45: "forty-five", 50: "fifty",
    60: "sixty",
}


def configure_console() -> None:
    """SSH terminals on the Mac use UTF-8, even if the Pi inherited Latin-1."""
    for name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors=(
                    "replace" if name == "stdin" else "backslashreplace"))
            except (OSError, ValueError):
                # An embedding application may already have read its stream.
                pass


def positive_seconds(value: str) -> float:
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Enter a positive number of seconds.") from exc
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("Seconds must be positive and finite.")
    return seconds


def positive_rate(value: str) -> int:
    try:
        rate = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Enter a positive integer sample rate.") from exc
    if rate <= 0:
        raise argparse.ArgumentTypeError("Sample rate must be positive.")
    return rate


def spoken_minutes(minutes: int) -> str:
    return NUMBER_WORDS.get(minutes, str(minutes))


class Dialogue:
    """The wizard selects transitions; no autonomous intent detection is claimed."""

    def __init__(self) -> None:
        self.stage = "task"
        self.task = ""
        self.minutes = 0

    def prompt(self) -> str:
        if self.stage == "task":
            return "What is one specific thing you want to work on?"
        if self.stage == "duration":
            return "How long would you like to focus?"
        if self.stage == "confirm":
            unit = "minute" if self.minutes == 1 else "minutes"
            return (f"{self.task} for {spoken_minutes(self.minutes)} {unit}. "
                    "Say start to begin, or tell me what to change.")
        raise ValueError(f"No prompt for stage {self.stage}")

    def choose(self, action: str, value: str = "") -> str:
        if action == "repeat":
            return self.prompt()
        if self.stage == "task":
            if action == "clarify":
                return "Which class or specific assignment would you like to work on?"
            if action == "accept_task":
                task = value.strip()
                if not task:
                    raise ValueError("Enter a specific task before continuing.")
                self.task = task
                self.stage = "duration"
                return self.prompt()
        elif self.stage == "duration":
            if action == "accept_duration":
                try:
                    minutes = int(value.strip())
                except ValueError as exc:
                    raise ValueError("Enter whole minutes, from 1 to 180.") from exc
                if not 1 <= minutes <= 180:
                    raise ValueError("Enter whole minutes, from 1 to 180.")
                self.minutes = minutes
                self.stage = "confirm"
                return self.prompt()
            if action == "change_task":
                self.stage = "task"
                return self.prompt()
        elif self.stage == "confirm":
            if action == "start":
                self.stage = "focus"
                return (f"Starting your {spoken_minutes(self.minutes)} minute "
                        "focus session now.")
            if action == "change_task":
                self.stage = "task"
                return self.prompt()
            if action == "change_duration":
                self.stage = "duration"
                return self.prompt()
        raise ValueError(f"Action {action!r} is unavailable at stage {self.stage!r}.")


class EventLog:
    def __init__(self, path: Path | None) -> None:
        self.path = path
        self.started = time.monotonic()
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Fail before a participant starts if the log cannot be written.
            with path.open("a", encoding="utf-8"):
                pass

    def add(self, event: str, **details: object) -> None:
        record = {"at": datetime.now(timezone.utc).isoformat(),
                  "elapsed_seconds": round(time.monotonic() - self.started, 3),
                  "event": event, **details}
        print(f"[event] {event}: {details}", flush=True)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")


class MiniPiTFT:
    """ST7789 display with pixel-measured text and an independent timer row."""

    def __init__(self) -> None:
        self.cs_pin = self.dc_pin = self.spi = self.backlight = None
        self.display = None
        try:
            try:
                import board
                import digitalio
                import adafruit_rgb_display.st7789 as st7789
                from PIL import Image, ImageDraw, ImageFont
            except ImportError as exc:
                raise RuntimeError(
                    "MiniPiTFT library missing in Lab 3 .venv. Install "
                    "adafruit-blinka, adafruit-circuitpython-rgb-display, and pillow."
                ) from exc
            self.image_cls = Image
            self.draw_cls = ImageDraw
            try:
                self.font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                self.small_font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except OSError:
                self.font = self.small_font = ImageFont.load_default()
            self.cs_pin = digitalio.DigitalInOut(board.D5)
            self.dc_pin = digitalio.DigitalInOut(board.D25)
            self.spi = board.SPI()
            self.display = st7789.ST7789(
                self.spi, cs=self.cs_pin, dc=self.dc_pin, rst=None,
                baudrate=64000000, width=135, height=240,
                x_offset=53, y_offset=40,
            )
            self.backlight = digitalio.DigitalInOut(board.D22)
            self.backlight.switch_to_output(value=True)
        except BaseException:
            self.close()
            raise

    @staticmethod
    def _wrap_pixels(draw: object, text: str, font: object,
                     max_width: int, max_lines: int) -> list[str]:
        """Wrap by measured width, splitting long words and marking omitted text."""
        words = str(text).split()
        lines = []
        line = ""
        for word in words:
            candidate = f"{line} {word}" if line else word
            if draw.textlength(candidate, font=font) <= max_width:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ""
            for character in word:
                if line and draw.textlength(line + character, font=font) > max_width:
                    lines.append(line)
                    line = ""
                line += character
        if line:
            lines.append(line)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            last = lines[-1].rstrip()
            while last and draw.textlength(last + "...", font=font) > max_width:
                last = last[:-1]
            lines[-1] = last + "..."
        return lines

    def show(self, state: str, detail: str = "", timer: str | None = None) -> None:
        colors = {
            "BOOTING": "#23395B", "READY": "#23395B", "SPEAKING": "#215D6B",
            "LISTENING": "#176B47", "PROCESSING": "#805900", "FOCUS": "#432B72",
            "ENDED": "#333333", "DONE": "#176B47", "STOPPED": "#333333",
            "ERROR": "#8B2424",
        }
        image = self.image_cls.new("RGB", (240, 135), colors.get(state, "#222222"))
        draw = self.draw_cls.Draw(image)
        draw.text((10, 10), state, font=self.font, fill="white")
        lines = self._wrap_pixels(draw, detail, self.small_font, 220,
                                  2 if timer is not None else 3)
        for line_number, line in enumerate(lines):
            draw.text((10, 48 + 23 * line_number), line,
                      font=self.small_font, fill="white")
        if timer is not None:
            draw.text((10, 102), str(timer), font=self.font, fill="white")
        self.display.image(image, 90)

    def close(self) -> None:
        """Release every acquired resource, including after partial initialization."""
        for name in ("backlight", "dc_pin", "cs_pin", "spi"):
            resource = getattr(self, name, None)
            if resource is None:
                continue
            setattr(self, name, None)
            if name == "backlight":
                try:
                    resource.value = False
                except Exception as exc:
                    print(f"[hardware] Could not switch off backlight: {exc}", file=sys.stderr)
            try:
                resource.deinit()
            except Exception as exc:
                print(f"[hardware] Could not release {name}: {exc}", file=sys.stderr)


class StatusLed:
    """Optional external one-color LED; --led-pin takes a board name like D17."""

    def __init__(self, pin_name: str | None) -> None:
        self.led = None
        self.mode = "off"
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.thread = None
        try:
            if pin_name:
                import board
                import digitalio
                self.led = digitalio.DigitalInOut(getattr(board, pin_name))
                self.led.switch_to_output(value=False)
                self.thread = threading.Thread(target=self._run, daemon=True)
                self.thread.start()
        except BaseException:
            self.close()
            raise

    def set(self, state: str) -> None:
        with self.lock:
            self.mode = ("on" if state == "LISTENING" else
                         "blink" if state == "PROCESSING" else "off")
            if self.led is not None:
                self.led.value = self.mode in ("on", "blink")

    def _run(self) -> None:
        while not self.stop.wait(0.45):
            with self.lock:
                if self.led is not None:
                    self.led.value = (True if self.mode == "on" else
                                      not self.led.value if self.mode == "blink" else False)

    def close(self) -> None:
        self.stop.set()
        if self.thread and self.thread.ident is not None:
            self.thread.join(timeout=1)
        with self.lock:
            led, self.led = self.led, None
            if led is not None:
                try:
                    led.value = False
                finally:
                    led.deinit()


class QwiicButtonDevice:
    """SparkFun Qwiic Button at its default I2C address, 0x6f."""

    def __init__(self, device: object | None = None) -> None:
        self.closed = False
        if device is None:
            import qwiic_button
            device = qwiic_button.QwiicButton()
        if not device.begin():
            raise RuntimeError("Qwiic Button did not initialize at I2C address 0x6f")
        self.device = device
        self.device.LED_off()

    def show(self, state: str) -> None:
        if state == "READY":
            # The firmware adds off_time AFTER cycle_time; these are not duty cycles.
            self.device.LED_config(60, 1000, 1000)
        elif state == "LISTENING":
            self.device.LED_on(90)
        elif state == "PROCESSING":
            self.device.LED_config(90, 500, 500)
        else:
            self.device.LED_off()

    def wait_for_press(self, poll_seconds: float = 0.05) -> None:
        while not self.device.is_button_pressed():
            time.sleep(poll_seconds)
        while self.device.is_button_pressed():
            time.sleep(poll_seconds)

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            self.device.LED_off()


class Interface:
    def __init__(self, use_screen: bool, led_pin: str | None,
                 use_qwiic_button: bool, log: EventLog) -> None:
        self.log = log
        self.screen = None
        self.led = None
        self.qwiic_button = None
        try:
            self.screen = MiniPiTFT() if use_screen else None
            self.led = StatusLed(led_pin)
            self.qwiic_button = QwiicButtonDevice() if use_qwiic_button else None
        except BaseException:
            self.close()
            raise

    def show(self, state: str, detail: str = "", timer: str | None = None) -> None:
        print(f"[device] {state}: {detail}", flush=True)
        if self.screen:
            self.screen.show(state, detail, timer=timer)
        if self.led:
            self.led.set(state)
        if self.qwiic_button:
            self.qwiic_button.show(state)
        self.log.add("state", state=state, detail=detail, timer=timer)

    def close(self) -> None:
        for name in ("qwiic_button", "led", "screen"):
            resource = getattr(self, name, None)
            setattr(self, name, None)
            if resource is not None:
                try:
                    resource.close()
                except Exception as exc:
                    print(f"[cleanup] {name}: {exc}", file=sys.stderr)


def check_audio_devices(args: argparse.Namespace, sd: object | None = None) -> tuple[int, int]:
    """Validate formats before loading models or showing READY.

    Both USB devices were measured working at 48 kHz. PortAudio device indexes
    are independent from ALSA card numbers, so validate the chosen direction too.
    This checks formats only; the operator must still verify audible playback.
    """
    if sd is None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("Install sounddevice in the active Lab 3 .venv.") from exc
    input_rate = getattr(args, "input_rate", 48000)
    output_rate = getattr(args, "output_rate", 48000)
    if input_rate not in (16000, 32000, 48000):
        raise ValueError("Input rate must be 16000, 32000, or 48000 Hz.")
    if not isinstance(output_rate, int) or output_rate <= 0:
        raise ValueError("Output rate must be a positive whole number of Hz.")
    for kind, device, rate, dtype, check in (
        ("input", args.input_device, input_rate, "float32", sd.check_input_settings),
        ("output", args.output_device, output_rate, "int16", sd.check_output_settings),
    ):
        try:
            info = sd.query_devices(device, kind)
            check(device=device, samplerate=rate, channels=1, dtype=dtype)
        except (sd.PortAudioError, ValueError) as exc:
            raise RuntimeError(
                f"Audio {kind} device {device} cannot use {rate} Hz mono {dtype}: {exc}. "
                "Run --list-devices and choose the correct input/output indexes. "
                "The tested USB setup uses --input-device 1 --output-device 0 "
                "--input-rate 48000 --output-rate 48000."
            ) from exc
        print(f"[audio] {kind}: {info['name']}; {rate} Hz mono {dtype}", flush=True)
    return input_rate, output_rate


class StreamingDownsampler:
    """Convert capture chunks to 16 kHz without restarting the filter per chunk."""

    def __init__(self, input_rate: int) -> None:
        import numpy as np
        from scipy.signal import firwin
        if input_rate not in (16000, 32000, 48000):
            raise ValueError("Capture rate must be 16000, 32000, or 48000 Hz.")
        self.factor = input_rate // SAMPLE_RATE
        self.offset = 0
        # Low-pass before decimation prevents high-frequency sound aliasing into
        # the recognizer's range; state and sample phase survive chunk boundaries.
        self.taps = (firwin(127, 7200, fs=input_rate)
                     if self.factor > 1 else None)
        self.state = np.zeros(126, dtype=np.float64)

    def process(self, samples: object) -> object:
        import numpy as np
        from scipy.signal import lfilter
        audio = np.asarray(samples, dtype=np.float32).reshape(-1)
        if not len(audio) or self.factor == 1:
            return audio
        filtered, self.state = lfilter(self.taps, [1.0], audio, zi=self.state)
        converted = filtered[self.offset::self.factor].astype(np.float32)
        self.offset = (self.offset - len(audio)) % self.factor
        return converted


class Speech:
    def __init__(self, args: argparse.Namespace) -> None:
        import sounddevice as sd
        self.sd = sd
        self.input_rate, self.output_rate = check_audio_devices(args, sd)
        try:
            import numpy
            from scipy.signal import firwin, lfilter, resample_poly
        except ImportError as exc:
            raise RuntimeError(
                "Audio conversion requires numpy and scipy in Lab 3 .venv. "
                "Run: python -m pip install numpy scipy"
            ) from exc
        try:
            import sherpa_onnx
            from faster_whisper import WhisperModel
            from piper import PiperVoice
        except ImportError as exc:
            raise RuntimeError(
                "Speech dependencies missing in Lab 3 .venv. "
                "Install the lab requirements (sherpa-onnx, faster-whisper, piper-tts)."
            ) from exc

        self.input_device = args.input_device
        self.output_device = args.output_device
        self.min_silence = args.min_silence
        self.vad_path = args.vad_model
        self.max_utterance_seconds = getattr(args, "max_utterance_seconds", 30.0)
        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = str(self.vad_path)
        config.silero_vad.min_silence_duration = self.min_silence
        config.silero_vad.max_speech_duration = self.max_utterance_seconds
        config.sample_rate = SAMPLE_RATE
        self.vad_window = config.silero_vad.window_size
        # Load once before the participant starts. Reset between utterances.
        self.vad = sherpa_onnx.VoiceActivityDetector(
            config, buffer_size_in_seconds=self.max_utterance_seconds + 2)
        self.model = WhisperModel(args.model, device="cpu", compute_type="int8")
        self.voice = PiperVoice.load(str(args.voice))

    def say(self, message: str) -> None:
        import numpy as np
        from math import gcd
        from scipy.signal import resample_poly
        produced_audio = False
        try:
            for chunk in self.voice.synthesize(message):
                if getattr(chunk, "sample_channels", 1) != 1:
                    raise RuntimeError("This prototype requires a mono Piper voice.")
                audio = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
                if not len(audio):
                    continue
                source_rate = int(chunk.sample_rate)
                if source_rate <= 0:
                    raise RuntimeError("Piper returned an invalid sample rate.")
                if source_rate != self.output_rate:
                    divisor = gcd(source_rate, self.output_rate)
                    audio = resample_poly(
                        audio.astype(np.float32),
                        self.output_rate // divisor, source_rate // divisor)
                    audio = np.clip(np.rint(audio), -32768, 32767).astype(np.int16)
                self.sd.play(audio, samplerate=self.output_rate,
                             device=self.output_device)
                self.sd.wait()
                produced_audio = True
            if not produced_audio:
                raise RuntimeError("Piper produced no audio for the device prompt.")
        finally:
            # Release the playback stream on success, error, or Ctrl+C.
            self.sd.stop()

    def hear(self, first_speech_timeout: float, on_listening=None) -> object | None:
        import numpy as np
        vad = self.vad
        vad.reset()
        converter = StreamingDownsampler(self.input_rate)
        window = self.vad_window
        buffer = np.empty(0, dtype=np.float32)
        speech_started = False
        frames_read = 0
        with self.sd.InputStream(channels=1, dtype="float32",
                                 samplerate=self.input_rate,
                                 device=self.input_device) as stream:
            if on_listening is not None:
                on_listening()
            started = time.monotonic()
            while True:
                chunk, overflow = stream.read(int(0.1 * self.input_rate))
                if overflow:
                    raise RuntimeError(
                        "Microphone input overflowed; audio was lost. "
                        "Close other audio programs and retry the interaction.")
                frames_read += len(chunk)
                buffer = np.concatenate([buffer, converter.process(chunk)])
                while len(buffer) >= window:
                    vad.accept_waveform(buffer[:window])
                    buffer = buffer[window:]
                    speech_started = speech_started or vad.is_speech_detected()
                    if not vad.empty():
                        utterance = np.array(vad.front.samples, dtype=np.float32)
                        vad.pop()
                        return utterance
                elapsed = max(time.monotonic() - started,
                              frames_read / self.input_rate)
                if not speech_started and elapsed >= first_speech_timeout:
                    return None
                if elapsed >= self.max_utterance_seconds:
                    print("[audio] Listening limit reached; finishing this turn.", flush=True)
                    if len(buffer):
                        vad.accept_waveform(np.pad(buffer, (0, window - len(buffer))))
                    vad.flush()
                    if not vad.empty():
                        utterance = np.array(vad.front.samples, dtype=np.float32)
                        vad.pop()
                        return utterance
                    return None

    def transcribe(self, utterance: object) -> str:
        segments, _info = self.model.transcribe(utterance, beam_size=1)
        return " ".join(segment.text.strip() for segment in segments).strip()

    def close(self) -> None:
        self.sd.stop()


OPTIONS = {
    "task": {"1": ("accept_task", "Accept specific task"),
             "2": ("clarify", "Ask which class or assignment"),
             "3": ("repeat", "Repeat prompt")},
    "duration": {"1": ("accept_duration", "Accept duration"),
                 "2": ("repeat", "Repeat prompt"),
                 "3": ("change_task", "Change task")},
    "confirm": {"1": ("start", "Start focus session"),
                "2": ("change_task", "Change task"),
                "3": ("change_duration", "Change duration"),
                "4": ("repeat", "Repeat confirmation")},
}


def ask_wizard(dialogue: Dialogue, heard: str) -> tuple[str, str, str]:
    print(f"\n[controller] Recognized: {heard!r}")
    for key, (_action, label) in OPTIONS[dialogue.stage].items():
        print(f"  {key}. {label}")
    print("  q. End interaction")
    while True:
        key = input("Wizard choice: ").strip().lower()
        if key == "q":
            return "quit", "", ""
        if key not in OPTIONS[dialogue.stage]:
            print("Choose one listed option.")
            continue
        action = OPTIONS[dialogue.stage][key][0]
        value = ""
        if action == "accept_task":
            value = input("Clean task wording to repeat aloud: ").strip()
        elif action == "accept_duration":
            value = input("Whole minutes (1-180): ").strip()
        try:
            reply = dialogue.choose(action, value)
        except ValueError as exc:
            print(exc)
            continue
        return action, value, reply


def focus_timer(dialogue: Dialogue, ui: Interface, log: EventLog) -> None:
    deadline = time.monotonic() + dialogue.minutes * 60
    log.add("focus_start", task=dialogue.task, minutes=dialogue.minutes)
    while True:
        remaining = max(0, int(deadline - time.monotonic() + 0.999))
        ui.show("FOCUS", dialogue.task,
                timer=f"{remaining // 60:02}:{remaining % 60:02}")
        if remaining == 0:
            log.add("focus_end")
            ui.show("DONE", "Focus session complete")
            return
        time.sleep(min(1, remaining))


def run_interaction(args: argparse.Namespace, speech: Speech,
                    ui: Interface, log: EventLog) -> None:
    """Run one participant session; the SSH controller chooses every action."""
    dialogue = Dialogue()
    ui.show("READY", "Press red button" if args.qwiic_button else "Focus Buddy")
    if ui.qwiic_button:
        print("[controller] Waiting for participant to press and release the red button.")
        ui.qwiic_button.wait_for_press()
        log.add("qwiic_button_start")
    else:
        input("[controller] Press Enter to begin after participant is ready: ")
    prompt = dialogue.prompt()
    while True:
        ui.show("SPEAKING", prompt)
        log.add("device_speech", text=prompt)
        speech.say(prompt)
        heard = ""
        for attempt in range(2):
            ui.show("PROCESSING", "Getting ready to listen")
            utterance = speech.hear(
                args.first_speech_timeout,
                on_listening=lambda: ui.show("LISTENING", "Speak now"))
            if utterance is not None:
                ui.show("PROCESSING", "Please wait")
                heard = speech.transcribe(utterance).strip()
                if heard:
                    break
            if attempt == 0:
                reminder = ("Take your time. Please say your answer when ready."
                            if utterance is None else
                            "I did not catch that. Please say your answer again.")
                ui.show("SPEAKING", reminder)
                log.add("reminder", text=reminder)
                speech.say(reminder)
        if not heard:
            log.add("no_response_end")
            ui.show("ENDED", "No answer. Session ended.")
            return
        log.add("recognized", text=heard, stage=dialogue.stage)
        ui.show("PROCESSING", "Please wait")
        action, value, prompt = ask_wizard(dialogue, heard)
        if action == "quit":
            log.add("wizard_quit")
            ui.show("ENDED", "Session ended")
            return
        log.add("wizard_choice", action=action, value=value,
                next_stage=dialogue.stage)
        if dialogue.stage == "focus":
            ui.show("SPEAKING", prompt)
            log.add("device_speech", text=prompt)
            speech.say(prompt)
            focus_timer(dialogue, ui, log)
            return


def report_terminal_state(ui: Interface | None, log: EventLog,
                          state: str, detail: str) -> None:
    # Preserve the original error even if the I2C device or the log also fails.
    try:
        log.add("session_end", state=state, detail=detail)
    except Exception as exc:
        print(f"[cleanup] Unable to log final state: {exc}", file=sys.stderr)
    if ui is not None:
        try:
            ui.show(state, detail)
        except Exception as exc:
            print(f"[cleanup] Unable to display final state: {exc}", file=sys.stderr)


def main() -> None:
    configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--model", default="tiny.en")
    parser.add_argument("--vad-model", type=Path,
                        default=LAB_DIR / "models" / "silero_vad.onnx")
    parser.add_argument("--voice", type=Path,
                        default=LAB_DIR / "voices" / "en_US-lessac-medium.onnx")
    parser.add_argument("--min-silence", type=positive_seconds, default=0.7)
    parser.add_argument("--first-speech-timeout", type=positive_seconds, default=6.0)
    parser.add_argument("--max-utterance-seconds", type=positive_seconds, default=30.0,
                        help="upper limit on a listening turn, including continuous noise")
    parser.add_argument("--input-rate", type=int, choices=(16000, 32000, 48000),
                        default=48000, help="microphone hardware rate; recognition remains 16000")
    parser.add_argument("--output-rate", type=positive_rate, default=48000,
                        help="speaker hardware rate; Piper audio is resampled before playback")
    parser.add_argument("--input-device", type=int,
                        help="PortAudio input index from sounddevice device list")
    parser.add_argument("--output-device", type=int,
                        help="PortAudio output index from sounddevice device list")
    parser.add_argument("--no-screen", action="store_true",
                        help="diagnostic mode only; system still requires voice")
    parser.add_argument("--led-pin", help="bare GPIO LED only; not for a Qwiic Button")
    parser.add_argument("--qwiic-button", action="store_true",
                        help="use SparkFun Qwiic Button as start input and status light")
    parser.add_argument("--log", type=Path,
                        help="optional JSONL event log; use only with participant consent")
    diagnostics = parser.add_mutually_exclusive_group()
    diagnostics.add_argument("--list-devices", action="store_true",
                        help="print PortAudio device indexes and exit")
    diagnostics.add_argument("--screen-test", action="store_true",
                        help="show each screen/LED state briefly and exit")
    diagnostics.add_argument("--check-audio", action="store_true",
                        help="check requested input/output formats without playing or recording")
    args = parser.parse_args()
    if args.max_utterance_seconds <= args.min_silence:
        parser.error("--max-utterance-seconds must exceed --min-silence")
    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        print("default input/output indexes:", sd.default.device)
        return
    if args.check_audio:
        check_audio_devices(args)
        print("Audio format checks passed; microphone/speaker behavior still requires a live run.")
        return
    if not args.screen_test:
        for path, label in ((args.vad_model, "VAD model"), (args.voice, "Piper voice"),
                            (Path(str(args.voice) + ".json"), "Piper voice configuration")):
            if not path.is_file():
                parser.error(f"{label} missing: {path}. See Lab 3/speech-scripts/setup.sh")

    log = EventLog(args.log)
    ui = None
    speech = None
    print(f"Focus Buddy {VERSION}", flush=True)
    try:
        ui = Interface(not args.no_screen, args.led_pin, args.qwiic_button, log)
        if args.screen_test:
            for state in ("READY", "SPEAKING", "LISTENING", "PROCESSING", "FOCUS"):
                ui.show(state, "Focus Buddy display test",
                        timer="01:00" if state == "FOCUS" else None)
                time.sleep(1.5)
            ui.show("ENDED", "Display test complete")
            return
        ui.show("BOOTING", "Loading. Please wait.")
        speech = Speech(args)
        run_interaction(args, speech, ui, log)
    except (KeyboardInterrupt, EOFError):
        report_terminal_state(ui, log, "STOPPED", "Session stopped")
        print("\nStopped by controller.")
    except Exception:
        report_terminal_state(ui, log, "ERROR", "Check controller terminal")
        raise
    finally:
        if speech is not None:
            try:
                speech.close()
            except Exception as exc:
                print(f"[cleanup] Audio: {exc}", file=sys.stderr)
        if ui is not None:
            ui.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by wizard.")
    except Exception as exc:
        print(f"Focus Buddy stopped: {exc}", file=sys.stderr)
        raise
