import whisper
import sounddevice as sd
import numpy as np
import tempfile
import wavio
import os
import re

os.system('espeak "Please say a number now"')

duration = 5 
samplerate = 16000

print("Recording... Speak now!")
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
sd.wait()
print("Recording finished!")

with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    wavio.write(f.name, recording, samplerate, sampwidth=2)
    wav_path = f.name

model = whisper.load_model("tiny.en")  
result = model.transcribe(wav_path)
text = result.get("text", "")

numbers_only = "".join(re.findall(r'\d+', text))

if numbers_only:
    print("You said (numbers only):", numbers_only)
    os.system(f'espeak "You said {numbers_only}"')
else:
    print("No numbers detected.")
    os.system('espeak "No numbers detected"')

os.remove(wav_path)

