import subprocess
import vosk
import sys
import sounddevice as sd
import ollama
import pyttsx3
import queue
import json

# --------------------
# 1. Speech recognition setup
# --------------------
model = vosk.Model("model")   # path to your vosk model (downloaded separately)
samplerate = 16000
q = queue.Queue()

def callback(indata, frames, time, status):
    q.put(bytes(indata))

# --------------------
# 2. Start mic stream
# --------------------
rec = vosk.KaldiRecognizer(model, samplerate)

print("🎤 Say something... (Ctrl+C to stop)")
with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                       channels=1, callback=callback):
    while True:
        data = q.get()
        if rec.AcceptWaveform(data):
            result = rec.Result()
            text = json.loads(result).get("text", "")
            if text:
                print(f"You said: {text}")

                # --------------------
                # 3. Send to Ollama
                # --------------------
                response = ollama.chat(model="llama3", messages=[
                    {"role": "user", "content": text}
                ])
                reply = response['message']['content']
                print(f"Ollama: {reply}")

                # --------------------
                # 4. Text-to-speech
                # --------------------
                engine = pyttsx3.init()
                engine.say(reply)
                engine.runAndWait()
