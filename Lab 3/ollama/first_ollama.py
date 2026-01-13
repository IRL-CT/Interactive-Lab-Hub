import whisper
import os
import requests

# === CONFIG ===
AUDIO_FILE = "user.wav"
WHISPER_MODEL = "tiny"
OLLAMA_MODEL = "phi3:mini"

# === 1. Record audio using arecord ===
os.system("espeak 'Ask AI anything!'")
DURATION = 5
os.system(f"arecord -f cd -d {DURATION} -r 16000 -c 1 {AUDIO_FILE}")

# === 2. Load Whisper model ===
model = whisper.load_model(WHISPER_MODEL)

# === 3. Transcribe audio ===
result = model.transcribe(AUDIO_FILE)
user_text = result["text"].strip()
print("You said:", user_text)

# === 4. Send transcription to Ollama ===
response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": OLLAMA_MODEL, "prompt": user_text, "stream": False}
)
ai_response = response.json().get("response", "Sorry, no response")

# === 5. Speak AI response ===
safe_response = ai_response.encode("utf-8", errors="replace").decode("utf-8")
print("AI says:", ai_response)
os.system(f'espeak "{ai_response}"')
