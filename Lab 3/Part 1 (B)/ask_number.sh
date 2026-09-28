#!/usr/bin/env bash
set -euo pipefail

# Always run from the folder containing this script.
cd -- "$(dirname -- "$0")"

# Create the folder for saved recordings and results.
mkdir -p results

# Create the spoken question.
python3 -m piper \
    --model en_US-lessac-medium \
    --data-dir ../voices \
    --output-file results/number_question.wav \
    -- "Please say a five digit ZIP code, one digit at a time. Speak after the question finishes."

# Play the question through the USB speaker.
aplay results/number_question.wav

# Record the respondent's answer from USB microphone card 3.
echo "Recording starts now. Say five digits one at a time."

arecord \
    -D plughw:3,0 \
    -d 8 \
    -f S16_LE \
    -c 1 \
    -r 16000 \
    results/number_answer.wav

echo "Recording finished."
echo "Transcribing your answer..."

# Convert the recorded speech into text.
python transcribe.py \
    results/number_answer.wav \
    --model tiny.en \
    | tee results/number_transcript.txt

echo "The transcript was saved to results/number_transcript.txt"
