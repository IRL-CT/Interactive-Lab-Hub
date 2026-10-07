#!/usr/bin/env bash
# Ask "What is your zip code?", record the answer, and print the transcript.
#
#   ./speech_to_text.sh
#   ./speech_to_text.sh 6 base.en      # listen for 6s, use the base.en model
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VOICES_DIR="$(dirname "$SCRIPT_DIR")/voices"
RECORDING="$SCRIPT_DIR/answer.wav"

SECONDS_TO_LISTEN="${1:-5}"
MODEL="${2:-tiny.en}"

echo "Asking..."
python3 -m piper \
  --model en_US-lessac-medium \
  --data-dir "$VOICES_DIR" \
  --output-raw \
  -- "What is your zip code?" \
  | aplay -q -r 22050 -f S16_LE -t raw -

echo "Listening for ${SECONDS_TO_LISTEN}s..."
arecord -q -f S16_LE -r 16000 -c 1 -d "$SECONDS_TO_LISTEN" "$RECORDING"

TEXT="$(python3 - "$RECORDING" "$MODEL" <<'PY'
import sys
from faster_whisper import WhisperModel

audio, model_size = sys.argv[1], sys.argv[2]
model = WhisperModel(model_size, device="cpu", compute_type="int8")
segments, _ = model.transcribe(audio, beam_size=1, language="en")
print(" ".join(s.text.strip() for s in segments))
PY
)"

echo
echo "You said: $TEXT"

# Word digits -> numerals, then keep digits only.
# Handles both "14850" and "one four eight five zero".
DIGITS="$(echo "$TEXT" | tr '[:upper:]' '[:lower:]' \
  | sed -E \
      -e 's/\bzero\b/0/g' -e 's/\boh\b/0/g' -e 's/\bo\b/0/g' \
      -e 's/\bone\b/1/g' -e 's/\btwo\b/2/g' -e 's/\bthree\b/3/g' \
      -e 's/\bfour\b/4/g' -e 's/\bfive\b/5/g' -e 's/\bsix\b/6/g' \
      -e 's/\bseven\b/7/g' -e 's/\beight\b/8/g' -e 's/\bnine\b/9/g' \
  | tr -cd '0-9')"

if [[ ${#DIGITS} -eq 5 ]]; then
  echo "Zip code: $DIGITS"
else
  echo "(Couldn't find a 5-digit zip; got digits '$DIGITS')"
fi
