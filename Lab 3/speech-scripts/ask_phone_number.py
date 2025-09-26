#!/usr/bin/env -S /home/pi/Interactive-Lab-Hub/Lab\ 3/.venv/bin/python
# Restrict Vosk to numbers and stop when we have enough digits for a phone number.

#I asked CHatGPT to write this script for me.
#The prompt was "i want to modify this so that it only uses numerical value and once it gets enough number for phone number, then it closes," 
import argparse
import json
import queue
import sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer

q = queue.Queue()

# --- helpers ---
def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# Words we'll accept -> digits
WORD2DIGIT = {
    "zero":"0","oh":"0","o":"0",
    "one":"1",
    "two":"2","to":"2","too":"2",
    "three":"3",
    "four":"4","for":"4",
    "five":"5",
    "six":"6",
    "seven":"7",
    "eight":"8","ate":"8",
    "nine":"9",
    "0":"0","1":"1","2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9",
    "dash":"","hyphen":"","space":"","pause":"","comma":"","period":"","dot":""
}

# Grammar: limit recognizer to these words
GRAMMAR_JSON = json.dumps(list(WORD2DIGIT.keys()))

parser = argparse.ArgumentParser(
    description="Capture spoken digits and stop when target length is reached.")
parser.add_argument("-d", "--device", type=int_or_str,
                    help="input device (numeric ID or substring)")
parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument("-m", "--model", type=str, default="en-us",
                    help="vosk language model (default: en-us)")
parser.add_argument("-n", "--num-digits", type=int, default=10,
                    help="how many digits to capture before exiting (default: 10)")
parser.add_argument("-o", "--outfile", type=str, default="phone.txt",
                    help="file to write the captured digits (default: phone.txt)")
args = parser.parse_args()

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        args.samplerate = int(device_info["default_samplerate"])

    model = Model(lang=args.model)
    rec = KaldiRecognizer(model, args.samplerate, GRAMMAR_JSON)

    print("#"*72)
    print(f"Say digits for a phone number ({args.num_digits} digits).")
    print("Speak one digit at a time: e.g., 'nine one seven ...'")
    print("I'll stop automatically when enough digits are captured.")
    print("#"*72)

    collected = []

    def consume_result_text(text: str):
        tokens = text.strip().lower().split()
        for tok in tokens:
            if tok in WORD2DIGIT:
                d = WORD2DIGIT[tok]
                if d in "0123456789":
                    collected.append(d)
        if collected:
            print(f"Digits so far: {''.join(collected)}")
        return len(collected) >= args.num_digits

    with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000,
                           device=args.device, dtype="int16",
                           channels=1, callback=callback):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if consume_result_text(res.get("text", "")):
                    break

    final_digits = "".join(collected)[:args.num_digits]
    with open(args.outfile, "w") as f:
        f.write(final_digits + "\n")

    print("#"*72)
    print(f"Captured {args.num_digits} digits: {final_digits}")
    print(f"Saved to: {args.outfile}")
    print("#"*72)

except KeyboardInterrupt:
    print("\nInterrupted. Partial digits:", "".join(collected) if 'collected' in locals() else "")
    sys.exit(0)
except Exception as e:
    sys.exit(f"{type(e).__name__}: {e}")
