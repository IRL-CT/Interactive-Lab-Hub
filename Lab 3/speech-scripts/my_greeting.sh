#!/usr/bin/env bash
# Neural TTS with Piper.
#
# NOTE: the Piper 1.x command line is different from the 0.x/1.3 one you may
# find in older tutorials. Voices are downloaded explicitly, and the entry
# point is `python3 -m piper`, not a `piper` binary on PATH.

set -euo pipefail
VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

# List everything available (there are a lot, in many languages):
#   python3 -m piper.download_voices
#
# Download one:
#   python3 -m piper.download_voices en_GB-jenny_dioco-medium --data-dir "$VOICES_DIR"

# Synthesize to a file, then play it.
python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-file welcome.wav \
  -- "Hi Hi Hi welcome to lab 3."
aplay welcome.wav

# Stream straight to the speaker instead — lower latency, because playback
# starts before the whole sentence is synthesized. Listen for the difference.
#python3 -m piper \
 # --model en_US-lessac-medium \
 # --data-dir "$VOICES_DIR" \
 # --output-raw \
 # -- "This sentence is spoken first. This one is synthesized while you hear it." \
 # | aplay -r 22050 -f S16_LE -t raw -

# Same text, slower and quieter — Piper exposes prosody knobs:
#python3 -m piper \
 # --model en_US-lessac-medium \
 # --data-dir "$VOICES_DIR" \
 # --length-scale 1.4 \
 # --volume 0.6 \
 # --output-raw \
 # -- "And this is what it sounds like when I slow down." \
 # | aplay -r 22050 -f S16_LE -t raw -
