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

## Prep for Part 2

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings...
2. What are other modes of interaction _beyond speech_ that you might also use to clarify how to interact?
3. Make a new storyboard, diagram and/or script based on these reflections.

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















