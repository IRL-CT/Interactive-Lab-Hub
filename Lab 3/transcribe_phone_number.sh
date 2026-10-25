#!/bin/bash
TEMP_WAV="phone_number_response.wav"
TEMP_TXT="phone_number_transcription.txt"
TTS_ENGINE="espeak"
QUESTION="Please state your ten-digit phone number now, clearly."
$TTS_ENGINE -s 130 "$QUESTION"
arecord -D plughw:CARD=Device,DEV=0 -f S16_LE -r 16000 -d 5 -t wav $TEMP_WAV 2>/dev/null
vosk-transcriber -i $TEMP_WAV -o $TEMP_TXT
TRANSCRIBED_TEXT=$(cat $TEMP_TXT)
NUMBER_WORDS=$(echo "$TRANSCRIBED_TEXT" | awk '{$1=$1};1')
DIGITS=$(
    echo "$NUMBER_WORDS" |
    sed -E 's/one/1/g' |
    sed -E 's/two/2/g' |
    sed -E 's/three/3/g' |
    sed -E 's/four/4/g' |
    sed -E 's/five/5/g' |
    sed -E 's/six/6/g' |
    sed -E 's/seven/7/g' |
    sed -E 's/eight/8/g' |
    sed -E 's/nine/9/g' |
    sed -E 's/zero|oh/0/g' |
    tr -d ' '
)
FORMATTED_NUMBER=$(echo "$DIGITS" | sed -E 's/^([0-9]{3})([0-9]{3})([0-9]{4})$/(\1) \2-\3/')
echo "User's Transcribed Text:"
echo "$NUMBER_WORDS"
echo "User's Phone Number (Formatted):"
echo "$FORMATTED_NUMBER"
rm $TEMP_WAV $TEMP_TXT