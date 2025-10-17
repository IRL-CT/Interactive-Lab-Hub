set -euo pipefail

LABEL="${1:-phone number}"
DUR="${2:-5}"
OUT="${3:-number_input.txt}"

TMP="/tmp/number_prompt.wav"
pico2wave -w "$TMP" "Please say your ${LABEL} after the beep."
aplay "$TMP" >/dev/null 2>&1 || true
rm -f "$TMP"
printf '\a'; sleep 0.2

arecord -D "${ARECORD_DEVICE:-hw:2,0}" -f cd -c1 -r 48000 -d "$DUR" -t wav recorded_mono.wav
python3 test_words.py recorded_mono.wav | tee "$OUT"
echo "Saved transcript to: $OUT"
