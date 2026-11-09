#!/usr/bin/env bash

set -euo pipefail

VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

NAME="Pallavi"

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "Wee Wee Waa Waa this is $NAME" \
  | aplay -r 22050 -f S16_LE -t raw -
