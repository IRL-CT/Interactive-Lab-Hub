#!/usr/bin/env bash

# Ask a numerical question using Piper TTS
# and record the user's spoken answer.

set -e

VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

echo "Asking the question..."

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "Hi Jindi! How many times do you walk your dog every day?" \
  | aplay -r 22050 -f S16_LE -t raw -

echo "Please answer now!"

# Find the microphone card number
MIC_CARD=$(arecord -l | awk -F'[ :]' '/^card/{print $2; exit}')

if [ -z "$MIC_CARD" ]; then
    echo "No microphone found!"
    exit 1
fi

# Save the recording
OUT="$HOME/numerical_answer.wav"

arecord \
  -D plughw:${MIC_CARD},0 \
  -f S16_LE \
  -r 16000 \
  -c 1 \
  -d 8 \
  "$OUT"

echo "Recording saved to $OUT"