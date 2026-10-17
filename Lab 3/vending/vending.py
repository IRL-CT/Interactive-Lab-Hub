#!/usr/bin/env python3
"""Voice vending machine using the Adafruit MiniPiTFT buttons.

GPIO23: next snack / NO during confirmation.
GPIO24: select snack / YES during confirmation.
Use --swap-buttons to reverse these assignments.

Run: python vending.py
Wizard-only recognition: python vending.py --woz
Keep the updated screens.py beside this file. Payments are simulated. Model paths are unchanged.
The wizard webpage remains available in both modes.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import logging
import queue
import re
import socket
import sys
import threading
import time
from pathlib import Path

import numpy as np

import screens

SAMPLE_RATE = 16000
LAB_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VAD = LAB_DIR / "models" / "silero_vad.onnx"
DEFAULT_VOICE = LAB_DIR / "voices" / "en_US-lessac-medium.onnx"
LOG_PATH = Path(__file__).resolve().parent / "interaction_log.csv"

SPOKEN = {"Chips": "chips", "Cookies": "cookies", "Candy Bar": "candy bar", "Soda": "soda"}
PLURAL = {"Chips", "Cookies"}

YES_WORDS = {"yes", "yeah", "yep", "yup", "ya", "yea", "sure", "ok", "okay", "correct",
             "definitely", "absolutely", "please", "affirmative", "mhm", "uh-huh"}
NO_WORDS = {"no", "nope", "nah", "cancel", "don't", "dont", "negative", "nevermind"}
NO_PHRASES = ("not really", "never mind", "something else", "another one", "go back")


def parse_yes_no(text: str) -> str | None:
    """'yeah sure' -> yes, 'actually no' -> no, 'thank you' -> None."""
    lowered = text.lower()
    words = set(re.findall(r"[a-z'-]+", lowered))
    if words & NO_WORDS or any(p in lowered for p in NO_PHRASES):
        return "no"
    if words & YES_WORDS or "i do" in lowered or "i'll take" in lowered:
        return "yes"
    return None


# Demo prices, in cents. No real payment is processed.
PRICES = {name: 200 for name in screens.ITEMS}
DIGIT_WORDS = dict(zip("zero one two three four five six seven eight nine".split(), "0123456789"))
DIGIT_WORDS["oh"] = "0"
SMALL = dict(zip("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split(), range(20)))
TENS = dict(zip("twenty thirty forty fifty sixty seventy eighty ninety".split(), range(20, 100, 10)))


def parse_card(text):
    text = text.lower().strip().rstrip(".!?")
    text = re.sub(r"^(?:my card number is|the card number is|my number is|it is|it's)\s+", "", text)
    if text.startswith("-") or "_" in text:
        return None
    tokens = re.findall(r"[a-z]+|[0-9]+|[^\w\s,-]", text)
    digits = ""
    for token in tokens:
        if re.fullmatch(r"[0-9]+", token):
            digits += token
        elif token in DIGIT_WORDS:
            digits += DIGIT_WORDS[token]
        else:
            return None
    return digits if len(digits) == 4 and digits != "0000" else None


def spoken_integer(text):
    words = text.replace("-", " ").strip().split()
    if not words:
        return None
    if len(words) == 1:
        if words[0].isdigit():
            return int(words[0])
        return SMALL.get(words[0], TENS.get(words[0]))
    if len(words) == 2 and words[0] in TENS and words[1] in SMALL and 0 < SMALL[words[1]] < 10:
        return TENS[words[0]] + SMALL[words[1]]
    if "hundred" in words:
        i = words.index("hundred")
        if i != 1 or words[0] not in SMALL or not 1 <= SMALL[words[0]] <= 9:
            return None
        rest = words[2:]
        if rest and rest[0] == "and":
            rest = rest[1:]
        tail = spoken_integer(" ".join(rest)) if rest else 0
        if tail is not None and tail < 100:
            return SMALL[words[0]] * 100 + tail
    return None


def parse_cash(text):
    """Return nonnegative integer cents; reject ambiguous/negative amounts."""
    text = text.lower().strip().rstrip(".!?")
    text = re.sub(r"^(?:i have|i've got|i have got|i've|i got|it is|it's)\s+", "", text)
    text = re.sub(r"\s+(?:in cash|cash)$", "", text)
    if "-" in text and re.search(r"-\s*[0-9]", text):
        return None
    # Numeric dollars: 2, $2.50, 2.50 dollars. No rounding invalid precision.
    match = re.fullmatch(r"\$?([0-9]+(?:\.[0-9]{1,2})?)(?:\s+dollars?)?", text)
    if match:
        return int(Decimal(match.group(1)) * 100)
    # Spoken decimal, e.g. 'two point five zero'.
    if " point " in text:
        whole, fraction = text.removesuffix(" dollars").removesuffix(" dollar").split(" point ", 1)
        dollars = spoken_integer(whole)
        parts = fraction.split()
        digits = "".join(DIGIT_WORDS.get(w, w if w.isdigit() else "?") for w in parts)
        if dollars is not None and re.fullmatch(r"[0-9]{1,2}", digits):
            return dollars * 100 + int(digits.ljust(2, "0"))
        return None
    match = re.fullmatch(r"(.+?) dollars?(?:\s+(?:and\s+)?(.+?) cents?)?", text)
    if match:
        dollars = spoken_integer(match.group(1))
        cents = spoken_integer(match.group(2)) if match.group(2) else 0
        if dollars is not None and cents is not None and 0 <= cents < 100:
            return dollars * 100 + cents
        return None
    if text.endswith((" cent", " cents")):
        return spoken_integer(re.sub(r" cents?$", "", text))
    dollars = spoken_integer(text)
    return dollars * 100 if dollars is not None else None


def parse_method(text):
    words = set(re.findall(r"[a-z]+", text.lower()))
    cash = "cash" in words
    card = bool(words & {"card", "credit", "debit"})
    return ("cash" if cash else "card") if cash != card else None


# Adapt the original artwork without requiring an edited screens.py.
def browse_screen(index, selected=False, status="BROWSE"):
    img = screens.browse(index, selected=selected, status=status)
    screens._status_bar(screens.ImageDraw.Draw(img), status,
                        f"${PRICES[screens.ITEMS[index]] / 100:.2f}  NEXT/SEL")
    return img


def confirm_screen(index, status, heard=""):
    img = screens.confirm(index, status, heard)
    screens._status_bar(screens.ImageDraw.Draw(img), status, "NEXT=no SEL=yes")
    return img


def dispense_frames(index):
    frames = screens.dispense_frames(index)
    screens._status_bar(screens.ImageDraw.Draw(frames[-1]), "ENJOY", "NEXT for more")
    return frames


# --- hardware ---------------------------------------------------------------

class Screen:
    """The Adafruit MiniPiTFT (ST7789, 240x135), same setup as Lab 2."""

    def __init__(self) -> None:
        self.disp = None
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
            print(f"[warn] screen not available ({e}); continuing without it")

    def show(self, image) -> None:
        if self.disp:
            self.disp.image(image, 90)


class Buttons:
    """Active-low MiniPiTFT buttons, with debounce and no hold-to-repeat."""

    DEBOUNCE = 0.04

    def __init__(self, swap: bool = False) -> None:
        self.pins = []
        self.events = ("press", "next") if swap else ("next", "press")
        try:
            import board
            import digitalio

            for pin in (board.D23, board.D24):
                button = digitalio.DigitalInOut(pin)
                self.pins.append(button)
                button.switch_to_input(pull=digitalio.Pull.UP)
            self.sync()
            print("Buttons: GPIO23 = " + self.events[0] +
                  "; GPIO24 = " + self.events[1])
        except Exception as e:
            self.close()
            print(f"[warn] screen buttons unavailable ({e}); use the wizard page")

    def sync(self) -> None:
        # Ignore buttons already held when entering a new interaction stage.
        self.raw = [not pin.value for pin in self.pins]
        self.stable = self.raw.copy()
        self.changed = [time.monotonic()] * len(self.pins)

    def poll(self) -> str | None:
        now = time.monotonic()
        events = []
        for i, pin in enumerate(self.pins):
            pressed = not pin.value
            if pressed != self.raw[i]:
                self.raw[i] = pressed
                self.changed[i] = now
            if pressed != self.stable[i] and now - self.changed[i] >= self.DEBOUNCE:
                self.stable[i] = pressed
                if pressed:
                    events.append(self.events[i])
        # Ignore simultaneous presses instead of accidentally selecting an item.
        return events[0] if len(events) == 1 else None

    def close(self) -> None:
        for pin in self.pins:
            pin.deinit()
        self.pins = []


class Led:
    """The LED inside the Qwiic Button (0x6F): solid = listening, pulsing = thinking."""

    def __init__(self) -> None:
        self.dev = None
        try:
            import board
            import busio
            from adafruit_bus_device.i2c_device import I2CDevice

            self.dev = I2CDevice(busio.I2C(board.SCL, board.SDA), 0x6F)
            self.off()
        except Exception as e:
            print(f"[warn] Qwiic Button LED not available ({e}); screen only")

    def _write(self, register: int, value: int, n_bytes: int = 1) -> None:
        buf = bytearray(1 + n_bytes)
        buf[0] = register
        buf[1:] = value.to_bytes(n_bytes, "little")
        with self.dev:
            self.dev.write(buf)

    def _config(self, brightness: int, cycle_ms: int = 0, off_ms: int = 0) -> None:
        if not self.dev:
            return
        try:
            self._write(0x1A, 1)               # pulse granularity
            self._write(0x1B, cycle_ms, 2)     # pulse cycle time
            self._write(0x1D, off_ms, 2)       # pulse off time
            self._write(0x19, brightness)      # brightness
        except OSError:
            pass

    def on(self) -> None:
        self._config(255)

    def pulse(self) -> None:
        self._config(255, cycle_ms=600, off_ms=100)

    def off(self) -> None:
        self._config(0)


class Speaker:
    """Piper TTS, same as echo_bot.py. Falls back to printing if Piper is missing."""

    def __init__(self, voice_path: Path) -> None:
        self.voice = None
        try:
            from piper import PiperVoice
            import sounddevice as sd

            self.sd = sd
            self.voice = PiperVoice.load(str(voice_path))
        except Exception as e:
            print(f"[warn] Piper TTS not available ({e}); printing speech instead")

    def say(self, text: str) -> None:
        print(f"  machine: {text}")
        if not self.voice:
            return
        for chunk in self.voice.synthesize(text):
            audio = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            self.sd.play(audio, samplerate=chunk.sample_rate)
            self.sd.wait()


class Ears:
    """Silero VAD + faster-whisper, same pipeline as listen.py, used one turn at a time."""

    def __init__(self, model: str, vad_path: Path, min_silence: float) -> None:
        import sherpa_onnx
        import sounddevice as sd
        from faster_whisper import WhisperModel

        self.sd = sd
        self.recognizer = WhisperModel(model, device="cpu", compute_type="int8")
        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = str(vad_path)
        config.silero_vad.min_silence_duration = min_silence
        config.silero_vad.min_speech_duration = 0.15   # "no" is short
        config.sample_rate = SAMPLE_RATE
        self.vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
        self.window = config.silero_vad.window_size

    def listen(self, timeout: float, interrupt, on_thinking, parser=parse_yes_no):
        """Listens for one yes/no answer.

        interrupt() is checked every 0.1 s and can end listening early (buttons
        or wizard). Returns (answer, heard) where answer is 'yes', 'no', None for
        unclear/silence, or whatever interrupt() returned.
        """
        self.vad.reset()
        buffer = np.empty(0, dtype=np.float32)
        deadline = time.monotonic() + timeout
        heard = ""
        with self.sd.InputStream(channels=1, dtype="float32", samplerate=SAMPLE_RATE) as stream:
            while time.monotonic() < deadline:
                early = interrupt()
                if early:
                    return early
                chunk, _ = stream.read(int(0.1 * SAMPLE_RATE))
                buffer = np.concatenate([buffer, chunk.reshape(-1)])
                while len(buffer) > self.window:
                    self.vad.accept_waveform(buffer[:self.window])
                    buffer = buffer[self.window:]
                if self.vad.is_speech_detected():
                    deadline = max(deadline, time.monotonic() + 1.0)  # don't cut them off
                while not self.vad.empty():
                    utterance = np.array(self.vad.front.samples, dtype=np.float32)
                    self.vad.pop()
                    on_thinking()
                    segments, _ = self.recognizer.transcribe(utterance, beam_size=1)
                    heard = " ".join(s.text.strip() for s in segments).strip()
                    print(f"  heard: {heard!r}")
                    if heard:
                        return parser(heard), heard
        return None, heard


# --- the interaction --------------------------------------------------------

class VendingMachine:
    def __init__(self, args) -> None:
        self.args = args
        self.screen = Screen()
        self.buttons = Buttons(args.swap_buttons)
        self.led = Led()
        self.speaker = Speaker(args.voice)
        self.ears = None
        if not args.woz:
            try:
                print("Loading Whisper + VAD...", flush=True)
                self.ears = Ears(args.model, args.vad_model, args.min_silence)
            except Exception as e:
                print(f"[warn] speech recognition not available ({e}); "
                      "answer yes/no from the wizard page")

        self.index = 0
        self.commands: queue.Queue = queue.Queue()   # filled by the wizard page
        self.status = {"state": "BROWSE", "item": screens.ITEMS[0], "heard": "",
                       "mode": "woz" if self.ears is None else "auto", "stage": "browse", "price": "2"}
        new_log = not LOG_PATH.exists()
        self._log_file = LOG_PATH.open("a", newline="")
        self._log = csv.writer(self._log_file)
        if new_log:
            self._log.writerow(["time", "state", "item", "event", "source", "detail"])

    # helpers

    @property
    def item(self) -> str:
        return screens.ITEMS[self.index]

    def log(self, event: str, source: str = "", detail: str = "") -> None:
        self._log.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), self.status["state"],
                            self.item, event, source, detail])
        self._log_file.flush()

    def set_state(self, state: str, image) -> None:
        self.status.update(state=state, item=self.item, price=f"{PRICES[self.item] / 100:.2f}")
        if state == "BROWSE":
            self.status["stage"] = "browse"
        self.screen.show(image)

    def speak(self, text: str, image) -> None:
        self.led.off()
        self.set_state("TALKING", image)
        self.log("say", "machine", text)
        self.speaker.say(text)
        self.buttons.sync()

    def poll(self):
        """One non-blocking check of the buttons and the wizard page.

        Returns (event, source, payload) or None. Events: prev, next, press,
        yes, no, say.
        """
        js = self.buttons.poll()
        if js:
            return js, "button", ""
        try:
            cmd, payload = self.commands.get_nowait()
        except queue.Empty:
            return None
        return cmd, "wizard", payload

    # states

    def run(self) -> None:
        self.speak("Hi! Press the next button to browse snacks, and the select button to pick one.",
                   browse_screen(self.index, status="TALKING"))
        self.set_state("BROWSE", browse_screen(self.index))
        while True:
            got = self.poll()
            if not got:
                time.sleep(0.02)
                continue
            event, source, payload = got
            if event == "answer":
                continue
            self.log(event, source, payload)
            if event in ("prev", "next"):
                self.index = (self.index + (1 if event == "next" else -1)) % len(screens.ITEMS)
                self.set_state("BROWSE", browse_screen(self.index))
            elif event == "press":
                self.offer()
            elif event == "say":
                self.speak(payload, browse_screen(self.index, status="TALKING"))
                self.set_state("BROWSE", browse_screen(self.index))

    def offer(self) -> None:
        self.speak(f"You picked {SPOKEN[self.item]}. Do you want this one?",
                   browse_screen(self.index, selected=True, status="TALKING"))
        self.status["stage"] = "confirm"
        for attempt in range(2):
            answer, heard = self.ask()
            self.log(f"answer:{answer}", "", heard)
            if answer == "yes":
                return self.payment()
            if answer == "no":
                self.speak("No problem. Press the next button to browse the other snacks.",
                           browse_screen(self.index, status="TALKING"))
                self.set_state("BROWSE", browse_screen(self.index))
                return
            if attempt == 0:
                self.speak("Sorry, I didn't catch that. Say yes or no, "
                           "or press the select button to take it.",
                           confirm_screen(self.index, "TALKING", heard))
        self.speak("No worries, take your time. Press a button when you're ready.",
                   browse_screen(self.index, status="TALKING"))
        self.set_state("BROWSE", browse_screen(self.index))

    def ask(self):
        """Listens for yes/no. Select button = yes, next button = no."""
        while True:
            self.buttons.sync()
            self.set_state("LISTENING", confirm_screen(self.index, "LISTENING"))
            self.status["heard"] = ""
            self.led.on()

            def interrupt():
                got = self.poll()
                if not got:
                    return None
                event, source, payload = got
                if event == "press":
                    return "yes", f"[{source} press]"
                if event in ("prev", "next"):
                    return "no", f"[{source} next]"
                if event in ("yes", "no"):
                    return event, f"[{source}]"
                if event == "say":
                    return "say", payload
                return None

            def thinking():
                self.led.pulse()
                self.set_state("THINKING", confirm_screen(self.index, "THINKING"))

            if self.ears:
                answer, heard = self.ears.listen(self.args.listen_timeout, interrupt, thinking)
            else:
                answer, heard = self._wait_for(interrupt, self.args.listen_timeout)
            self.led.off()
            self.status["heard"] = heard
            if answer != "say":
                return answer, heard
            self.speak(heard, confirm_screen(self.index, "TALKING"))   # wizard spoke

    @staticmethod
    def _wait_for(interrupt, timeout: float):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            got = interrupt()
            if got:
                return got
            time.sleep(0.02)
        return None, ""

    def payment_view(self, stage, status="LISTENING"):
        return screens.payment(self.index, PRICES[self.item], stage, status)

    def payment_input(self, stage):
        """Receive one spoken or typed answer. NEXT cancels numeric entry."""
        self.status.update(stage=stage, heard="")
        self.buttons.sync()
        self.set_state("LISTENING", self.payment_view(stage))
        self.led.on()

        def interrupt():
            got = self.poll()
            if not got:
                return None
            event, source, payload = got
            if event == "answer":
                target, text = payload
                if target == stage:
                    return text, text
            if event == "cancel":
                return "__cancel__", ""
            if stage == "method":
                if event in ("next", "prev", "cash"):
                    return "cash", "cash"
                if event in ("press", "card"):
                    return "card", "card"
            elif event in ("next", "prev"):
                return "__cancel__", ""
            return None

        def thinking():
            self.led.pulse()
            self.set_state("THINKING", self.payment_view(stage, "THINKING"))

        try:
            if self.ears:
                answer, heard = self.ears.listen(self.args.payment_timeout, interrupt, thinking,
                                                parser=lambda text: text)
            else:
                answer, heard = self._wait_for(interrupt, self.args.payment_timeout)
        finally:
            self.led.off()
        # Do not retain entered card digits in the web status or CSV.
        self.status["heard"] = "[card entry]" if stage == "card" else heard
        return answer or ""

    def payment_fail(self, message):
        self.log("payment_failed", "machine", message)
        self.speak(message, self.payment_view("failed", "TALKING"))
        self.set_state("BROWSE", browse_screen(self.index))

    def payment(self):
        price = PRICES[self.item]
        self.status["stage"] = "method"
        self.speak(f"That costs {price / 100:.2f} dollars. Cash or card?",
                   self.payment_view("method", "TALKING"))
        method = None
        for attempt in range(2):
            reply = self.payment_input("method")
            if reply == "__cancel__" or reply.lower().strip(" .!?") in ("cancel", "go back"):
                return self.payment_fail("Payment cancelled.")
            method = parse_method(reply)
            if method:
                break
            if attempt == 0:
                self.speak("Please say cash or card. Or press next for cash, select for card.",
                           self.payment_view("method", "TALKING"))
        if not method:
            return self.payment_fail("I didn't catch the payment method. Please select a snack again.")

        self.status["stage"] = method
        if method == "card":
            self.speak("Give me a four digit card number.",
                       self.payment_view("card", "TALKING"))
            reply = self.payment_input("card")
            if reply == "__cancel__" or reply.lower().strip(" .!?") in ("cancel", "go back"):
                return self.payment_fail("Payment cancelled.")
            if parse_card(reply) is None:
                return self.payment_fail("Incorrect card number.")
        else:
            self.speak("How much cash do you have?", self.payment_view("cash", "TALKING"))
            reply = self.payment_input("cash")
            if reply == "__cancel__" or reply.lower().strip(" .!?") in ("cancel", "go back"):
                return self.payment_fail("Payment cancelled.")
            amount = parse_cash(reply)
            if amount is None:
                return self.payment_fail("I couldn't understand the cash amount. Please select a snack again.")
            if amount < price:
                return self.payment_fail("Insufficient funds.")
        self.log("payment_accepted", method, "simulated")
        self.status["stage"] = "dispense"
        self.dispense()

    def dispense(self) -> None:
        name = self.item
        line = f"Here {'are' if name in PLURAL else 'is'} your {SPOKEN[name]}. Enjoy!"
        self.status.update(state="ENJOY", item=name)
        self.log("say", "machine", line)
        voice = threading.Thread(target=self.speaker.say, args=(line,))
        for k, frame in enumerate(dispense_frames(self.index)):
            if k == 16:          # start talking as it flies out
                voice.start()
            self.screen.show(frame)
            time.sleep(0.05)
        voice.join()
        time.sleep(1.0)
        self.speak("Want anything else? Press the next button to browse.",
                   dispense_frames(self.index)[-1])
        self.set_state("BROWSE", browse_screen(self.index))


# --- wizard controller ------------------------------------------------------

WIZARD_PAGE = """<!doctype html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vending Wizard</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:480px;margin:16px auto;padding:0 16px;background:#12121c;color:#eee}
 h1{font-size:20px} .row{display:flex;gap:8px;margin:10px 0}
 button{flex:1;padding:16px;font-size:18px;border:0;border-radius:10px;background:#333;color:#eee}
 .yes{background:#1e8a46}.no{background:#a83232}.sel{background:#b8860b}
 input{flex:3;padding:12px;font-size:16px;border-radius:10px;border:0}
 #st{background:#222;padding:12px;border-radius:10px;font-family:monospace;white-space:pre}
</style></head><body>
<h1>Vending machine wizard</h1>
<p>Simulated payments only. Use a made-up four-digit number.</p>
<div id="st">connecting...</div>
<div class="row"><button onclick="c('prev')">&#9664;</button>
 <button class="sel" onclick="c('press')">Select</button>
 <button onclick="c('next')">&#9654;</button></div>
<div class="row"><button class="yes" onclick="c('yes')">YES</button>
 <button class="no" onclick="c('no')">NO</button></div>
<div class="row"><button onclick="answerText('cash')">Cash</button><button onclick="answerText('card')">Card</button><button onclick="c('cancel')">Cancel</button></div>
<div class="row"><input id="answer" placeholder="Payment answer: 1234 or 2 dollars"><button onclick="submitAnswer()">Answer</button></div>
<div class="row"><input id="t" placeholder="Make the machine say..."><button onclick="say()">Say</button></div>
<div class="row">
 <button onclick="sayText('Sorry, could you say that again?')">Repeat?</button>
 <button onclick="sayText('Press the next button to see more snacks.')">Hint</button>
</div>
<script>
let currentStage = 'browse';
function answerText(text){fetch('/answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,stage:currentStage})})}
function submitAnswer(){const t=document.getElementById('answer');if(t.value){answerText(t.value);t.value=''}}
document.getElementById('answer').addEventListener('keydown',e=>{if(e.key==='Enter')submitAnswer()});
function c(x){fetch('/cmd/'+x,{method:'POST'})}
function sayText(s){fetch('/say',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:s})})}
function say(){const t=document.getElementById('t');if(t.value){sayText(t.value);t.value=''}}
document.getElementById('t').addEventListener('keydown',e=>{if(e.key==='Enter')say()});
setInterval(async()=>{try{const s=await (await fetch('/state')).json(); currentStage=s.stage;
 document.getElementById('st').textContent='mode:  '+s.mode+'\\nstate: '+s.state+'\\nstage: '+s.stage+'\\nprice: $'+s.price+'\\nitem:  '+s.item+'\\nheard: '+(s.heard||'-')}catch(e){}},400);
</script></body></html>"""


def start_wizard(machine: VendingMachine, port: int) -> None:
    from flask import Flask, jsonify, request

    app = Flask(__name__)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    @app.get("/")
    def index():
        return WIZARD_PAGE

    @app.get("/state")
    def state():
        return jsonify(machine.status)

    @app.post("/cmd/<name>")
    def cmd(name):
        if name in ("prev", "next", "press", "yes", "no", "cancel"):
            machine.commands.put((name, ""))
        return "", 204

    @app.post("/answer")
    def answer():
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        stage = data.get("stage", "")
        if not isinstance(text, str) or stage not in ("method", "card", "cash"):
            return "Invalid answer", 400
        if machine.status["stage"] != stage or machine.status["state"] != "LISTENING":
            return "Wait for the payment question", 409
        machine.commands.put(("answer", (stage, text.strip()[:200])))
        return "", 204

    @app.post("/say")
    def say():
        text = (request.get_json(silent=True) or {}).get("text", "").strip()
        if text:
            machine.commands.put(("say", text))
        return "", 204

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, threaded=True),
                     daemon=True).start()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except OSError:
        ip = "<pi-ip>"
    print(f"Wizard controller: http://{ip}:{port}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--woz", action="store_true",
                        help="skip Whisper; a wizard answers yes/no from the web page")
    parser.add_argument("--swap-buttons", action="store_true",
                        help="swap the next and select buttons")
    parser.add_argument("--model", default="tiny.en", help="whisper model size")
    parser.add_argument("--vad-model", type=Path, default=DEFAULT_VAD)
    parser.add_argument("--voice", type=Path, default=DEFAULT_VOICE)
    parser.add_argument("--min-silence", type=float, default=0.6,
                        help="seconds of silence that end an answer (default: 0.6)")
    parser.add_argument("--listen-timeout", type=float, default=None,
                        help="seconds to wait for yes/no (default: 6, or 20 with --woz)")
    parser.add_argument("--payment-timeout", type=float, default=15.0,
                        help="seconds to wait for each payment answer (default: 15)")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    if args.listen_timeout is None:
        args.listen_timeout = 20.0 if args.woz else 6.0

    for path, what in [(args.vad_model, "VAD model"), (args.voice, "Piper voice")]:
        if not path.is_file():
            print(f"[warn] {what} not found at {path}. Run speech-scripts/setup.sh first.")

    machine = VendingMachine(args)
    start_wizard(machine, args.port)
    print("Ready. Ctrl-C to stop.\n")
    try:
        machine.run()
    finally:
        machine.led.off()
        machine.buttons.close()
        machine._log_file.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)