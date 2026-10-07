#!/usr/bin/env bash

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

