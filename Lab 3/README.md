# Chatterboxes
Cast of the video: (poor guys tortured by the aferMATH deployer)
Estelle Zhang, Zirui Han

## Part 1.
### Setup 
Activate your virtual environment. (I retain this because I will always use it)
```
pi@ixe00:~$ cd Interactive-Lab-Hub
pi@ixe00:~/Interactive-Lab-Hub $ cd Lab\ 3
pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ python3 -m venv .venv
pi@ixe00:~/Interactive-Lab-Hub $ source .venv/bin/activate
(.venv)pi@ixe00:~/Interactive-Lab-Hub $ 
```
### Text to Speech 
\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
```
#from: https://elinux.org/RPi_Text_to_Speech_(Speech_Synthesis)#Festival_Text_to_Speech
echo "Good morning, oharyo, Zao Shang Hao, Gootten morgen, Eric Chen" | festival --tts
```
---

  
### Speech to Text
\*\***Write your own shell file that verbally asks for a numerical based input (such as a phone number, zipcode, number of pets, etc) and records the answer the respondent provides.**\*\*
```
#!/bin/bash
# ask_number_vosk.sh
# Ask a number, record it, and transcribe with Vosk

QUESTION="Please say a number, such as your phone number or zipcode."
DURATION=5               # seconds to record
OUTFILE="answer.wav"
RESULT="result.txt"

# Speak the question
espeak "$QUESTION"

echo "Recording for $DURATION seconds..."
arecord -d $DURATION -f cd -t wav "$OUTFILE"

echo "Transcribing with Vosk..."
vosk-transcriber -i "$OUTFILE" -o "$RESULT"

echo "Transcription saved to $RESULT"
echo "Detected text:"
cat "$RESULT"
```


### 🤖 NEW: AI-Powered Conversations with Ollama
#### Quick Start with Ollama
#### Ready-to-Use Scripts

#### Integration in Your Projects
\*\***Try creating a simple voice interaction that combines speech recognition, Ollama processing, and text-to-speech output. Document what you built and how users responded to it.**\*\*
```
import speech_recognition as sr
import requests
import pyttsx3

# URL of the local Ollama API
OLLAMA_URL = "http://localhost:11434/api/generate"
# Name of the model you have pulled (change if needed)
MODEL      = "llama3"

def listen():
    """Capture microphone input and convert to text using Google Speech Recognition."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak now...")
        r.adjust_for_ambient_noise(source)  # reduce background noise
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio)
        print("You said:", text)
        return text
    except Exception as e:
        print("Speech recognition failed:", e)
        return ""

def query_ollama(prompt):
    """Send the recognized text to Ollama and collect the streamed response."""
    data = {"model": MODEL, "prompt": prompt}
    resp = requests.post(OLLAMA_URL, json=data, stream=True)
    reply = ""
    for line in resp.iter_lines():
        if not line:
            continue
        part = line.decode("utf-8")
        # Ollama streams JSON lines; extract the "response" field
        if '"response":"' in part:
            reply += part.split('"response":"')[1].split('"')[0]
    print("Ollama:", reply)
    return reply

def speak(text):
    """Speak the response aloud using offline TTS."""
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Main loop: continuously listen → process → speak
print("Start talking (say 'exit' or 'quit' to stop)")
while True:
    user_text = listen()
    if not user_text:
        continue
    if user_text.lower() in ["exit", "quit", "stop"]:
        break
    answer = query_ollama(user_text)
    speak(answer)
```

### Storyboard

Storyboard and/or use a Verplank diagram to design a speech-enabled device. (Stuck? Make a device that talks for dogs. If that is too stupid, find an application that is better than that.) 

