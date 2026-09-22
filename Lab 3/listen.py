#!/usr/bin/env python3
"""Listen continuously, and transcribe each utterance as it ends.

This is the script that makes turn-taking visible. A voice activity detector
(Silero VAD, running in ONNX Runtime) watches the microphone stream and decides
where each utterance starts and stops. Only the detected speech is handed to
faster-whisper, so the Pi is not transcribing silence.

    python listen.py
    python listen.py --min-silence 0.8      # wait longer before deciding you're done
    python listen.py --model base.en

The parameter that matters most for how the interaction *feels* is
--min-silence. It is the endpointing threshold: how long a pause has to be
before the system concludes your turn is over. Too short and it interrupts you
mid-sentence; too long and it feels unresponsive. There is no correct value —
it depends on the interaction you are designing.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import sherpa_onnx
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DEFAULT_VAD = Path(__file__).resolve().parent.parent / "models" / "silero_vad.onnx"


def build_vad(model_path: Path, min_silence: float, min_speech: float):
    """Returns (detector, window_size)."""
    config = sherpa_onnx.VadModelConfig()
    config.silero_vad.model = str(model_path)
    config.silero_vad.min_silence_duration = min_silence
    config.silero_vad.min_speech_duration = min_speech
    config.sample_rate = SAMPLE_RATE
    detector = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
    return detector, config.silero_vad.window_size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="tiny.en", help="whisper model size")
    parser.add_argument("--vad-model", type=Path, default=DEFAULT_VAD)
    parser.add_argument("--min-silence", type=float, default=0.4,
                        help="seconds of silence that end a turn (default: 0.4)")
    parser.add_argument("--min-speech", type=float, default=0.25,
                        help="ignore speech bursts shorter than this (default: 0.25)")
    args = parser.parse_args()

    if not args.vad_model.is_file():
        sys.exit(f"VAD model not found at {args.vad_model}. Run ./setup.sh first.")

    print("Loading models...", flush=True)
    recognizer = WhisperModel(args.model, device="cpu", compute_type="int8")
    vad, window = build_vad(args.vad_model, args.min_silence, args.min_speech)

    print(f"Input device: {sd.query_devices(sd.default.device[0])['name']}")
    print(f"Endpointing after {args.min_silence}s of silence. Ctrl-C to stop.\n")

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

                t0 = time.perf_counter()
                segments, _ = recognizer.transcribe(utterance, beam_size=1)
                text = " ".join(s.text.strip() for s in segments)
                elapsed = time.perf_counter() - t0

                if text:
                    print(f"[{len(utterance) / SAMPLE_RATE:.1f}s speech, "
                          f"{elapsed:.2f}s to transcribe]  {text}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
