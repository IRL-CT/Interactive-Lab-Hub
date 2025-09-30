#!/bin/bash
# This script asks the user for their phone number and records the answer

# Use TTS to ask the question
espeak "Hello Charlotte, please say your phone number after the beep."

# Record audio from the microphone for 7 seconds (using webcam microphone)
arecord -D hw:2,0 -f cd -t wav -d 7 -c 1 phone_number.wav

# Transcribe the recorded audio using Vosk
vosk-transcriber -i phone_number.wav -o phone_number.txt

# Print the transcription to terminal
echo "You said your phone number is:"
cat phone_number.txt