\*\***Post your storyboard and diagram here.**\*\*
![633ed1c52f3e6f34551f16214cfc09c1](https://github.com/user-attachments/assets/82466cbe-d8f7-40f5-9147-08a31e8b3b93)


Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses. 

\*\***Please describe and document your process.**\*\*
![95918264d08586473d2e751919934381](https://github.com/user-attachments/assets/54358e9c-3650-4f6b-a449-78afd5768293)


### Acting out the dialogue

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing.  Please record this interaction (for example, using Zoom's record feature).
[Acting out](https://drive.google.com/video/captions/edit?id=1U9JBEsrq14Mv1NO6AZO3RXu17p5BgyGX)
\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*
The participant seems not to enjoy the arithmetics (that's their problems >:( ) and they some times will react with a mixture of words and numbers, because they are calculating, or they are initially confused by the question.


# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.
![ceddb4077bf1370bf7647e50cdba6596](https://github.com/user-attachments/assets/6795ee23-605c-4058-b945-5428bea37b84)


## Prep for Part 2

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings...
2. What are other modes of interaction _beyond speech_ that you might also use to clarify how to interact?
3. Make a new storyboard, diagram and/or script based on these reflections.

```
# -*- coding: utf-8 -*-
import sounddevice as sd
import numpy as np
import json
from vosk import Model, KaldiRecognizer
import re
import time
import random
import pandas as pd
import subprocess
import os
from gtts import gTTS
import warnings
from word2number import w2n

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

digits_vocab = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", 
    "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", 
    "sixty", "seventy", "eighty", "ninety"]     # The stt models are all so bad that I have to use a limited word list

# Settings
SAMPLE_RATE = 16000   # Whisper recommended sample rate
ANSWER_DURATION = 30  # max recording time in seconds

# load vosk model once
model = Model("model")
rec = KaldiRecognizer(model, 16000, json.dumps(digits_vocab))

# Load CSV (must have 2 columns: Question, Answer)
questions = pd.read_csv("questions.csv")

# Counters
count = 0
win = 0

def record_audio(duration=ANSWER_DURATION):
    # Record audio for a fixed duration
    print(f"Recording for {duration} seconds...")
    audio = sd.rec(int(duration * SAMPLE_RATE), 
                   samplerate=SAMPLE_RATE, 
                   channels=1, 
                   dtype='int16')
    sd.wait()
    print("Recording finished.")
    return np.squeeze(audio)

def transcribe_and_extract_numbers(audio):
    # Transcribe speech to text and extract numbers
    print("Transcribing with Vosk...")

    # Ensure audio is PCM bytes (int16)
    audio_bytes = audio.tobytes()

    if rec.AcceptWaveform(audio_bytes):
        result = json.loads(rec.Result())
    else:
        result = json.loads(rec.PartialResult())

    text = result.get("text", "")
    # Extract integers from the text
    try:
        number = w2n.word_to_num(text)
        return number
    except:
        return None

def ask_question(count):
    """Select a random question and return index, question text, correct answer"""
    if count < 6:
        i = random.randint(0, 50)
        d = 10
    elif count < 10:
        i = random.randint(51, 99)
        d= 15
    else:
        i = 99
        d = 25
    q = questions.iloc[i, 0]   # Question text
    a = questions.iloc[i, 1]  # Correct answer (as string)
    return i, q, a, d

def speak(text, filename="output_padded.mp3"):
    """Speak text using gTTS, prepend 0.3s silence with ffmpeg, and play with mpg123"""
    # Save raw mp3
    tts = gTTS(text=text, lang="en")
    tts.save("output_raw.mp3")

    # Prepend 2s silence
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=2",
        "-i", "output_raw.mp3",
        "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]",
        "-map", "[out]",
        filename
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Play with mpg123
    subprocess.run(["mpg123", filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    global count, win
    speak("Hahahaha, I am After Math Deployer! Now torture begins!")
    while True:
        count += 1
        # Select a question
        i, q, a, d= ask_question(count)

        # Speak the question
        print(f"Question: {q}")
        speak(q)

        # Record answer
        audio = record_audio(d)
        nums = transcribe_and_extract_numbers(audio)

        # Evaluate
        print(nums)
        if nums == a:   # compare the extracted number
            win += 1
            print("Correct!")
            speak("Oh Pity! You made it right.")
        else:
            print(f"Wrong. Correct answer was: {a}")
            speak("Heeheehee, Booboo! Wrong Answer, Hahaha!")

        print(f"Score: {win}/{count}")

        if count == 10:
            print("Game over.")
            speak("Enough for today!")
            break

if __name__ == "__main__":
    main()
```

## Prototype your system

[Myself testing the prototype](https://drive.google.com/video/captions/edit?id=1auHtaVb_D5dP7Y4rtOu4LpyDfaS5jWwF)
  

## Test the system
Try to get at least two people to interact with your system. (Ideally, you would inform them that there is a wizard _after_ the interaction, but we recognize that can be hard.)

[Test Video, starred by Estelle](https://drive.google.com/video/captions/edit?id=1HtOWd5qiqxzV8Nk49G2B0hetfA2mPaQ_)
[Test Video, starred by Zirui]https://drive.google.com/video/captions/edit?id=1pMhvXTp2bB1YKboAv1vLF-kOwPaE2E9H

Answer the following:

### What worked well about the system and what didn't?
√ The questions are broadcast well out.
√ The numbers are abstracted from complicated sentences.
X The numbers are misrecognized when the participant does not stay close to the mic.
X Some initial words are not completely spoken by the tts.

### What worked well about the controller and what didn't?
√ Everything goes automatically well, according to the difficulty level.
X Sometimes the final question show up earlier, and sometimes the question repeats.

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

There could be more interactions like inserted dialogues. eg. "Pardon?", "What's the correct answer?"

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?
answer : video and audio abstract

action : continue, stop, repeat, give correct answers...

mood analysis : freq analysis of audio...

A video camera can be used to read the answer, since sometimes participants read when they valculate and may affect the stt process. 

















