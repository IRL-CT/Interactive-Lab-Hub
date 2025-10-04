#!/bin/bash

# Use TTS to ask the question
echo "Please state your 5-digit zip code now." | espeak

# Record the response 
arecord -D hw:2,0 -f S16_LE -r 16000 -d 5 numerical_answer.wav

echo "Recording complete. The audio is saved as numerical_answer.wav."


