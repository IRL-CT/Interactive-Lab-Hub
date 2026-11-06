#!/usr/bin/env bash
# Wrapper: run the greeting with the en_US-lessac-medium voice.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/piper_greet.sh" "$SCRIPT_DIR/en_US-lessac-medium.onnx"
