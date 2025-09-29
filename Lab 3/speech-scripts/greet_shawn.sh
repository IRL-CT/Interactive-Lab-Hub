set -euo pipefail

TMP="/tmp/greet_shawn.wav"
TEXT="Hey Shawn, welcome back to the lab! Your Pi is ready."

pico2wave -w "$TMP" "$TEXT"
aplay "$TMP" >/dev/null 2>&1
rm -f "$TMP"
