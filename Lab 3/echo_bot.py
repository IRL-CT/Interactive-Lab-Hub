#!/usr/bin/env python3
"""The whole loop: listen, understand where the turn ended, answer out loud.

This is deliberately the dumbest possible dialogue policy — it repeats what you
said back to you. That is the point. With the content held constant, everything
you notice about the interaction is a property of the *timing* and the *voice*,
not of what the system says. Get this working, then replace `respond()` with
something of your own.

    python echo_bot.py
    python echo_bot.py --min-silence 1.0
    python echo_bot.py --barge-in

Things worth trying:
  - Interrupt it while it's speaking. What happens? Should it stop?
  - Set --min-silence to 0.2, then to 1.5. Which one feels like it is listening?
  - Add a deliberate 2-second delay before it replies. Does it feel broken, or
    thoughtful?
"""

import argparse
import queue
import sys
import threading
import time
import wave
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


def respond(heard: str) -> str:
    """Your dialogue policy goes here. Right now it is a parrot."""
    return f"You said: {heard}"


class Speaker:
    """Synthesizes with Piper and plays through the default output device."""

    def __init__(self, voice_path: Path) -> None:
        self.voice = PiperVoice.load(str(voice_path))
        self.speaking = threading.Event()

    def say(self, text: str) -> float:
        self.speaking.set()
        t0 = time.perf_counter()
        first_audio_at = None
        try:
            for chunk in self.voice.synthesize(text):
                audio = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
                if first_audio_at is None:
                    first_audio_at = time.perf_counter() - t0
                sd.play(audio, samplerate=chunk.sample_rate)
                sd.wait()
        finally:
            self.speaking.clear()
        return first_audio_at or 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="tiny.en")
    parser.add_argument("--vad-model", type=Path, default=DEFAULT_VAD)
    parser.add_argument("--voice", type=Path, default=DEFAULT_VOICE)
    parser.add_argument("--min-silence", type=float, default=0.4,
                        help="seconds of silence that end your turn")
    parser.add_argument("--barge-in", action="store_true",
                        help="keep listening while the system is talking "
                             "(you will hear it transcribe its own voice — "
                             "this is the echo-cancellation problem)")
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

    speaker.say("I'm listening.")
    print(f"Ready. Endpointing after {args.min_silence}s of silence. Ctrl-C to stop.\n")

    buffer = np.empty(0, dtype=np.float32)
    samples_per_read = int(0.1 * SAMPLE_RATE)

    with sd.InputStream(channels=1, dtype="float32", samplerate=SAMPLE_RATE) as stream:
        while True:
            chunk, _ = stream.read(samples_per_read)

            if speaker.speaking.is_set() and not args.barge_in:
                continue  # half-duplex: ignore the mic while we talk

            buffer = np.concatenate([buffer, chunk.reshape(-1)])
            while len(buffer) > window:
                vad.accept_waveform(buffer[:window])
                buffer = buffer[window:]

            while not vad.empty():
                utterance = np.array(vad.front.samples, dtype=np.float32)
                vad.pop()
                turn_ended = time.perf_counter()

                segments, _ = recognizer.transcribe(utterance, beam_size=1)
                heard = " ".join(s.text.strip() for s in segments)
                if not heard:
                    continue
                asr_done = time.perf_counter()

                reply = respond(heard)
                print(f"  heard: {heard}")
                print(f"  reply: {reply}")
                tts_latency = speaker.say(reply)

                print(f"  [asr {asr_done - turn_ended:.2f}s | "
                      f"tts first audio {tts_latency:.2f}s | "
                      f"total gap {asr_done - turn_ended + tts_latency:.2f}s]\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
