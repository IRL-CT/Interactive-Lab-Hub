MODEL_PATH="$HOME/.local/share/piper/voices/en_US/en_US-lessac-medium.onnx"

echo "Hello Maggie, welcome to Lab 3 with Piper!" | piper \
  --model "$MODEL_PATH" \
  --output_file piper_greet.wav

aplay piper_greet.wav
