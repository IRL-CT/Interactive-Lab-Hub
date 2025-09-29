#!/bin/bash
# ask_number.sh - Verbal prompt and record spoken answer

OUTPUT_FILE="response.wav"

# Step 1: Speak the question
espeak "Please say your zip code."

# Step 2: Record audio for 5 seconds
echo "Recording... please speak now."
arecord -f cd -t wav -d 5 -r 16000 -c 1 $OUTPUT_FILE
echo "Recording saved to $OUTPUT_FILE"

# Step 3: Confirm
espeak "Thank you. Your response has been recorded."
