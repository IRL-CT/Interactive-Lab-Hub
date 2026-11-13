#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VOICES_DIR="$(dirname "$SCRIPT_DIR")/voices"

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "Hello Yangchen. Welcome back. I am ready to help you today." \
  | aplay -r 22050 -f S16_LE -t raw -
