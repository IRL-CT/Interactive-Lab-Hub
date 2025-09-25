#!/usr/bin/env bash
set -euo pipefail

# Config
PROMPT="Please say your 5-digit ZIP code after the beep."
REC_SECONDS=5
CARD_DEV="plughw:2,0"
SR=16000
OUTDIR="data"
MODEL_SIZE="tiny.en"

mkdir -p "$OUTDIR"

# Prompt
echo "$PROMPT" | espeak -s 170 -v en-us || true

# Beep
[ -f /usr/share/sounds/alsa/Front_Center.wav ] && aplay /usr/share/sounds/alsa/Front_Center.wav || true

# Record
WAV="$OUTDIR/input_$(date +%s).wav"
if arecord --version >/dev/null 2>&1; then
  if arecord -l | grep -q "$CARD_DEV" 2>/dev/null; then
    arecord -D "$CARD_DEV" -f S16_LE -r "$SR" -c 1 -d "$REC_SECONDS" "$WAV"
  else
    arecord -f S16_LE -r "$SR" -c 1 -d "$REC_SECONDS" "$WAV"
  fi
else
  echo "arecord not available, install with: sudo apt-get install -y alsa-utils"
  exit 1
fi

# Transcribe with faster-whisper
TRANS_TXT="${WAV%.wav}.txt"
python3 - "$WAV" "$TRANS_TXT" "$MODEL_SIZE" << 'PY'
import sys
from faster_whisper import WhisperModel

wav_path, out_txt, model_size = sys.argv[1], sys.argv[2], sys.argv[3]
model = WhisperModel(model_size, device="cpu", compute_type="int8")
segments, info = model.transcribe(wav_path, language="en")

with open(out_txt, "w", encoding="utf-8") as f:
    for seg in segments:
        f.write(seg.text.strip() + " ")
PY

# Extract digits and save CSV
TXT="$TRANS_TXT"
NUM=$(grep -oE '[0-9]+' "$TXT" | tr -d '\n' || true)
CSV="$OUTDIR/answers.csv"
echo "$(date -Is),$NUM" >> "$CSV"

# Display results
echo "Audio: $WAV"
echo "Transcript: $(cat "$TXT")"
echo "Digits recognized: ${NUM:-<none>}"
echo "Saved to: $CSV"
