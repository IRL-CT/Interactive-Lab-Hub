#!/usr/bin/env bash
# Neural TTS with Piper.
#
# NOTE: the Piper 1.x command line is different from the 0.x/1.3 one you may
# find in older tutorials. Voices are downloaded explicitly, and the entry
# point is `python3 -m piper`, not a `piper` binary on PATH.

set -euo pipefail
VOICES_DIR="$(cd "$(dirname "\){BASH_SOURCE[0]}")" && pwd)/voices"

# List everything available (there are a lot, in many languages):
#   python3 -m piper.download_voices
#
# Download one:
#   python3 -m piper.download_voices bg_BG-dimitar-medium --data-dir "\$VOICES_DIR"

# Synthesize to a file, then play it.
python3 -m piper \
  --model bg_BG-dimitar-medium \
  --data-dir "\$VOICES_DIR" \
  --output-file welcome.wav \
  -- "Добре дошли в света на синтеза на реч."
aplay welcome.wav

# Stream straight to the speaker instead — lower latency, because playback
# starts before the whole sentence is synthesized. Listen for the difference.
python3 -m piper \
  --model bg_BG-dimitar-medium \
  --data-dir "\$VOICES_DIR" \
  --output-raw \
  -- "Това изречение се произнася първо. Това се синтезира, докато го чувате." \
  | aplay -r 16000  -f S16_LE -t raw -

# Same text, slower and quieter — Piper exposes prosody knobs:
python3 -m piper \
  --model bg_BG-dimitar-medium \
  --data-dir "\$VOICES_DIR" \
  --length-scale 1.4 \
  --volume 0.6 \
  --output-raw \
  -- "А ето как звучи, когато забавя темпото." \
  | aplay -r 16000  -f S16_LE -t raw -
