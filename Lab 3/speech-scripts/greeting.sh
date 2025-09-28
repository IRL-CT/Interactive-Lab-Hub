pip install piper-tts

# python -m piper.download_voices en_US-lessac-medium

echo 'Hello Eva!' | piper \
  --model en_US-lessac-medium \
  --output_file greeting.wav

sleep 0.5

aplay greeting.wav