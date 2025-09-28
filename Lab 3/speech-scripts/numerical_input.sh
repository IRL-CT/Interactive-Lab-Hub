#!/bin/bash

# Use TTS to ask the question
echo "Please state your 5-digit zip code now." | espeak

# Record the response from your C270 webcam mic (hw:2,0) for 5 seconds
# This creates a file named 'numerical_answer.wav'
arecord -D hw:2,0 -f S16_LE -r 16000 -d 5 numerical_answer.wav

echo "Recording complete. The audio is saved as numerical_answer.wav."


