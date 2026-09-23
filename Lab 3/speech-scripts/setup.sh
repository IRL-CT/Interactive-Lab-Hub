#!/usr/bin/env bash
# Lab 3  Chatterboxes setup
#
# Run this ONCE, from inside the Lab 3 directory, with your venv activated:
#   source .venv/bin/activate
#   ./setup.sh
#
# It installs the classic (non-neural) TTS engines, fetches the VAD model,
# and pre-downloads a Piper voice so nobody is waiting on a download in class.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$LAB_DIR/models"
VOICES_DIR="$LAB_DIR/voices"

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "WARNING: no virtualenv active. Run 'source .venv/bin/activate' first."
  echo "Continuing in 5s — Ctrl-C to abort."
  sleep 5
fi

echo "==> Installing system audio and classic TTS packages"
sudo apt-get update
sudo apt-get install -y \
  alsa-utils \
  libportaudio2 \
  espeak-ng \
  festival festvox-kallpc16k \
  flite

# Notes on what we deliberately no longer install:
#   libttspico-utils — abandoned Android TTS code, not in current Debian
#   mplayer          — was only there for the Google translate_tts hack
#   portaudio19-dev  — only needed to *build* pyaudio; we use sounddevice

echo "==> Fetching Silero VAD model"
mkdir -p "$MODELS_DIR"
if [[ ! -f "$MODELS_DIR/silero_vad.onnx" ]]; then
  wget -q --show-progress \
    -O "$MODELS_DIR/silero_vad.onnx" \
    https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx
else
  echo "    already present, skipping"
fi

echo "==> Downloading a Piper voice (en_US-lessac-medium)"
mkdir -p "$VOICES_DIR"
if [[ ! -f "$VOICES_DIR/en_US-lessac-medium.onnx" ]]; then
  python3 -m piper.download_voices en_US-lessac-medium --data-dir "$VOICES_DIR"
else
  echo "    already present, skipping"
fi

echo "==> Warming the faster-whisper cache (tiny.en)"
python3 - <<'PY'
from faster_whisper import WhisperModel
WhisperModel("tiny.en", device="cpu", compute_type="int8")
print("    model cached")
PY

echo "==> Making speech-scripts executable"
chmod u+x "$LAB_DIR"/speech-scripts/*.sh 2>/dev/null || true

echo
echo "Setup complete. Try:  python speech-scripts/transcribe.py --help"
