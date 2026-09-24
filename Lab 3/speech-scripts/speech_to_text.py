#!/usr/bin/env python3
"""Ask "What is your zip code?", record the answer, and print the transcript.

    python ask_zip.py
    python ask_zip.py --seconds 6 --model base.en

Pipeline: Piper speaks the question -> arecord captures a fixed-length reply
-> faster-whisper transcribes it. The Whisper model is loaded *before* the
question is asked, so the load time doesn't add to the wait after you speak.
"""

import argparse
import re
import subprocess
from pathlib import Path

from faster_whisper import WhisperModel

VOICES_DIR = Path(__file__).resolve().parent.parent / "voices"  # same as piper_demo.sh
RECORDING = "answer.wav"

WORD_DIGITS = {"zero": "0", "oh": "0", "o": "0", "one": "1", "two": "2",
               "three": "3", "four": "4", "five": "5", "six": "6",
               "seven": "7", "eight": "8", "nine": "9"}


def speak(text: str, voice: str) -> None:
    piper = subprocess.Popen(
        ["python3", "-m", "piper", "--model", voice, "--data-dir", str(VOICES_DIR),
         "--output-raw", "--", text],
        stdout=subprocess.PIPE)
    subprocess.run(["aplay", "-q", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
                   stdin=piper.stdout, check=True)
    piper.wait()


def record(seconds: int) -> None:
    # 16 kHz mono is what Whisper wants natively.
    subprocess.run(["arecord", "-q", "-f", "S16_LE", "-r", "16000", "-c", "1",
                    "-d", str(seconds), RECORDING], check=True)


def extract_digits(text: str) -> str:
    """Handles both '14850' and 'one four eight five zero'."""
    out = []
    for tok in re.findall(r"[a-z]+|\d+", text.lower()):
        if tok.isdigit():
            out.append(tok)
        elif tok in WORD_DIGITS:
            out.append(WORD_DIGITS[tok])
    return "".join(out)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="tiny.en")
    p.add_argument("--voice", default="en_US-lessac-medium")
    p.add_argument("--seconds", type=int, default=5, help="how long to listen")
    args = p.parse_args()

    model = WhisperModel(args.model, device="cpu", compute_type="int8")

    speak("What is your zip code?", args.voice)
    print(f"Listening for {args.seconds}s...")
    record(args.seconds)

    segments, _ = model.transcribe(RECORDING, beam_size=1, language="en")
    text = " ".join(s.text.strip() for s in segments)

    print(f"\nYou said: {text}")
    digits = extract_digits(text)
    if len(digits) == 5:
        print(f"Zip code: {digits}")
    else:
        print(f"(Couldn't find a 5-digit zip; got digits '{digits}')")


if __name__ == "__main__":
    main()
