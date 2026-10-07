#!/usr/bin/env bash

# Greet Jindi using Piper TTS

VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "Hello Jindi! Welcome back! I hope you are having a wonderful day!" \
  | aplay -r 22050 -f S16_LE -t raw -
  