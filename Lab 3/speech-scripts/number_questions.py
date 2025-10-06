from faster_whisper import WhisperModel

model = WhisperModel(model_size, device="cpu", compute_type="int8")
segments, info = model.transcribe("lookdave.wav", beam_size=5)

echo "whats your social security number" | festival --tts
