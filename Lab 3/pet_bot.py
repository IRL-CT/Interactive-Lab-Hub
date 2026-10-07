#!/usr/bin/env python3
"""Chatterbox pet: press the button, pick a friend, talk to it.

    python pet_bot.py                 # on the Pi: mic + screen + button
    python pet_bot.py --demo          # anywhere: type instead of speaking
    python pet_bot.py --min-silence 1.0

The dialogue rules live in pet_logic.py and are unit tested. This file only
connects them to hardware: microphone (Silero VAD + faster-whisper), speaker
(Piper), the MiniPiTFT screen, button A on GPIO 23, and the Adafruit I2C
rotary encoder (seesaw, address 0x36).

Pressing the knob does the same thing as button A. The knob's NeoPixel is the
LED from the README: off = asleep, green = your turn, amber = working,
blue = it is speaking. The same colour is also drawn as a bar across the top
of the screen, so the device still works if the knob is unplugged.
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

from pet_brain import DEFAULT_MODEL, DEFAULT_URL, make_brain
from pet_logic import PETS, SLEEP_SCREEN, PetMachine

SAMPLE_RATE = 16000
# Extra silence after the pet finishes speaking, before the microphone is
# switched back on, so the tail of the speaker is not heard as a new turn.
SELF_HEAR_GUARD = 0.8
# Right after the pet speaks, an empty transcript is almost always its own
# echo, not the user, so it is not counted as a failed try.
ECHO_WINDOW = 2.0
LAB_DIR = Path(__file__).resolve().parent
DEFAULT_VAD = LAB_DIR / "models" / "silero_vad.onnx"
DEFAULT_VOICE = LAB_DIR / "voices" / "en_US-lessac-medium.onnx"
LOG_PATH = LAB_DIR / "session_log.csv"

LED_COLORS = {
    "off": (40, 40, 40),
    "green": (0, 170, 80),
    "amber": (255, 165, 0),
    "blue": (0, 80, 220),
}


def draw_face(draw, kind: str, cx: float, cy: float, r: float, asleep=False) -> None:
    """A cat, dog or bird face from circles and lines: no image files needed."""
    white, dark = "#FFFFFF", "#202020"
    if kind == "cat":
        draw.polygon([(cx - r, cy - r * 0.4), (cx - r * 0.9, cy - r * 1.5),
                      (cx - r * 0.2, cy - r * 0.8)], fill=white)
        draw.polygon([(cx + r, cy - r * 0.4), (cx + r * 0.9, cy - r * 1.5),
                      (cx + r * 0.2, cy - r * 0.8)], fill=white)
    elif kind == "dog":
        draw.ellipse((cx - r * 1.35, cy - r * 0.8, cx - r * 0.55, cy + r * 0.6), fill=white)
        draw.ellipse((cx + r * 0.55, cy - r * 0.8, cx + r * 1.35, cy + r * 0.6), fill=white)
    draw.ellipse((cx - r, cy - r * 0.85, cx + r, cy + r * 0.85), fill=white)
    eye_y = cy - r * 0.15
    for dx in (-r * 0.38, r * 0.38):
        if asleep:
            draw.line((cx + dx - r * 0.18, eye_y, cx + dx + r * 0.18, eye_y),
                      fill=dark, width=2)
        else:
            draw.ellipse((cx + dx - r * 0.12, eye_y - r * 0.14,
                          cx + dx + r * 0.12, eye_y + r * 0.14), fill=dark)
    if kind == "bird":
        draw.polygon([(cx - r * 0.18, cy + r * 0.2), (cx + r * 0.18, cy + r * 0.2),
                      (cx, cy + r * 0.62)], fill="#F5A11E")
    else:
        draw.arc((cx - r * 0.35, cy + r * 0.05, cx + r * 0.35, cy + r * 0.5),
                 start=15, end=165, fill=dark, width=2)


class Screen:
    """MiniPiTFT display, or printed lines when there is no screen attached."""

    def __init__(self) -> None:
        self.display = None
        self.led_hook = None      # called with the LED colour on every update
        try:
            import board
            import digitalio
            from adafruit_rgb_display import st7789
            from PIL import Image, ImageDraw, ImageFont

            # Same pins as Lab 2's working screen_clock.py.
            cs = digitalio.DigitalInOut(board.D5)
            dc = digitalio.DigitalInOut(board.D25)
            self.display = st7789.ST7789(
                board.SPI(), cs=cs, dc=dc, rst=None, baudrate=64000000,
                width=135, height=240, x_offset=53, y_offset=40,
            )
            backlight = digitalio.DigitalInOut(board.D22)
            backlight.switch_to_output()
            backlight.value = True

            self.width, self.height = self.display.height, self.display.width
            self.Image, self.ImageDraw = Image, ImageDraw
            self.font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            self.small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except Exception as exc:  # no screen, wrong wiring, running on a laptop
            print(f"(no screen: {type(exc).__name__}: {exc})")
            if isinstance(exc, ImportError):
                print("  -> pip install adafruit-circuitpython-rgb-display pillow")
            else:
                print("  -> is another program using the screen? "
                      "sudo systemctl stop piscreen.service")

    def show(self, led: str, main: str, heard: str = "",
             state: str | None = None, animal: str | None = None) -> None:
        print(f"  [{led:5}] {main}" + (f"   heard: {heard}" if heard else ""))
        if self.led_hook is not None:
            self.led_hook(led)
        if self.display is None:
            return
        image = self.render(led, main, heard, state, animal)
        self.display.image(image, 90)

    def render(self, led, main, heard="", state=None, animal=None):
        """Builds the frame. Kept separate so it can be rendered without a Pi."""
        image = self.Image.new("RGB", (self.width, self.height), (20, 20, 20))
        draw = self.ImageDraw.Draw(image)
        draw.rectangle((0, 0, self.width, 18), fill=LED_COLORS.get(led, (40, 40, 40)))
        middle = 18 + (self.height - 18) // 2

        if state == "CHOOSE":
            for i, kind in enumerate(("cat", "dog", "bird")):
                cx = self.width * (i + 0.5) / 3
                draw_face(draw, kind, cx, middle - 12, 22)
                draw.text((cx, middle + 26), kind, font=self.small,
                          fill="#FFFFFF", anchor="mm")
        elif animal:
            name = PETS[animal]["name"]
            draw_face(draw, animal, 44, middle, 26)
            draw.text((self.width // 2 + 34, middle - 20), name,
                      font=self.font, fill="#FFFFFF", anchor="mm")
            # `main` is the pet's name while it waits, and its line while it
            # talks. Only the line is worth a second row.
            if main and main != name:
                for i, row in enumerate(_wrap(main, 20, 2)):
                    draw.text((self.width // 2 + 34, middle + 6 + i * 14), row,
                              font=self.small, fill="#DDDDDD", anchor="mm")
        else:
            draw_face(draw, "cat", self.width // 2, middle - 18, 22, asleep=True)
            draw.text((self.width // 2, middle + 24), main, font=self.font,
                      fill="#FFFFFF", anchor="mm")

        if heard:
            draw.text((self.width // 2, self.height - 10), f'heard: "{_fit(heard, 30)}"',
                      font=self.small, fill="#999999", anchor="mm")
        return image


class Button:
    """Button A on GPIO 23, or the Enter key when there is no GPIO.

    The keyboard fallback exists so the whole interaction can be tested on a
    laptop with a microphone, before it ever runs on the Pi.
    """

    def __init__(self) -> None:
        self.pin = None
        self.was_down = False
        self.key_presses = 0
        try:
            import board
            import digitalio

            self.pin = digitalio.DigitalInOut(board.D23)
            self.pin.switch_to_input(pull=digitalio.Pull.UP)
        except Exception as exc:
            print(f"(no GPIO button: {exc}) — press Enter instead")
            self._listen_for_enter()

    def _listen_for_enter(self) -> None:
        import threading

        def reader():
            for _ in sys.stdin:          # one press per line
                self.key_presses += 1

        threading.Thread(target=reader, daemon=True).start()

    def pressed(self) -> bool:
        if self.pin is None:
            if self.key_presses:
                self.key_presses -= 1
                return True
            return False
        down = not self.pin.value          # active low
        clicked = down and not self.was_down
        self.was_down = down
        return clicked


class Knob:
    """Adafruit I2C rotary encoder: its push button and its NeoPixel LED.

    Optional. If it is unplugged, or a loose wire makes I2C fail mid-run, it
    switches itself off with one message and the rest keeps working.
    """

    ADDRESS = 0x36
    BUTTON_PIN = 24
    PIXEL_PIN = 6
    BRIGHTNESS = 0.3
    # Pure colours: a NeoPixel mixes channels, so the screen's teal-ish green
    # (0, 170, 80) looked blue on the LED. Each state gets one clear hue here.
    COLORS = {
        "off": (0, 0, 0),
        "green": (0, 255, 0),
        "amber": (255, 90, 0),
        "blue": (0, 0, 255),
    }

    def __init__(self) -> None:
        self.ok = False
        self.was_down = False
        self.current = None
        try:
            import board
            from adafruit_seesaw import digitalio, neopixel, seesaw

            ss = seesaw.Seesaw(board.I2C(), addr=self.ADDRESS)
            ss.pin_mode(self.BUTTON_PIN, ss.INPUT_PULLUP)
            self.button = digitalio.DigitalIO(ss, self.BUTTON_PIN)
            self.pixel = neopixel.NeoPixel(ss, self.PIXEL_PIN, 1)
            self.pixel.brightness = self.BRIGHTNESS
            self.ok = True
            print("(knob found at 0x36: press = button, NeoPixel = LED)")
        except ImportError:
            print("(no knob: pip install adafruit-circuitpython-seesaw)")
        except Exception as exc:
            print(f"(no knob at 0x36: {exc}) — using button A only")

    def _give_up(self, exc: Exception) -> None:
        print(f"(knob stopped responding: {exc}) — check the I2C wires")
        self.ok = False

    def pressed(self) -> bool:
        if not self.ok:
            return False
        try:
            down = not self.button.value       # active low
        except Exception as exc:
            self._give_up(exc)
            return False
        clicked = down and not self.was_down
        self.was_down = down
        return clicked

    def set_led(self, name: str) -> None:
        if not self.ok or name == self.current:
            return                              # skip repeat I2C writes
        try:
            self.pixel.fill(self.COLORS.get(name, (0, 0, 0)))
            self.current = name
        except Exception as exc:
            self._give_up(exc)


class Speaker:
    """Piper, with a per-animal speaking rate."""

    def __init__(self, voice_path: Path) -> None:
        from piper import PiperVoice

        self.voice = PiperVoice.load(str(voice_path))
        try:
            from piper import SynthesisConfig
            self.SynthesisConfig = SynthesisConfig
        except ImportError:
            self.SynthesisConfig = None

    def say(self, text: str, animal: str | None = None) -> None:
        import numpy as np
        import sounddevice as sd

        kwargs = {}
        if animal and self.SynthesisConfig is not None:
            kwargs["syn_config"] = self.SynthesisConfig(
                length_scale=PETS[animal]["length_scale"])
        try:
            chunks = self.voice.synthesize(text, **kwargs)
        except TypeError:       # older/newer piper without syn_config
            chunks = self.voice.synthesize(text)
        for chunk in chunks:
            audio = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            sd.play(audio, samplerate=chunk.sample_rate)
            sd.wait()


def _wrap(text: str, limit: int, rows: int) -> list[str]:
    """Split a spoken line into at most `rows` short rows for the small screen."""
    words, lines, line = text.split(), [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) <= limit:
            line = candidate
        else:
            lines.append(line)
            line = word
            if len(lines) == rows:
                break
    if line and len(lines) < rows:
        lines.append(line)
    if len(lines) == rows and len(" ".join(lines)) < len(text):
        lines[-1] = _fit(lines[-1] + "\u2026", limit)
    return lines


def _fit(text: str, limit: int) -> str:
    """Trim a line so it fits the 240 px screen."""
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


def _words(text: str) -> list[str]:
    return "".join(c.lower() if c.isalnum() else " " for c in text).split()


def is_own_echo(heard: str, last_said: str) -> bool:
    """True when the transcript is mostly the line the pet just said.

    Needs at least 3 words, so a short real answer that happens to reuse a
    word from the question ("tiring" after "good or tiring?") still counts.
    """
    heard_words, said_words = _words(heard), set(_words(last_said))
    if len(heard_words) < 3 or not said_words:
        return False
    overlap = sum(w in said_words for w in heard_words) / len(heard_words)
    return overlap >= 0.6


def log_turn(heard: str, said: str | None, state: str) -> None:
    """One row per turn, so the transcripts can be read back later."""
    new = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="") as handle:
        writer = csv.writer(handle)
        if new:
            writer.writerow(["time", "state", "heard", "said"])
        writer.writerow([datetime.now().isoformat(timespec="seconds"), state,
                         heard, said or ""])


def act(machine, response, screen, speak) -> None:
    """Demo-mode version: show the reply, say it, then show the waiting state."""
    if response.say:
        screen.show(response.led, response.say, response.heard_text,
                    machine.state, response.animal or machine.animal)
        speak(response.say, response.animal)
        log_turn(response.heard_text, response.say, machine.state)
    screen.show(machine.led, machine.screen, "", machine.state, machine.animal)


def run_demo(args) -> None:
    """Typed input instead of a microphone: same rules, no hardware."""
    machine = PetMachine(brain=make_brain(args.brain, args.llm_model, args.llm_url))
    screen = Screen()

    def speak(text, animal=None):
        print(f'  PET ({animal or "-"}): "{text}"')

    print('Type what you would say. "b" = press the button, "" = silence, "q" = quit.')
    screen.show(machine.led, machine.screen)
    while True:
        try:
            line = input("you> ").strip()
        except EOFError:
            return
        if line == "q":
            return
        if line == "b":
            act(machine, machine.press(), screen, speak)
        elif line == "":
            act(machine, machine.nothing_heard(), screen, speak)
        else:
            act(machine, machine.hear(line), screen, speak)


def run_on_pi(args) -> None:
    import numpy as np
    import sherpa_onnx
    import sounddevice as sd
    from faster_whisper import WhisperModel

    for path, what in [(args.vad_model, "VAD model"), (args.voice, "Piper voice")]:
        if not path.is_file():
            sys.exit(f"{what} not found at {path}. Run speech-scripts/setup.sh first.")

    print("Loading models...", flush=True)
    recognizer = WhisperModel(args.model, device="cpu", compute_type="int8")
    speaker = Speaker(args.voice)
    screen, button, knob = Screen(), Button(), Knob()
    screen.led_hook = knob.set_led
    machine = PetMachine(brain=make_brain(args.brain, args.llm_model, args.llm_url))

    config = sherpa_onnx.VadModelConfig()
    config.silero_vad.model = str(args.vad_model)
    config.silero_vad.min_silence_duration = args.min_silence
    config.sample_rate = SAMPLE_RATE
    vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
    window = config.silero_vad.window_size

    screen.show(machine.led, SLEEP_SCREEN)
    print(f"Ready. Press the knob or button A to start "
          f"(endpointing after {args.min_silence}s).\n")
    try:
        _listen_loop(args, machine, screen, button, knob, recognizer, speaker,
                     vad, window, np, sd)
    finally:
        knob.set_led("off")       # do not leave the LED glowing after Ctrl+C


def _listen_loop(args, machine, screen, button, knob, recognizer, speaker,
                 vad, window, np, sd) -> None:

    buffer = np.empty(0, dtype=np.float32)
    samples_per_read = int(0.1 * SAMPLE_RATE)
    ignore_until = 0.0        # audio recorded before this time is the pet itself
    last_said, spoke_at = "", 0.0

    with sd.InputStream(channels=1, dtype="float32", samplerate=SAMPLE_RATE) as stream:

        def respond(response) -> None:
            """Speak, then ignore the microphone briefly.

            The microphone sits next to the speaker, so the audio recorded
            while the pet talks is thrown away instead of transcribed;
            otherwise the pet answers its own voice. The stream keeps running
            throughout: stopping and restarting it left some devices deaf.
            """
            nonlocal buffer, ignore_until, last_said, spoke_at
            if response.say:
                screen.show(response.led, response.say, response.heard_text,
                            machine.state, response.animal or machine.animal)
                try:
                    t2 = time.perf_counter()
                    speaker.say(response.say, response.animal)
                    print(f"  spoke in {time.perf_counter() - t2:.2f}s")
                    log_turn(response.heard_text, response.say, machine.state)
                finally:
                    # Audio recorded while it was talking is still queued in
                    # the input stream: read it out and throw it away.
                    try:
                        queued = stream.read_available
                        if queued:
                            stream.read(queued)
                    except Exception:
                        pass
                    ignore_until = time.monotonic() + args.echo_guard
                    last_said, spoke_at = response.say, time.monotonic()
                    buffer = np.empty(0, dtype=np.float32)
                    while not vad.empty():
                        vad.pop()
                    if hasattr(vad, "reset"):
                        vad.reset()       # forget a half-detected echo
            screen.show(machine.led, machine.screen, "", machine.state,
                        machine.animal)

        last_meter = 0.0
        while True:
            chunk, _ = stream.read(samples_per_read)

            if args.debug:
                # Once a second: is the mic alive, and what state are we in?
                level = float(np.abs(chunk).mean())
                if time.monotonic() - last_meter > 1.0:
                    last_meter = time.monotonic()
                    bar = "#" * min(30, int(level * 600))
                    muted = " (ignoring: pet is talking)" if time.monotonic() < ignore_until else ""
                    print(f"  [debug] {machine.state:8} mic {level:.4f} |{bar}{muted}")

            # Read both every loop so each one keeps track of its own release.
            clicked_a, clicked_knob = button.pressed(), knob.pressed()
            if clicked_a or clicked_knob:
                print("  [knob]" if clicked_knob else "  [button]")
                respond(machine.press())
                continue

            if machine.state == "ASLEEP":
                continue          # not listening until the button is pressed

            if time.monotonic() < ignore_until:
                continue          # this is the pet's own voice, not yours

            buffer = np.concatenate([buffer, chunk.reshape(-1)])
            while len(buffer) > window:
                vad.accept_waveform(buffer[:window])
                buffer = buffer[window:]

            while not vad.empty():
                utterance = np.array(vad.front.samples, dtype=np.float32)
                vad.pop()
                if args.debug:
                    print(f"  [debug] VAD utterance: "
                          f"{len(utterance) / SAMPLE_RATE:.1f}s")

                screen.show("amber", machine.screen or "...", "",
                            machine.state, machine.animal)   # working
                t0 = time.perf_counter()
                segments, _ = recognizer.transcribe(utterance, beam_size=1)
                heard = " ".join(s.text.strip() for s in segments)
                print(f'  heard "{heard}" in {time.perf_counter() - t0:.2f}s')

                just_spoke = time.monotonic() - spoke_at < ECHO_WINDOW
                if is_own_echo(heard, last_said) or (not heard and just_spoke):
                    print("  (ignored: that was the pet's own voice)")
                    screen.show(machine.led, machine.screen, "", machine.state,
                                machine.animal)
                    continue

                t1 = time.perf_counter()
                response = machine.hear(heard) if heard else machine.nothing_heard()
                print(f"  reply chosen in {time.perf_counter() - t1:.2f}s")
                respond(response)


def main() -> None:
    # Never crash just because the terminal cannot print a character.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--demo", action="store_true",
                        help="type instead of speaking (no mic, screen or button)")
    parser.add_argument("--model", default="tiny.en", help="whisper model size")
    parser.add_argument("--vad-model", type=Path, default=DEFAULT_VAD)
    parser.add_argument("--voice", type=Path, default=DEFAULT_VOICE)
    parser.add_argument("--echo-guard", type=float, default=SELF_HEAR_GUARD,
                        help="seconds the mic is ignored after the pet speaks "
                             f"(default: {SELF_HEAR_GUARD}); raise it if the pet "
                             "still hears itself")
    parser.add_argument("--min-silence", type=float, default=0.8,
                        help="seconds of silence that end a turn (default: 0.8)")
    parser.add_argument("--brain", choices=["auto", "ollama", "off"], default="auto",
                        help="free conversation: use the local model if it is "
                             "running (auto), require it (ollama), or fixed "
                             "lines only (off)")
    parser.add_argument("--llm-model", default=DEFAULT_MODEL)
    parser.add_argument("--llm-url", default=DEFAULT_URL)
    parser.add_argument("--debug", action="store_true",
                        help="print the microphone level and state once a second")
    args = parser.parse_args()

    if args.demo:
        run_demo(args)
    else:
        run_on_pi(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")