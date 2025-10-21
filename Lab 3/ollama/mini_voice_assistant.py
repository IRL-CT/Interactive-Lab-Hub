import speech_recognition as sr
import subprocess
import requests

OLLAMA_URL = "http://localhost:11434"
MODEL = "phi3:mini"

r = sr.Recognizer()
mic = sr.Microphone(device_index=0)

with mic as source:
    print("Say something...")
    audio = r.listen(source, timeout=5, phrase_time_limit=5)

text = r.recognize_google(audio)
print("You said:", text)

response = requests.post(
    f"{OLLAMA_URL}/api/generate",
    json={"model": MODEL, "prompt": text, "stream": False}
)

reply = response.json()["response"]
clean_reply = reply.encode("ascii", "ignore").decode("ascii")
print("Ollama:", reply)

subprocess.run(["espeak", reply])
