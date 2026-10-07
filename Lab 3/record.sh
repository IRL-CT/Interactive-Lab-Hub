#!/bin/bash
# Records 5 seconds from the USB microphone and saves it as a .wav file

# Uses the first capture card found; to override, run: ./record.sh 3
MIC_CARD=${1:-$(arecord -l | awk -F'[ :]' '/^card/{print $2; exit}')}
OUT="$HOME/recording_$(date +%Y%m%d_%H%M%S).wav"

if [ -z "$MIC_CARD" ]; then
     echo "No microphone found. Check the connection with: arecord -l"
     exit 1
fi

echo "Recording 5 seconds from card $MIC_CARD... speak now!"
   if arecord -D plughw:${MIC_CARD},0 -f S16_LE -r 16000 -c 1 -d 5 "$OUT"; then
       echo "Saved to $OUT"
   else
       echo "Recording failed. Check the card number with: arecord -l"
   fi
EOF
