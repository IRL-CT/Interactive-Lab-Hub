import sounddevice as sd
import numpy as np
import tempfile
import wavio
import os
import re
from faster_whisper import WhisperModel

os.system('espeak "Please say a number now"')

duration = 3  
samplerate = 16000

print("Recording... Speak now!")
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
sd.wait()
print("Recording finished!")

with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    wavio.write(f.name, recording, samplerate, sampwidth=2)
    wav_path = f.name

model = WhisperModel("tiny.en", device="cpu", compute_type="int8")  # int8 模式更快
segments, info = model.transcribe(wav_path)

text = " ".join([segment.text for segment in segments])

numbers_only = "".join(re.findall(r'\d+', text))

if numbers_only:
    print("You said (numbers only):", numbers_only)
    os.system(f'espeak "You said {numbers_only}"')
else:
    print("No numbers detected.")
    os.system('espeak "No numbers detected"')

os.remove(wav_path)
