#!/usr/bin/env python3
"""Ask a question that expects a number as the answer, and record what was heard.

Digit strings are a good stress test for ASR: "double oh seven" vs "007", missed
or duplicated digits, and words like "oh" vs "zero" all trip up transcription in
their own characteristic ways. This script asks a question out loud, listens for
one answer (same VAD turn-taking as echo_bot.py), transcribes it, and appends
the raw result to a log file so you can review the failure modes afterward.

    python ask_number.py
    python ask_number.py --question "What's your zip code?" --field zipcode
    python ask_number.py --question "How many pets do you have?" --field pets

Run it a few times with the same question and compare what got logged. Note
where the transcript is a word ("seven") vs a digit ("7") — whisper is
inconsistent about this, and anything downstream that expects one format will
need to normalize it.
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import sherpa_onnx
import sounddevice as sd
from faster_whisper import WhisperModel
from piper import PiperVoice

SAMPLE_RATE = 16000
LAB_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VAD = LAB_DIR / "models" / "silero_vad.onnx"
DEFAULT_VOICE = LAB_DIR / "voices" / "en_US-lessac-medium.onnx"
DEFAULT_LOG = Path(__file__).resolve().parent / "number_answers.csv"


class Speaker:
    """Synthesizes with Piper and plays through the default output device."""

    def __init__(self, voice_path: Path) -> None:
        self.voice = PiperVoice.load(str(voice_path))

    def say(self, text: str) -> None:
        for chunk in self.voice.synthesize(text):
            audio = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            sd.play(audio, samplerate=chunk.sample_rate)
            sd.wait()


def listen_for_one_answer(recognizer: WhisperModel, vad_model: Path,
                          min_silence: float) -> str:
    """Blocks until one utterance is heard, then returns its transcript."""
    config = sherpa_onnx.VadModelConfig()
    config.silero_vad.model = str(vad_model)
    config.silero_vad.min_silence_duration = min_silence
    config.sample_rate = SAMPLE_RATE
    vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
    window = config.silero_vad.window_size

    buffer = np.empty(0, dtype=np.float32)
    samples_per_read = int(0.1 * SAMPLE_RATE)

    with sd.InputStream(channels=1, dtype="float32", samplerate=SAMPLE_RATE) as stream:
        while True:
            chunk, _ = stream.read(samples_per_read)
            buffer = np.concatenate([buffer, chunk.reshape(-1)])

            while len(buffer) > window:
                vad.accept_waveform(buffer[:window])
                buffer = buffer[window:]

            while not vad.empty():
                utterance = np.array(vad.front.samples, dtype=np.float32)
                vad.pop()

                segments, _ = recognizer.transcribe(utterance, beam_size=1)
                text = " ".join(s.text.strip() for s in segments)
                if text:
                    return text
                # noise, not words: keep listening


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--question", default="What is your phone number?")
    parser.add_argument("--field", default="phone_number",
                        help="label recorded alongside the answer (default: phone_number)")
    parser.add_argument("--model", default="tiny.en", help="whisper model size")
    parser.add_argument("--vad-model", type=Path, default=DEFAULT_VAD)
    parser.add_argument("--voice", type=Path, default=DEFAULT_VOICE)
    parser.add_argument("--min-silence", type=float, default=0.6,
                        help="seconds of silence that end your turn (default: 0.6)")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG,
                        help="CSV file to append the recorded answer to")
    args = parser.parse_args()

    for path, what in [(args.vad_model, "VAD model"), (args.voice, "Piper voice")]:
        if not path.is_file():
            sys.exit(f"{what} not found at {path}. Run ./setup.sh first.")

    print("Loading models...", flush=True)
    recognizer = WhisperModel(args.model, device="cpu", compute_type="int8")
    speaker = Speaker(args.voice)

    speaker.say(args.question)
    print(f"Asked: {args.question}")
    print("Listening for your answer...\n")

    t0 = time.perf_counter()
    answer = listen_for_one_answer(recognizer, args.vad_model, args.min_silence)
    elapsed = time.perf_counter() - t0

    print(f"  heard: {answer}   [{elapsed:.2f}s]")

    is_new_log = not args.log.exists()
    with args.log.open("a", newline="") as f:
        writer = csv.writer(f)
        if is_new_log:
            writer.writerow(["timestamp", "field", "question", "answer"])
        writer.writerow([datetime.now().isoformat(timespec="seconds"),
                         args.field, args.question, answer])
    print(f"Logged to {args.log}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
