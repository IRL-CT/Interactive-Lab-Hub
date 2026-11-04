#!/usr/bin/env python3
"""ask_number.py: the Pi asks for a number out loud, records the answer,
transcribes it, and pulls out the digits.

Put this in "Lab 3/speech-scripts/" and run it with the lab venv active:

    python ask_number.py                                  # asks for a zipcode
    python ask_number.py --question phone                 # asks for a phone number
    python ask_number.py --question pets --seconds 4
    python ask_number.py --model small.en                 # compare model sizes

Every answer is appended to number_log.csv with the raw transcript next to
the digits we extracted, so you can see the characteristic mistakes the
transcriber makes on numbers (e.g. "oh" vs 0, "for" vs 4, "to" vs 2).
"""

import argparse
import csv
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VOICES_DIR = SCRIPT_DIR.parent / "voices"  # same folder piper_demo.sh uses
LOG_FILE = SCRIPT_DIR / "number_log.csv"
ANSWER_WAV = SCRIPT_DIR / "answer.wav"

QUESTIONS = {
    "zip": ("What is your zip code?", 5),
    "phone": ("What is your phone number? Please say it one digit at a time.", 10),
    "pets": ("How many pets do you have?", None),
}

WORD_TO_DIGIT = {
    "zero": "0", "oh": "0", "o": "0", "one": "1", "two": "2", "to": "2",
    "too": "2", "three": "3", "four": "4", "for": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "ate": "8", "nine": "9",
}
TENS = {"ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
        "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}


def extract_digits(text: str) -> str:
    """Turn a transcript like 'One oh four, double four.' into '10444'.

    Handles digits Whisper already wrote as numerals ("10044", "555-1234"),
    spelled-out digits, "oh" for zero, homophones like "for"/"to",
    "double"/"triple", and simple tens like "twenty three".
    """
    words = re.findall(r"[a-z]+|\d+", text.lower())
    out, repeat = [], 1
    i = 0
    while i < len(words):
        w = words[i]
        if w.isdigit():
            out.append(w * repeat if repeat > 1 and len(w) == 1 else w)
            repeat = 1
        elif w in ("double", "triple"):
            repeat = 2 if w == "double" else 3
        elif w in TENS:
            value = TENS[w]
            nxt = words[i + 1] if i + 1 < len(words) else ""
            if value >= 20 and nxt in WORD_TO_DIGIT and WORD_TO_DIGIT[nxt] != "0":
                value += int(WORD_TO_DIGIT[nxt])
                i += 1
            out.append(str(value))
            repeat = 1
        elif w in WORD_TO_DIGIT:
            out.append(WORD_TO_DIGIT[w] * repeat)
            repeat = 1
        i += 1
    return "".join(out)


def say(text: str, voice: str) -> None:
    """Speak with Piper, streaming to the speaker."""
    config = json.loads((VOICES_DIR / f"{voice}.onnx.json").read_text())
    rate = str(config["audio"]["sample_rate"])
    piper = subprocess.Popen(
        ["python3", "-m", "piper", "--model", voice, "--data-dir", str(VOICES_DIR),
         "--output-raw", "--", text],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    subprocess.run(["aplay", "-q", "-r", rate, "-f", "S16_LE", "-c", "1", "-t", "raw", "-"],
                   stdin=piper.stdout, check=True)
    piper.wait()


def record(seconds: int) -> None:
    """Record mono 16 kHz audio from the default mic (what Whisper expects)."""
    subprocess.run(["arecord", "-q", "-d", str(seconds), "-f", "S16_LE",
                    "-c", "1", "-r", "16000", str(ANSWER_WAV)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--question", choices=QUESTIONS, default="zip")
    parser.add_argument("--seconds", type=int, default=6, help="how long to record")
    parser.add_argument("--model", default="base.en", help="tiny.en, base.en, small.en ...")
    parser.add_argument("--voice", default="en_US-lessac-medium")
    args = parser.parse_args()

    question, expected_len = QUESTIONS[args.question]

    # Load the model before asking, so the user doesn't wait on it after answering.
    print(f"Loading faster-whisper model {args.model} ...")
    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device="cpu", compute_type="int8")

    print(f"Pi: {question}")
    say(question, args.voice)
    print(f"Recording for {args.seconds} seconds, speak now ...")
    record(args.seconds)

    start = time.perf_counter()
    segments, _ = model.transcribe(str(ANSWER_WAV), beam_size=5, language="en")
    transcript = " ".join(s.text.strip() for s in segments).strip()
    elapsed = time.perf_counter() - start
    rtf = elapsed / args.seconds

    digits = extract_digits(transcript)
    looks_right = expected_len is None or len(digits) == expected_len

    print(f"Transcript : {transcript!r}")
    print(f"Digits     : {digits or '(none found)'}")
    print(f"Took {elapsed:.2f}s for {args.seconds}s of audio (real-time factor {rtf:.2f})")

    if not digits:
        reply = "Sorry, I didn't catch a number."
    elif not looks_right:
        reply = f"I heard {' '.join(digits)}. That doesn't look like a full {args.question} number."
    else:
        reply = f"I heard {' '.join(digits)}. Thank you."
    print(f"Pi: {reply}")
    say(reply, args.voice)

    new_file = not LOG_FILE.exists()
    with LOG_FILE.open("a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["time", "question", "model", "transcript", "digits",
                             "length_ok", "transcribe_seconds", "rtf"])
        writer.writerow([datetime.now().isoformat(timespec="seconds"), args.question,
                         args.model, transcript, digits, looks_right,
                         f"{elapsed:.2f}", f"{rtf:.2f}"])
    print(f"Saved to {LOG_FILE.name}")


if __name__ == "__main__":
    main()