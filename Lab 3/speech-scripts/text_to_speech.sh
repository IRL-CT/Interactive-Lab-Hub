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
  -- "Hi Gaurav, how are you doing?"
aplay welcome.wav

