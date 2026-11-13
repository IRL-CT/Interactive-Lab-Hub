#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VOICES_DIR="$(dirname "$SCRIPT_DIR")/voices"
OUTPUT="$SCRIPT_DIR/zipcode_answer.wav"

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "Please say your five digit ZIP code after I finish speaking." \
  | aplay -r 22050 -f S16_LE -t raw -

sleep 0.5

echo "Recording for five seconds. Speak now."

arecord \
  -D plughw:3,0 \
  -d 5 \
  -f S16_LE \
  -r 16000 \
  -c 1 \
  "$OUTPUT"

echo "Answer saved to: $OUTPUT"
