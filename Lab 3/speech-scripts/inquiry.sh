#!/bin/bash
pip install piper-tts

# python -m piper.download_voices en_US-lessac-medium

echo 'Hello there! Can you tell me your phone number please?' | \
  piper --model en_US-lessac-medium --output-raw | \
  aplay -r 22050 -f S16_LE -t raw -

echo "Recording now (5 seconds)..."

# Record
arecord -d 5 -f cd -t wav user_answer.wav

echo "convertin speech to text"

# Speech to text with Whisper
echo "convertin speech to text"
whisper user_answer.wav --model base --output_format txt --output_dir . --verbose False

# Get the transcribed text
USER_TEXT=$(cat user_answer.txt)
echo "You said: $USER_TEXT"

# Generate response (you could add AI processing here)
RESPONSE="Your phone number is: $USER_TEXT. Got it!"

# Convert response to speech with Piper
echo "$RESPONSE" | piper --model en_US-lessac-medium --output_file response.wav

# Play the response
aplay response.wav