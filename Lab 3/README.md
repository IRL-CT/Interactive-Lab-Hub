# Chatterboxes
Cast of the video: (poor guys tortured by the aferMATH deployer)
Estelle Zhang, Zirui Han

## Prep for Part 1: Get the Latest Content and Pick up Additional Parts 
### Pick up Web Camera If You Don't Have One
### Get the Latest Content
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

Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses. 

\*\***Please describe and document your process.**\*\*

### Acting out the dialogue

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing.  Please record this interaction (for example, using Zoom's record feature).

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*

### Wizarding with the Pi (optional)
In the [demo directory](./demo), you will find an example Wizard of Oz project. In that project, you can see how audio and sensor data is streamed from the Pi to a wizard controller that runs in the browser.  You may use this demo code as a template. By running the `app.py` script, you can see how audio and sensor data (Adafruit MPU-6050 6-DoF Accel and Gyro Sensor) is streamed from the Pi to a wizard controller that runs in the browser `http://<YouPiIPAddress>:5000`. You can control what the system says from the controller as well!

\*\***Describe if the dialogue seemed different than what you imagined, or when acted out, when it was wizarded, and how.**\*\*

# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.

## Prep for Part 2

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings...
2. What are other modes of interaction _beyond speech_ that you might also use to clarify how to interact?
3. Make a new storyboard, diagram and/or script based on these reflections.

## Prototype your system

The system should:
* use the Raspberry Pi 
* use one or more sensors
* require participants to speak to it. 

*Document how the system works*

*Include videos or screencaptures of both the system and the controller.*

<details>
  <summary><strong>Submission Cleanup Reminder (Click to Expand)</strong></summary>
  
  **Before submitting your README.md:**
  - This readme.md file has a lot of extra text for guidance.
  - Remove all instructional text and example prompts from this file.
  - You may either delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
  - Your final submission should be neat, focused on your own work, and easy to read for grading.
  
  This helps ensure your README.md is clear professional and uniquely yours!
</details>

## Test the system
Try to get at least two people to interact with your system. (Ideally, you would inform them that there is a wizard _after_ the interaction, but we recognize that can be hard.)

Answer the following:

### What worked well about the system and what didn't?
\*\**your answer here*\*\*

### What worked well about the controller and what didn't?

\*\**your answer here*\*\*

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

\*\**your answer here*\*\*


### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?

\*\**your answer here*\*\*











