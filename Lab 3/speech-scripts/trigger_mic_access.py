import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone() as source:
    print("Adjusting for ambient noise...")
    r.adjust_for_ambient_noise(source)
    print("Listening for 3 seconds...")
    audio = r.listen(source, timeout=3)
