#!/usr/bin/env python3
#this code was based off echo_bot.py and troubledshooted w/ ChatGPT
import argparse
import sys
import time
from pathlib import Path

import busio
import adafruit_mpr121

import random

import soundfile as sf

import numpy as np
import sherpa_onnx
import sounddevice as sd
from faster_whisper import WhisperModel, audio
from piper import PiperVoice

from PIL import Image, ImageDraw, ImageFont
import board
import digitalio
import adafruit_rgb_display.st7789 as st7789
# DISPLAY SETUP

cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

spi = board.SPI()

disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=64000000,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

WIDTH = 240
HEIGHT = 135

font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    24
)

def screen_text(text):
    screen = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        "black"
    )

    draw = ImageDraw.Draw(screen)

    # Load font
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        20
    )

    # Split text into words
    words = text.split()

    lines = []
    current_line = ""

    # Make lines fit the screen
    for word in words:
        test_line = current_line + " " + word

        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= WIDTH - 20:
            current_line = test_line.strip()
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    # Calculate total height
    line_height = 25
    total_height = len(lines) * line_height

    # Starting y position
    y = (HEIGHT - total_height) // 2

    # Draw each line
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]

        x = (WIDTH - text_width) // 2

        draw.text(
            (x, y),
            line,
            font=font,
            fill="white"
        )

        y += line_height

    # Rotate for the PiTFT
    screen = screen.rotate(90, expand=True)

    disp.image(screen)

# ============================================================
# MPR121 SENSOR SETUP
# ============================================================
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)


SAMPLE_RATE = 16000
LAB_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VAD = LAB_DIR / "models" / "silero_vad.onnx"
DEFAULT_VOICE = LAB_DIR / "voices" / "en_US-lessac-medium.onnx"

# ============================================================
# FORTUNE LISTS
# ============================================================
school_fortunes = [
    "You will have a surprisingly good day at school.",
    "A friend may help you with something important.",
    "You are going to learn something interesting soon.",
    "A challenging assignment will turn out better than expected.",
    "Something unexpected will make your school day more exciting."
]

career_fortunes = [
    "A new opportunity may be coming your way.",
    "Your hard work will start to get noticed.",
    "You may discover a career path you had not considered.",
    "Someone may give you useful advice about your future.",
    "You will have a chance to show what you can do."
]

random_fortunes = [
    "Something unexpected will happen soon.",
    "You may meet someone who makes you smile.",
    "A small decision could lead to an interesting adventure.",
    "Good luck may find you when you aren't looking for it.",
    "Your next adventure may be closer than you think."
]

class Speaker:
    """Synthesizes with Piper and plays through the default output device."""
    def __init__(self, voice_path: Path) -> None:
        self.voice = PiperVoice.load(str(voice_path))

    def say(self, text: str) -> float:
        """Speaks the text. Returns seconds until the first audio was ready."""
        t0 = time.perf_counter()
        first_audio_at = None
        for chunk in self.voice.synthesize(text):
            audio = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            if first_audio_at is None:
                first_audio_at = time.perf_counter() - t0
            sd.play(audio, samplerate=chunk.sample_rate)
            sd.wait()
        return first_audio_at or 0.0

def listen():
    print("Listening...")

    buffer = np.empty(0, dtype=np.float32)
    samples_per_read = int(0.1 * SAMPLE_RATE)

    with sd.InputStream(channels=1, dtype="float32", samplerate=SAMPLE_RATE) as stream:

        while True:
            chunk, _ = stream.read(samples_per_read)

            buffer = np.concatenate([
                buffer,
                chunk.reshape(-1)
            ])

            while len(buffer) > window:
                vad.accept_waveform(buffer[:window])
                buffer = buffer[window:]

            while not vad.empty():
                utterance = np.array(
                    vad.front.samples,
                    dtype=np.float32
                )

                vad.pop()

                segments, _ = recognizer.transcribe(
                    utterance,
                    beam_size=1
                )

                heard = " ".join(
                    s.text.strip()
                    for s in segments
                )

                if heard:
                    print("You said:", heard)
                    return heard.lower()

