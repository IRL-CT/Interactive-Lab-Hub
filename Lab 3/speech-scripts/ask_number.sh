#!/bin/bash

echo "What is your zip code?" | festival --tts

sleep 1

echo "Recording your answer for 5 seconds. Please speak now."

arecord -D plughw:3,0 \
  -f S16_LE \
  -r 16000 \
  -c 1 \
  -d 5 \
  numerical_answer.wav

echo "Recording finished."
