#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VOICES_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/voices"

echo "Asking for the number of pets you have..."

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "Hello! How many pets do you have or would like to have?" \
| aplay -r 22050 -f S16_LE -t raw -

sleep 0.5

echo "Recording answer for 5 seconds..."

arecord -d 5 -f cd -c 1 -r 16000 numerical_answer.wav

echo "Answer saved to numerical_answer.wav"
