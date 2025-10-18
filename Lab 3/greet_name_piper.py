#!/usr/bin/env python3
# greet_name_piper.py
# Usage:
#   ./greet_name_piper.py "Your exact text here."
#   echo "Your exact text here." | ./greet_name_piper.py
#
# It will speaks EXACTLY the input text.
# Defaults to WAV mode with writing a temp .wav, then plays with aplay
# Set PIPER_STREAM=1 to stream raw PCM directly to aplay.
#
# Env vars you can tweak:
#   PIPER_VOICE_DIR     (default: ~/facerecog/voices)
#   PIPER_VOICE_NAME    (default: en_US-libritts_r-medium.onnx)
#   PIPER_LENGTH_SCALE  (default: 1.08)   # 1.0 = default; >1.0 slower/warmer
#   PIPER_NOISE_SCALE   (default: 0.5)
#   PIPER_NOISE_W       (default: 0.6)
#   PIPER_SENT_SIL      (default: 0.12)   # seconds pause between sentences
#   PIPER_SPEAKER_ID    (optional)        # for multi-speaker models
#   PIPER_STREAM        (0/1)             # 1 = stream raw to aplay; 0 = WAV mode
#
# Requires:
#   python3 -m pip install piper-tts
#   sudo apt install -y alsa-utils     # for aplay

import json
import os
import shlex
import subprocess
import sys
import tempfile

VOICE_DIR  = os.environ.get("PIPER_VOICE_DIR", os.path.expanduser("~/facerecog/voices"))
VOICE_NAME = os.environ.get("PIPER_VOICE_NAME", "en_US-libritts_r-medium.onnx")
VOICE_PATH = os.path.join(VOICE_DIR, VOICE_NAME)
VOICE_JSON = VOICE_PATH + ".json"  # Piper voices ship with a matching .onnx.json

# Prosody knobs (tweak to taste)
LENGTH_SCALE = os.environ.get("PIPER_LENGTH_SCALE", "1.08")
NOISE_SCALE  = os.environ.get("PIPER_NOISE_SCALE",  "0.5")
NOISE_W      = os.environ.get("PIPER_NOISE_W",      "0.6")
SENT_SIL     = os.environ.get("PIPER_SENT_SIL",     "0.12")

SPEAKER_ID   = os.environ.get("PIPER_SPEAKER_ID", "").strip()
STREAM_MODE  = os.environ.get("PIPER_STREAM", "0").strip().lower() in ("1", "true", "yes", "on")

def _which(cmd: str) -> bool:
    from shutil import which
    return which(cmd) is not None

def _read_voice_sample_rate(default_sr: int = 22050) -> int:
    """Read the Piper voice JSON to get the sample rate; fall back to default if missing."""
    try:
        with open(VOICE_JSON, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return int(meta.get("sample_rate", default_sr))
    except Exception:
        return default_sr

def _get_text_from_args_or_stdin() -> str:
    # Prefer CLI args; if none, read from stdin
    text = " ".join(sys.argv[1:]).strip()
    if not text and not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    return text

def main():
    text = _get_text_from_args_or_stdin()
    if not text:
        print("[greet_name_piper] No input text provided.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(VOICE_PATH):
        print(f"[greet_name_piper] Missing voice model: {VOICE_PATH}", file=sys.stderr)
        sys.exit(2)
    if not _which("piper"):
        print("[greet_name_piper] 'piper' CLI not found. Install with: python3 -m pip install piper-tts", file=sys.stderr)
        sys.exit(2)
    if not _which("aplay"):
        print("[greet_name_piper] 'aplay' not found. Install with: sudo apt install -y alsa-utils", file=sys.stderr)
        sys.exit(2)

    # Base Piper command; text is piped on stdin
    piper_base = [
        "piper",
        "--model", VOICE_PATH,
        "--length_scale", str(LENGTH_SCALE),
        "--noise_scale", str(NOISE_SCALE),
        "--noise_w", str(NOISE_W),
        "--sentence_silence", str(SENT_SIL),
    ]
    if SPEAKER_ID:
        piper_base += ["--speaker", SPEAKER_ID]

    if STREAM_MODE:
        # STREAM: raw PCM to aplay using the model's sample rate to avoid noise/static
        sample_rate = _read_voice_sample_rate(default_sr=22050)
        piper_cmd = piper_base + ["--output-raw", "-"]
        try:
            piper = subprocess.Popen(
                piper_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"[greet_name_piper] Failed to start piper: {e}", file=sys.stderr)
            sys.exit(3)

        try:
            aplay = subprocess.Popen(
                ["aplay", "-q", "-r", str(sample_rate), "-f", "S16_LE", "-t", "raw", "-"],
                stdin=piper.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            assert piper.stdin is not None
            piper.stdin.write(text.encode("utf-8"))
            piper.stdin.close()
            aplay.wait()
            piper.wait()
        except Exception as e:
            print(f"[greet_name_piper] Streaming error: {e}", file=sys.stderr)
            sys.exit(4)
    else:
        # WAV MODE (recommended by docs), piper writes a proper WAV, then play it with aplay
        with tempfile.NamedTemporaryFile(prefix="piper_", suffix=".wav", delete=False) as tf:
            wav_path = tf.name

        piper_cmd = piper_base + ["--output_file", wav_path]
        try:
            p = subprocess.Popen(
                piper_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"[greet_name_piper] Failed to start piper: {e}", file=sys.stderr)
            try: os.unlink(wav_path)
            except Exception: pass
            sys.exit(3)

        try:
            assert p.stdin is not None
            p.stdin.write(text.encode("utf-8"))
            p.stdin.close()
            rc = p.wait(timeout=60)
            if rc != 0 or not os.path.isfile(wav_path) or os.path.getsize(wav_path) == 0:
                print(f"[greet_name_piper] Piper failed (rc={rc}); no WAV produced.", file=sys.stderr)
                try: os.unlink(wav_path)
                except Exception: pass
                sys.exit(4)

            aplay_rc = subprocess.call(["aplay", "-q", wav_path])
            if aplay_rc != 0:
                print(f"[greet_name_piper] aplay failed with rc={aplay_rc}", file=sys.stderr)
        finally:
            try: os.unlink(wav_path)
            except Exception: pass

if __name__ == "__main__":
    main()
