#!/usr/bin/env bash
# greet_viktor.sh: Piper (neural TTS) greets me by name, in Bulgarian.
#
# Put this in "Lab 3/speech-scripts/" and run it from there:
#   chmod +x greet_viktor.sh
#   ./greet_viktor.sh                      # default Bulgarian greeting
#   ./greet_viktor.sh "some other text"    # say something else
#
# The Bulgarian greeting is stored below as \uXXXX escapes, so this file is
# plain ASCII. If an editor or a copy step mangles Cyrillic (e.g. Cyrillic "b"
# turns into "D+-"), the voice reads symbols like "plus-minus" aloud. ASCII can't
# be mangled that way.
#
# Voice: bg_BG-dimitar-medium. It is downloaded into "Lab 3/voices" if it is missing.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Same voices folder as piper_demo.sh: "Lab 3/voices", one level up.
VOICES_DIR="${VOICES_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)/voices}"
VOICE="${VOICE:-bg_BG-dimitar-medium}"
MODEL="$VOICES_DIR/$VOICE.onnx"
CONFIG="$MODEL.json"

# Make Python read and write UTF-8 no matter what the Pi's locale is set to.
export PYTHONUTF8=1

# "Zdravey, Viktor Radev! Dobre doshal v laboratoriyata."
# = "Hello, Viktor Radev! Welcome to the lab."
GREETING='\u0417\u0434\u0440\u0430\u0432\u0435\u0439, \u0412\u0438\u043a\u0442\u043e\u0440 \u0420\u0430\u0434\u0435\u0432! \u0414\u043e\u0431\u0440\u0435 \u0434\u043e\u0448\u044a\u043b \u0432 \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f\u0442\u0430.'

# Use the lab's virtual environment if it isn't already active.
if [[ -z "${VIRTUAL_ENV:-}" && -f "$SCRIPT_DIR/../.venv/bin/activate" ]]; then
  set +u
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/../.venv/bin/activate"
  set -u
fi

if ! python3 -c "import piper" 2>/dev/null; then
  echo "Piper isn't installed in this Python. Activate the lab venv and run:" >&2
  echo "  pip install -r requirements.txt" >&2
  exit 1
fi

# Download the voice into VOICES_DIR if it isn't there yet.
if [[ ! -f "$MODEL" || ! -f "$CONFIG" ]]; then
  echo "Downloading $VOICE into $VOICES_DIR ..."
  mkdir -p "$VOICES_DIR"
  python3 -m piper.download_voices "$VOICE" --data-dir "$VOICES_DIR"
fi

# Raw audio has no header, so aplay has to be told the sample rate.
# Each voice stores its own rate in its .onnx.json (medium voices are
# usually 22050 Hz, not 16000). A wrong rate makes the voice slow and deep.
if [[ $# -gt 0 ]]; then
  TEXT="$1"
else
  TEXT="$(python3 -c 'import sys; print(sys.argv[1].encode("ascii").decode("unicode_escape"))' "$GREETING")"
fi
echo "Saying: $TEXT"

RATE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["audio"]["sample_rate"])' "$CONFIG")"

# Stream straight to the speaker so speech starts before synthesis finishes.
python3 -m piper \
  --model "$MODEL" \
  --output-raw \
  -- "$TEXT" \
  | aplay -q -r "$RATE" -f S16_LE -c 1 -t raw -