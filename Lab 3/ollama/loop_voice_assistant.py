#!/usr/bin/env python3

import speech_recognition as sr
import subprocess
import requests

OLLAMA_URL = "http://localhost:11434"
MODEL = "phi3:mini"

r = sr.Recognizer()
mic = sr.Microphone(device_index=0)

print("Looping Voice Assistant started. Say 'exit' to quit.")

while True:
    with mic as source:
        print("Say something...")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        except Exception as e:
            print("⏱️ Timeout, no speech detected.")
            continue

    try:
        text = r.recognize_google(audio)
    except Exception as e:
        print("❌ Could not recognize speech:", e)
        continue

    print("You said:", text)

    if text.lower().strip() in ["exit", "quit", "bye"]:
        print("👋 Exiting assistant.")
        subprocess.run(["espeak", "Goodbye!"])
        break

    # Send to Ollama
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODEL, "prompt": text, "stream": False}
    )
    reply = response.json()["response"]
    clean_reply = reply.encode("ascii", "ignore").decode("ascii")

    print("Ollama:", clean_reply)
    subprocess.run(["espeak", clean_reply])
