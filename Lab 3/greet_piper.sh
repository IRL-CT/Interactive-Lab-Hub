
#!/usr/bin/env bash

set -euo pipefail

VOICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/voices"

python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-file my_greeting.wav \
  -- "Hello,Afroza, KM, CICI, Lamiah, welcome! I am so proud of you guys"

aplay my_greeting.wav
