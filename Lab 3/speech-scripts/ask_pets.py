import speech_recognition as sr
import pyttsx3

# Text-to-speech setup
engine = pyttsx3.init()
engine.say("How many pets do you have?")
engine.runAndWait()

# Speech-to-text setup
recognizer = sr.Recognizer()
mic = sr.Microphone()

with mic as source:
    print("🎤 Listening for your answer...")
    audio = recognizer.listen(source)

print("🔁 Transcribing...")
try:
    text = recognizer.recognize_whisper(audio, model="base")
    print("You said:", text)
except Exception as e:
    print("Error:", e)
