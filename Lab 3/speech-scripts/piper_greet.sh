#!/usr/bin/env bash
# Greet Abiola Bolaji using a Piper voice. Model path is passed in by the
# per-voice wrapper scripts (piper_greet_en.sh, piper_greet_sw.sh).

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="${1:-$SCRIPT_DIR/sw_CD-lanfrica-medium.onnx}"

python3 -m piper \
  --model "$MODEL" \
  --output-file greeting.wav \
  -- "Hello, The Oga , Prime Minister, Excellency, Importer, Exporter, Pure Water, Sir Abiola Bolaji. Welcome!"
aplay greeting.wav
