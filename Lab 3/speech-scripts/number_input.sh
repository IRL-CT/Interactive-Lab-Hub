#!/usr/bin/env bash

set -euo pipefail

VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "What is your ZIP code?" \
  | aplay -r 22050 -f S16_LE -t raw -

echo "Say your ZIP code"
arecord -d 5 -f cd -c 1 -r 16000 zipcode.wav

echo "Your answer has been recorded. Thank you."