def main() -> None:
    global recognizer
    global vad
    global window

    screen_text("Welcome to iFortune!")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="tiny.en", help="whisper model size (default: tiny.en)")
    parser.add_argument("--vad-model", type=Path, default=DEFAULT_VAD)
    parser.add_argument("--voice", type=Path, default=DEFAULT_VOICE)
    parser.add_argument("--min-silence", type=float, default=0.4,help="seconds of silence that end your turn (default: 0.4)")
    args = parser.parse_args()

    for path, what in [(args.vad_model, "VAD model"), (args.voice, "Piper voice")]:
        if not path.is_file():
            sys.exit(f"{what} not found at {path}. Run ./setup.sh first.")

    print("Loading models...", flush=True)
    recognizer = WhisperModel(args.model, device="cpu", compute_type="int8")
    speaker = Speaker(args.voice)

    config = sherpa_onnx.VadModelConfig()
    config.silero_vad.model = str(args.vad_model)
    config.silero_vad.min_silence_duration = args.min_silence
    config.sample_rate = SAMPLE_RATE
    vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
    window = config.silero_vad.window_size

    while True:
        #INTRO
        print("ABOUT TO SPEAK")
        screen_text("Choose a topic")
        speaker.say("Welcome to iFortune! Would you like your fortune to be about school, career, or a random topic?")
        heard = listen()

        # ============================================================
        # TOPIC CHOICE
        # ============================================================
        while True:
            if "school" in heard:
                topic = "school"
                break
            elif "career" in heard:
                topic = "career"
                break
            elif "random" in heard:
                topic = "random"
                break
            else:
                speaker.say("Sorry, I didn't catch that. Please say school, career, or random.")
                heard = listen()
        
        # ============================================================
        # NUMBER SELECTION WITH MPR121 SENSOr
        # ============================================================
        screen_text("Pick a number from 1 to 10")
        speaker.say("Great! Let's get started. Pick a number from one to ten.")

        while True:
            for i in range(10):
                if mpr121[i].value:
                    number = i + 1

                    print("Selected number:", number)

                    # Wait for the person to release the pad
                    while mpr121[i].value:
                        time.sleep(0.05)
                    break
            else:
                continue

            break

        # ============================================================
        # COLORS
        # ============================================================
        screen_text("Pick a color from the rainbow.")
        speaker.say("Good choice. Now pick a color from the rainbow.")

        while True:
            color = listen()
            if "red" in color:
                color = "red"
                break
            elif "orange" in color:
                color = "orange"
                break
            elif "yellow" in color:
                color = "yellow"
                break
            elif "green" in color:
                color = "green"
                break
            elif "blue" in color:
                color = "blue"
                break
            elif "purple" in color:
                color = "purple"
                break
            else:
                speaker.say("Sorry. Please choose a color from red, orange, yellow, green, blue, or purple.")

        # ============================================================
        # GIVING THE FORTUNE
        # ============================================================
        screen_text("Fortune loading...")
        speaker.say("Nice! Now focus on your future so that I can get your fortune!")

        time.sleep(3)
        audio, sample_rate = sf.read("fortune_complete.wav")
        sd.play(audio, sample_rate)
        sd.wait()

        screen_text("Here's your fortune!")

        if topic == "school":
            fortune = random.choice(school_fortunes)
        elif topic == "career":
            fortune = random.choice(career_fortunes)
        elif topic == "random":
            fortune = random.choice(random_fortunes)

        speaker.say("I see. Your fortune is " + fortune)
        speaker.say("Thanks for playing! Would you like to try again?")
        
        while True:
            again = listen()

            if "yes" in again or "yeah" in again:
                break
            elif "no" in again or "nope" in again:
                speaker.say("Thanks for playing! Goodbye!")
                return
            else:
                speaker.say("Please say yes or no.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")


