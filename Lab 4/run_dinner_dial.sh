#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec ./.venv/bin/python dinner_dial.py \
  --run --axis y --neutral 498 --audio \
  --left-us 1650 --center-us 1200 --right-us 900
