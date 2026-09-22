#!/usr/bin/env python3
"""Transcribe an audio file with faster-whisper, and report how long it took.

The point of this script is not the transcript. It is the *latency*, and what
different model sizes cost you. Run it on the same file with several models and
watch the accuracy/latency tradeoff directly.

    python transcribe.py lookdave.wav
    python transcribe.py lookdave.wav --model base.en
    python transcribe.py lookdave.wav --model tiny.en --compute-type float32

Models, smallest first: tiny.en, base.en, small.en, medium.en
(The .en variants are English-only and noticeably faster than the multilingual
ones at the same size. Drop the suffix if you need another language.)
"""

import argparse
import time

from faster_whisper import WhisperModel


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("audio", help="path to a .wav file")
    parser.add_argument("--model", default="tiny.en",
                        help="whisper model size (default: tiny.en)")
    parser.add_argument("--compute-type", default="int8",
                        choices=["int8", "int8_float32", "float32"],
                        help="quantization; int8 is ~2-3x faster on the Pi (default: int8)")
    parser.add_argument("--beam-size", type=int, default=1,
                        help="1 is greedy and fastest; 5 is more accurate and slower")
    args = parser.parse_args()

    t0 = time.perf_counter()
    model = WhisperModel(args.model, device="cpu", compute_type=args.compute_type)
    t_load = time.perf_counter() - t0

    t1 = time.perf_counter()
    segments, info = model.transcribe(args.audio, beam_size=args.beam_size)
    text = " ".join(seg.text.strip() for seg in segments)  # generator: consume it
    t_transcribe = time.perf_counter() - t1

    print(f"\n{text}\n")
    print(f"model            {args.model} ({args.compute_type}, beam={args.beam_size})")
    print(f"audio duration   {info.duration:.2f}s")
    print(f"model load       {t_load:.2f}s")
    print(f"transcription    {t_transcribe:.2f}s")
    print(f"real-time factor {t_transcribe / info.duration:.2f}x")
    print("\n(Model load is a one-time cost per process. In an interactive system "
          "you load once and keep the model resident — which is what listen.py does.)")


if __name__ == "__main__":
    main()
