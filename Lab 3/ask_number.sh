#!/bin/bash
# Activate virtual environment
source .venv/bin/activate
echo "Please tell me your number" | festival --tts
sleep 2
echo "Starting recording, please say your number..."
arecord -D hw:2,0 -f cd -c1 -r 48000 -d 5 -t wav number_input.wav
echo "Processing speech recognition..."
vosk-transcriber -i number_input.wav -o number_result.txt
cat number_result.txt > recorded_number.txt
cat number_result.txt | festival --tts
rm -f number_input.wav number_result.txt