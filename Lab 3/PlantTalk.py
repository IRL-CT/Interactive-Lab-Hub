import os
import queue
import sounddevice as sd
import json
import subprocess
import requests
from vosk import Model, KaldiRecognizer

# -----------------------------
# Ollama integration
# -----------------------------
def ask_specialized_ollama(question, personality):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:270m",
                "prompt": question,
                "system": personality,
                "stream": False
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get('response', 'Sorry, no response')
        else:
            return f"Error from Ollama: {response.status_code}"
    except Exception as e:
        return f"Error contacting Ollama: {e}"

# -----------------------------
# Load Vosk model
# -----------------------------
MODEL_PATH = os.path.expanduser("~/vosk-model-en-us")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        "Vosk model not found. Download from https://alphacephei.com/vosk/models and unzip to ~/vosk-model-en-us"
    )

model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, 16000)

# -----------------------------
# Text-to-Speech
# -----------------------------
def speak(text):
    print(f"Plant says: {text}")
    subprocess.run(["espeak", text])

# -----------------------------
# Microphone queue
# -----------------------------
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    q.put(bytes(indata))

def listen_and_transcribe():
    """Listen from mic until a phrase is recognized, return as text."""
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                           channels=1, callback=callback):
        print("Listening...")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get("text"):
                    return result["text"].lower()

# -----------------------------
# Main Plant interaction loop
# -----------------------------
def main():
    print("Plant device is running...")
    asleep = True
 
    while True:
        if asleep:
            choice = input("Wave at the plant? (y/n): ").strip().lower()
            if choice == "y":
                asleep = False
                speak("Good day human! How are you today?")
            else:
                continue

        user_text = listen_and_transcribe()
        print(f"You said: {user_text}")

        if "goodbye" in user_text or "bye" in user_text:
            speak("Goodbye, I am going back to sleep now.")
            asleep = True
        elif "how are you" in user_text:
            speak("I'm leafy and thriving, thank you for asking!")

        elif "water" in user_text:
            speak("Ahh, yes, water! My favorite drink!")

        elif "sun" in user_text:
            speak("I love the sun. I could lowkey use a bit more sunshine on my leaves.")
        else:
            # Ask Ollama for a personality-driven response
            plant_response = ask_specialized_ollama(user_text, "You are a green houseplant. Be funny and practical.")
            speak(plant_response)

if __name__ == "__main__":
    main()

