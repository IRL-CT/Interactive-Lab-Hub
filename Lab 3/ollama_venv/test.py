import pyaudio
# test_components.py
import speech_recognition as sr

# Test microphone
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something!")
    audio = r.listen(source, timeout=5)
    try:
        text = r.recognize_google(audio)
        print(f"Heard: {text}")
    except Exception as e:
        print(f"Error: {e}")