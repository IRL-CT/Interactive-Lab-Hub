#!/bin/bash
VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-file greeting.wav \
  -- "Hello, Alison. Welcome to Lab 3."

aplay greeting.wav
