import os
import wave
import json
import glob
from vosk import Model, KaldiRecognizer

# Define cache model directory and check if the model is in cache
cache_model_path = os.path.expanduser("~/.cache/vosk/vosk-model-small-en-us-0.15")
if not os.path.exists(cache_model_path):
    print("Please run the microphone_test.py first to download the model.")
    exit(1)

# Find the most recently created WAV file in the current directory
wav_files = glob.glob('*.wav')
if not wav_files:
    print("No WAV files found in the current directory.")
    exit(1)

# Get the last created WAV file
latest_wav_file = max(wav_files, key=os.path.getctime)

# Load the latest WAV file
wf = wave.open(latest_wav_file, "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("Audio file must be WAV format mono PCM.")
    exit(1)

# Set up recognizer with the model from the cache
model = Model(cache_model_path)
rec = KaldiRecognizer(model, wf.getframerate())

# Process the audio file
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        print(rec.Result())
    else:
        print(rec.PartialResult())

final_result = rec.FinalResult()
final_text = json.loads(final_result).get('text', '')
print("Final Recognized Text: ", final_text)

# Check if any of the predefined words are in the recognized text
words_list = ["oh", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "zero"]

for word in words_list:
    if word in final_text.split():
        print(f"The word '{word}' is in the recognized text.")
    else:
        print(f"The word '{word}' is not in the recognized text.")
