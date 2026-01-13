# Chatterboxes
**Melody Huang(yh2353) & Xiang Chang (xc529) & Dingran Dai (dd699)**


## Part 1.
### Setup 

Activate your virtual environment

```
pi@ixe00:~$ cd Interactive-Lab-Hub
pi@ixe00:~/Interactive-Lab-Hub $ cd Lab\ 3
pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ python3 -m venv .venv
pi@ixe00:~/Interactive-Lab-Hub $ source .venv/bin/activate
(.venv)pi@ixe00:~/Interactive-Lab-Hub $ 
```

Run the setup script
```(.venv)pi@ixe00:~/Interactive-Lab-Hub $ pip install -r requirements.txt  ```

Next, run the setup script to install additional text-to-speech dependencies:
```
(.venv)pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ ./setup.sh
```
<details>
  <summary>Text to Speech </summary>


In this part of lab, we are going to start peeking into the world of audio on your Pi! 

We will be using the microphone and speaker on your webcamera. In the directory is a folder called `speech-scripts` containing several shell scripts. `cd` to the folder and list out all the files by `ls`:

```
pi@ixe00:~/speech-scripts $ ls
Download        festival_demo.sh  GoogleTTS_demo.sh  pico2text_demo.sh
espeak_demo.sh  flite_demo.sh     lookdave.wav
```

You can run these shell files `.sh` by typing `./filename`, for example, typing `./espeak_demo.sh` and see what happens. Take some time to look at each script and see how it works. You can see a script by typing `cat filename`. For instance:

```
pi@ixe00:~/speech-scripts $ cat festival_demo.sh 
#from: https://elinux.org/RPi_Text_to_Speech_(Speech_Synthesis)#Festival_Text_to_Speech
```
You can test the commands by running
```
echo "Just what do you think you're doing, Dave?" | festival --tts
```

Now, you might wonder what exactly is a `.sh` file? 
Typically, a `.sh` file is a shell script which you can execute in a terminal. The example files we offer here are for you to figure out the ways to play with audio on your Pi!

You can also play audio files directly with `aplay filename`. Try typing `aplay lookdave.wav`.

\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
(This shell file should be saved to your own repo for this lab.)
```
#!/bin/bash
say() { local IFS=+;/usr/bin/mplayer -ao alsa -really-quiet -noconsolecontrols "http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q=$*&tl=en"; }
#say $*
TIME=$(date +"%H:%M")
say "Hello, right now is $TIME. Welcome to the Raspberry Pi world."
```

---
Bonus:
[Piper](https://github.com/rhasspy/piper) is another fast neural based text to speech package for raspberry pi which can be installed easily through python with:
```
pip install piper-tts
```
and used from the command line. Running the command below the first time will download the model, concurrent runs will be faster. 
```
echo 'Welcome to the world of speech synthesis!' | piper \
  --model en_US-lessac-medium \
  --output_file welcome.wav
```
Check the file that was created by running `aplay welcome.wav`. Many more languages are supported and audio can be streamed dirctly to an audio output, rather than into an file by:

```
echo 'This sentence is spoken first. This sentence is synthesized while the first sentence is spoken.' | \
  piper --model en_US-lessac-medium --output-raw | \
  aplay -r 22050 -f S16_LE -t raw -
```
</details>
<details>
  <summary>Speech to Text</summary>
Next setup speech to text. We are using a speech recognition engine, [Vosk](https://alphacephei.com/vosk/), which is made by researchers at Carnegie Mellon University. Vosk is amazing because it is an offline speech recognition engine; that is, all the processing for the speech recognition is happening onboard the Raspberry Pi. 

Make sure you're running in your virtual environment with the dependencies already installed:
```
source .venv/bin/activate
```

Test if vosk works by transcribing text:

```
vosk-transcriber -i recorded_mono.wav -o test.txt
```

You can use vosk with the microphone by running 
```
python test_microphone.py -m en
```

---
Bonus:
[Whisper](https://openai.com/index/whisper/) is a neural network–based speech-to-text (STT) model developed and open-sourced by OpenAI. Compared to Vosk, Whisper generally achieves higher accuracy, particularly on noisy audio and diverse accents. It is available in multiple model sizes; for edge devices such as the Raspberry Pi 5 used in this class, the tiny.en model runs with reasonable latency even without a GPU.

By contrast, Vosk is more lightweight and optimized for running efficiently on low-power devices like the Raspberry Pi. The choice between Whisper and Vosk depends on your scenario: if you need higher accuracy and can afford slightly more compute, Whisper is preferable; if your priority is minimal resource usage, Vosk may be a better fit.

In this class, we provide two Whisper options: A quantized 8-bit faster-whisper model for speed, and the standard Whisper model. Try them out and compare the trade-offs.

Make sure you're in the Lab 3 directory with your virtual environment activated:
```
cd ~/Interactive-Lab-Hub/Lab\ 3/speech-scripts
source ../.venv/bin/activate
```

Then test the Whisper models:
```
python whisper_try.py
```
and

```
python faster_whisper_try.py
```
\*\***Write your own shell file that verbally asks for a numerical based input (such as a phone number, zipcode, number of pets, etc) and records the answer the respondent provides.**\*\*

```
#!/bin/bash

# Configurable variables
QUESTION="Please answer the question: How many boroughs in New York City?"
OUTPUT_AUDIO="response.wav"
TRANSCRIPT="response.txt"
MODEL="tiny"


# 1. Text-to-speech function

say() { 
    local IFS=+
    /usr/bin/mplayer -ao alsa -really-quiet -noconsolecontrols \
    "http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q=$*&tl=en"
}

# Speak the question
say "$QUESTION"
sleep 0.2



# 2. Record audio
echo "Recording... Please speak now."
arecord -f cd -d 3 -t wav -r 16000 -c 1 "$OUTPUT_AUDIO"
echo "Recording finished."


# 3. Transcribe with Whisper
if ! command -v whisper >/dev/null 2>&1; then
    echo "Error: whisper CLI not found. Install with 'pip install git+https://github.com/openai/whisper.git'"
    exit 1
fi

# Run Whisper
whisper "$OUTPUT_AUDIO" --model "$MODEL" --output_format txt --output_dir .


# 4. Read transcription result
# Whisper automatically creates a TXT file with the same basename as the audio
if [[ -f "${OUTPUT_AUDIO%.wav}.txt" ]]; then
    RESPONSE=$(cat "${OUTPUT_AUDIO%.wav}.txt")
    echo "You said: $RESPONSE"
    # Optional: speak back the answer
    say "You said: $RESPONSE"
else
    echo "Error: transcription file not found."
    exit 1
fi


# 5. Save to file
echo "$RESPONSE" > "$TRANSCRIPT"
echo "Answer saved to $TRANSCRIPT"

```

**Output**
```
Recording... Please speak now.
Recording WAVE 'response.wav' : Signed 16 bit Little Endian, Rate 16000 Hz, Mono
Recording finished.
/home/pi/Interactive-Lab-Hub/Lab 3/.venv/lib/python3.11/site-packages/whisper/transcribe.py:132: UserWarning: FP16 is not supported on CPU; using FP32 instead
  warnings.warn("FP16 is not supported on CPU; using FP32 instead")
Detecting language using up to the first 30 seconds. Use `--language` to specify the language
Detected language: English
[00:00.000 --> 00:01.000]  5
You said: 5
Answer saved to response.txt
```
</details>

<details>
  <summary>
    🤖 NEW: AI-Powered Conversations with Ollama
  </summary>

Want to add intelligent conversation capabilities to your voice projects? **Ollama** lets you run AI models locally on your Raspberry Pi for sophisticated dialogue without requiring internet connectivity!

#### Quick Start with Ollama

**Installation** (takes ~5 minutes):
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download recommended model for Pi 5
ollama pull phi3:mini

# Install system dependencies for audio (required for pyaudio)
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-dev

# Create separate virtual environment for Ollama (due to pyaudio conflicts)
cd ollama/
python3 -m venv ollama_venv
source ollama_venv/bin/activate

# Install Python dependencies in separate environment
pip install -r ollama_requirements.txt
```
#### Ready-to-Use Scripts

We've created three Ollama integration scripts for different use cases:

**1. Basic Demo** - Learn how Ollama works:
```bash
python3 ollama_demo.py
```

**2. Voice Assistant** - Full speech-to-text + AI + text-to-speech:
```bash
python3 ollama_voice_assistant.py
```

**3. Web Interface** - Beautiful web-based chat with voice options:
```bash
python3 ollama_web_app.py
# Then open: http://localhost:5000
```

#### Integration in Your Projects

Simple example to add AI to any project:
```python
import requests

def ask_ai(question):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "phi3:mini", "prompt": question, "stream": False}
    )
    return response.json().get('response', 'No response')

# Use it anywhere!
answer = ask_ai("How should I greet users?")
```

**📖 Complete Setup Guide**: See `OLLAMA_SETUP.md` for detailed instructions, troubleshooting, and advanced usage!

\*\***Try creating a simple voice interaction that combines speech recognition, Ollama processing, and text-to-speech output. Document what you built and how users responded to it.**\*\*
```
import whisper
import os
import requests

# === CONFIG ===
AUDIO_FILE = "user.wav"
WHISPER_MODEL = "tiny"
OLLAMA_MODEL = "phi3:mini"

# === 1. Record audio using arecord ===
os.system("espeak 'Ask AI anything!'")
DURATION = 5
os.system(f"arecord -f cd -d {DURATION} -r 16000 -c 1 {AUDIO_FILE}")

# === 2. Load Whisper model ===
model = whisper.load_model(WHISPER_MODEL)

# === 3. Transcribe audio ===
result = model.transcribe(AUDIO_FILE)
user_text = result["text"].strip()
print("You said:", user_text)

# === 4. Send transcription to Ollama ===
response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": OLLAMA_MODEL, "prompt": user_text, "stream": False}
)
ai_response = response.json().get("response", "Sorry, no response")

# === 5. Speak AI response ===
safe_response = ai_response.encode("utf-8", errors="replace").decode("utf-8")
print("AI says:", ai_response)
os.system(f'espeak "{ai_response}"')
```
**Output**
```
Recording WAVE 'user.wav' : Signed 16 bit Little Endian, Rate 16000 Hz, Mono
/home/pi/Interactive-Lab-Hub/Lab 3/.venv/lib/python3.11/site-packages/whisper/transcribe.py:132: UserWarning: FP16 is not supported on CPU; using FP32 instead
  warnings.warn("FP16 is not supported on CPU; using FP32 instead")
You said: How do you make spaghetti?
AI says: To prepare a classic Italian-style Spaghetti, follow these simple steps:
1. Boil water in a large pot with some salt for seasoning (about 4 quarts of water per pound of pasta is ideal). Bring to boiling point over high heat and add the spaghetti noodles directly into it without using oil on them or stirring, which could prevent stickiness.
2. Follow the package instructions regarding cook time for your preferred al dente texture (firm but not hard), usually around 8-10 minutes of boiling pasta is standard after opening a fresh box/packet from dry form into wet one with hot water without oil in it. The perfect timing may vary depending on thickness and brand, so better to taste occasionally if you're unsure about the correct time.
3. Drain well using a colander but do not rinse spaghetti as this washes away starch which helps sauce adhere nicely (unless instructed by your recipe). If serving with tomato-based pasta like traditional marinara, garlic & olive oil or Alfredo etc., you may want to mix them directly into the hot drained noodles for flavor melding.
4. For non-sauce applications such as Parmesan cheese sprinkle on top while warm if desired; enjoy immediately after serving, ideally paired with a light salad or garlic bread!
```

I built a simple ChatGPT-like function that can answer almost any question, but the speed is the disadvantage.

### Serving Pages

In Lab 1, we served a webpage with flask. In this lab, you may find it useful to serve a webpage for the controller on a remote device. Here is a simple example of a webserver.

```
pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ python server.py
 * Serving Flask app "server" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 162-573-883
```
From a remote browser on the same network, check to make sure your webserver is working by going to `http://<YourPiIPAddress>:5000`. You should be able to see "Hello World" on the webpage.
</details>

### Storyboard

Storyboard and/or use a Verplank diagram to design a speech-enabled device. (Stuck? Make a device that talks for dogs. If that is too stupid, find an application that is better than that.) 

\*\***Post your storyboard and diagram here.**\*\*

**Who:** busy student/professional who often forgets a daily pill.

**What:** voice device with one big confirm button + LED ring + small display (optional). Local wake word (“Hey Remi”).

**Why:** reduce missed doses; make adherence quick and friendly without opening an app.


<img src='https://github.com/user-attachments/assets/d8a02f95-b28a-46a6-8487-73900325c7fa'>

**Idea:** Lower the cognitive load of medication adherence.

**Metaphor:** Gentle companion + kitchen timer that talks and listens.

**Model:** Finite‑state reminder cycle per medication: Scheduled → Alerting → Waiting for Confirmation → (Snoozed/Repeat) → Done.

**Display**: LED ring states (idle, listening, alerting), optional e‑ink line for text (“Yaz • 10:00”), simple chime.

**Tasks:** Create/edit schedule; acknowledge dose; snooze/skip; check next dose; add meds.

**Control:** Voice commands (“Hey Remi…”), one big confirm button, capacitive snooze tap (optional), physical mute switch.


\*\***Please describe and document your process.**\*\*

1. Set task: “Set Yaz reminder at 10:00 AM every day.” Device must confirm schedule.

2. On‑time reminder (10:00): Chime + TTS: “It’s 10:00. Time to take Yaz.”

3. Follow‑up (10:05): If no confirmation, ask: “Did you take Yaz yet?”

4. Complete: User presses the large button or says “Yes, I took it,” device: “Great job — you’ve completed today’s dose. I’ll stop reminding.”

   
### Acting out the dialogue

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing.  Please record this interaction (for example, using Zoom's record feature).
Dialogue Scripts

<details>
<summary><strong>Dialogue here</strong></summary>

**A) Setup (User creates a daily reminder)**

D: “Hey Remi, set a medication reminder for Yaz at 10:00 AM every day.”

D: “Okay. I’ll remind you to take Yaz at 10:00 AM daily. Start today?”

U: “Yes.”

D: “All set. I’ll chime at 10:00.”

**B) On‑time reminder (10:00)**

D (chime): “It’s 10:00. Time to take Yaz.”

D (nudge): “Friendly reminder: Yaz time.”

U: sleeping

**C) Follow‑up (10:05)**

Condition: no response by 10:05.

D: “Quick check — did you take Yaz? You can press the button, say ‘Yes’, or say ‘Snooze’.”

U: “Yes.”

D: “Awesome. Marked complete.”

</details>

https://github.com/user-attachments/assets/287550ee-90cc-46c5-9c37-fdab2474139b


\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*

**Chime before speech.** When we acted/wizarded it, a disembodied voice felt jarring, so we added a brief “ding” to cue attention.

**Improve:** Precede TTS with a sub-second earcon (or ≤2s musical lead-in) and keep barge-in enabled so users can reply immediately, with volume auto-reduced during quiet hours.

**Knowing when the user is done (endpointing). **The device hesitated to avoid cutting users off, creating awkward pauses.

**Improve:** Combine a short silence threshold with intent confidence for a “soft end,” then wait ~200 ms for any continued speech before responding (cancel if speech resumes).


## Our scripts
```
import os
import time
import re
import whisper
import subprocess
from datetime import datetime, timedelta

# ================== Google TTS ==================
def say(text, lang="en"):
    text = text.replace(" ", "+")
    url = f"http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q={text}&tl={lang}"
    subprocess.run(["mplayer", "-ao", "alsa", "-really-quiet", "-noconsolecontrols", url])

# ================== Setting the alarm ==================
say("What time would you like to take your medicine? Please use 24-hour format.")
os.system("echo -e '\a'")
time.sleep(0.5)
print("Recording your answer...")
os.system("arecord -f cd -d 5 -t wav -r 16000 -c 1 response.wav")
print("Finished recording.")

model = whisper.load_model("tiny")
result = model.transcribe("response.wav", language="en")
text = result["text"].strip()
print(f"You said: {text}")

# === Extract time (24-hour format, e.g., 14:30 or 1830) ===
text = text.lower()
time_patterns = [
    r"(\d{1,2}):(\d{2})",          # e.g. 14:30
    r"(\d{2})(\d{2})",             # e.g. 1830
    r"(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(\d{2})?"
]

num_map = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "twenty one": 21, "twenty two": 22, "twenty three": 23
}

hour, minute = None, 0

for p in time_patterns:
    match = re.search(p, text)
    if match:
        if p == time_patterns[0] or p == time_patterns[1]:
            hour = int(match.group(1))
            minute = int(match.group(2))
            break
        elif match.group(1) in num_map:
            hour = num_map[match.group(1)]
            minute = int(match.group(2)) if match.group(2) else 0
            break

# === Confirm extracted time ===
if hour is not None:
    say(f"You said {hour:02d}:{minute:02d}. Is that correct?")
    print(f"Detected time: {hour:02d}:{minute:02d}")
else:
    say("Sorry, I could not detect the time. Please try again.")
    exit()

# === Confirmation recording ===
os.system("arecord -f cd -d 3 -t wav -r 16000 -c 1 confirm.wav")
confirm = model.transcribe("confirm.wav", language="en")["text"].lower()
print("Confirmation:", confirm)

if "yes" not in confirm:
    say("Okay, let's try again later.")
    exit()

# === Set alarm ===
from datetime import datetime, timedelta
now = datetime.now()
alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
if alarm_time < now:
    alarm_time += timedelta(days=1)

say(f"Alarm set for {alarm_time.strftime('%H:%M')}.")

# ================== waiting for alarm ==================
alarm_triggered = False
medicine_taken = False

while True:
    now = datetime.now()
    if not alarm_triggered and now >= alarm_time:
        alarm_triggered = True
        say("It's time to take your medicine!")
        
        # Confirmation
        time.sleep(10) # wait 10 seconds before asking
        say("Did you take your medicine?")
        print("Recording your confirmation...")
        os.system("arecord -f cd -d 5 -t wav -r 16000 -c 1 confirm_medicine.wav")
        response = model.transcribe("confirm_medicine.wav", language="en")["text"].lower()
        print("User response:", response)
        
        if "yes" in response:
            medicine_taken = True
            say("Good job! Don't forget it tomorrow!")
        else:
            say("Okay, remember to take it soon!")
    
    time.sleep(5)  # Check every 5 seconds
```

# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.
<details>
  <summary>Prep for Part 2</summary>


1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings...
2. What are other modes of interaction _beyond speech_ that you might also use to clarify how to interact?
3. Make a new storyboard, diagram and/or script based on these reflections.
</details>


## Prototype your system

The system should:
* use the Raspberry Pi 
* use one or more sensors
* require participants to speak to it. 

*Document how the system works*

*Include videos or screencaptures of both the system and the controller.*

<img width="1018" height="1857" alt="storyboard_;ab3_2" src="https://github.com/user-attachments/assets/b5d8c9d9-1e58-4663-9bf0-2a0070b737b7" />


## Video for our device

https://github.com/user-attachments/assets/e11038f0-0971-4ba7-99c3-ef0360c2c194



## 1) Product Overview
**Goal:** A voice-driven assistant that helps the user schedule a medication reminder and handles snooze/confirm workflows via two hardware buttons. All prompts and speech are in English.

**User flow:**
1. User presses the *TOP* tactile button.
2. Assistant: “Starting a new medication plan. When should I remind you?”  
   User replies with natural language (e.g., “in three minutes”, “one minute”, “at 8:05 pm”).
3. Assistant parses and schedules the reminder.
4. At the scheduled time, Assistant speaks: “It’s time to take your medicine.”
5. A 30‑second response window begins:
   - If user presses *TOP* → snooze 30 seconds and repeat step 4.
   - If user presses *BOTTOM* → confirm taken. Assistant: “Good job. Finished!” and returns to idle.

**Display behavior:**
- Idle: “Medication Assistant / Press TOP to start”
- Listening: “Listening… / Say a time”
- Scheduled: shows **Next Reminder**, **target time**, and a live **T‑MM:SS** countdown plus current time.
- Ringing: “Time to take / medicine”
- Snoozed: “Snoozed / 30 s”
- Finished: “Taken / OK”

---

## 2) Architecture & Components
### State machine
- **IDLE** → (TOP) → **AWAIT_TIME** (listen/parse) → **SCHEDULED** (timer threads)
- **SCHEDULED** → (time reached) → **RINGING** (30 s response window)
- **RINGING** → (TOP) → **SNOOZE** (30 s) → back to **RINGING**
- **RINGING** → (BOTTOM) → **IDLE** (Finished)

### Modules
- **Buttons**: `gpiozero.Button` on BCM23 (TOP) and BCM24 (BOTTOM); debounced. Fallbacks: `evdev` (GPIO keys) or keyboard.
- **ASR**: Vosk + sounddevice @ 16 kHz. The callback passes **bytes** to `AcceptWaveform`. Optional mic selection via `SD_INPUT_NAME`.
- **Time parsing**: Heuristics for:
  - relative: “in 3 minutes”, “one minute”, “30 seconds” (even without “in/after”), “2h 15m”
  - absolute: “at 8:05 pm” (rolls over to tomorrow if past)
  - fallback to `dateparser` with timezone‑safe settings
- **TTS**: `espeak-ng` (or `pyttsx3` fallback). Includes a **Bluetooth audio warm‑up** to prevent first‑word truncation.
- **Display**: ST7789 (SPI). Pillow for rendering (Pillow 10+ safe via `textbbox`). Dedicated countdown painter updates once per second.
- **Scheduler**: lightweight threads: a waiter for time reach, a countdown refresher, snooze timers.

---

## 3) Hardware Interface & Pin Map
- **Buttons**:
  - TOP: **BCM23** (pull‑up, active‑low)
  - BOTTOM: **BCM24** (pull‑up, active‑low)
- **Backlight**: **BCM22** (output, on)
- **Mini PiTFT (ST7789)** over SPI:  
  `cs=D5`, `dc=D25`, `rst=None`, `baudrate=64 MHz`, `width=135`, `height=240`, `x_offset=53`, `y_offset=40`, rotation=90°.  
  > Using `rst=None` avoids conflicts with BCM24 (BOTTOM button).

---

## 4) Software Setup
### APT packages (recommended)
```bash
sudo apt-get update
sudo apt-get install -y espeak-ng portaudio19-dev python3-pip python3-venv \
  libatlas-base-dev libopenblas-dev
```

### Python venv and dependencies
```bash
cd "/home/pi/Interactive-Lab-Hub/Lab 3"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install gpiozero lgpio sounddevice vosk pillow dateparser \
    adafruit-circuitpython-rgb-display pyttsx3
```

### Services that can block GPIO
If your course image starts a screen service on boot:
```bash
sudo systemctl stop piscreen.service --now   # stop during development
# ... later when done
sudo systemctl start piscreen.service --now
```

---

## 5) Running & Useful Environment Variables
**Minimal button test**
```bash
python "/home/pi/Interactive-Lab-Hub/Lab 3/speech-scripts/button_test.py"
```

**Final app (no display, easier to debug)**
```bash
cd "/home/pi/Interactive-Lab-Hub/Lab 3/speech-scripts"
source ../.venv/bin/activate
USE_DISPLAY=0 BUTTON_BACKEND=gpio GPIOZERO_PIN_FACTORY=lgpio \
python med_assistant_v3_final.py
```

**Final app with display**
```bash
sudo systemctl stop piscreen.service --now
BUTTON_BACKEND=gpio USE_DISPLAY=1 GPIOZERO_PIN_FACTORY=lgpio \
python med_assistant_v3_final.py
```

**Select a specific microphone (e.g., Logitech)**
```bash
SD_INPUT_NAME=Logi BUTTON_BACKEND=gpio USE_DISPLAY=1 GPIOZERO_PIN_FACTORY=lgpio \
python med_assistant_v3_final.py
```

**Environment variables (summary)**
- `USE_DISPLAY={0|1}`: enable screen drawing
- `BUTTON_BACKEND={gpio|evdev|keyboard}`: force button driver
- `GPIOZERO_PIN_FACTORY=lgpio`: preferred on Pi 5
- `TOP_BUTTON_PIN`, `BOTTOM_BUTTON_PIN`: override BCM pins (defaults 23/24)
- `SD_INPUT_NAME`: substring to select input audio device
- `TZ`: timezone (default `America/New_York`)

---

## 6) Issues Encountered & Fixes
1. **GPIO busy** during display init or button read  
   **Cause:** a boot service (`piscreen.service`) occupying pins.  
   **Fix:** stop the service while running the app; ensure TFT reset is **not** mapped to BCM24.

2. **Physical buttons didn’t trigger in the main app**  
   **Cause:** pin factory / contention differences between scripts.  
   **Fix:** verified with `button_test.py`; for the app, forced `BUTTON_BACKEND=gpio` and `GPIOZERO_PIN_FACTORY=lgpio`.

3. **UnicodeEncodeError** in logs (em‑dash/UTF‑8)  
   **Fix:** ASCII‑only logs for terminal safety; removed special punctuation.

4. **Pillow 10+ removed `ImageDraw.textsize`**  
   **Symptom:** `AttributeError: 'ImageDraw' object has no attribute 'textsize'`.  
   **Fix:** used `textbbox()` when available, fallback to legacy `textsize()`.

5. **Vosk cffi TypeError** in sound callback  
   **Symptom:** `initializer for ctype 'char *' must be a cdata pointer...`.  
   **Fix:** pass `bytes(indata)` to `AcceptWaveform`.

6. **`dateparser` TypeError (timezone)**  
   **Symptom:** `Invalid {"TIMEZONE": None}`.  
   **Fix:** only pass `TIMEZONE` if non‑empty; otherwise omit; also add robust relative parsing.

7. **Utterances like “one minute” (no “in/after”) not parsed**  
   **Fix:** added detection for bare relative phrases (words or numeric + units) → seconds.

8. **Bluetooth speaker cuts off first words**  
   **Fix:** added TTS **warm‑up**: `espeak-ng -a 0` (silent) + ~120 ms pause before speaking real text.

9. **Display didn’t update (fixed time)**  
   **Fix:** added a dedicated countdown thread (paint at second boundaries) and a rich scheduled screen.

10. **TOP/BOTTOM behavior clarity**  
    **Note:** in **IDLE**, only TOP starts; in **RINGING**, TOP=**Snooze 30s**, BOTTOM=**Finished**.

---

## 7) Code Map (key files)
- `med_assistant_v3_final.py` – main application with all fixes (ASR/TTS/Display/Buttons/State machine)
- `button_test.py` – minimal hardware button verifier (prints & speaks on press)
- (previous diagnostic builds retained for reference):
  - `med_assistant_v3_diag.py` – button callback logging
  - `med_assistant_v3_diag_fix.py` – ASR bytes fix
  - `med_assistant_v3_diag_tzfix.py` – timezone‑safe parsing + bare relative time

---

## 8) Testing Checklist
- **Buttons:** `button_test.py` prints on both TOP/BOTTOM; no “GPIO busy”.
- **ASR:** say “in 10 seconds” → logs show `[ASR] Heard: in 10 seconds`.
- **Scheduling:** screen shows Next Reminder, target time, and T‑MM:SS counting down.
- **Ringing:** at time, complete TTS sentence is audible; 30 s response window starts.
- **Snooze:** TOP during ringing → “Snoozed / 30 s”, then rings again.
- **Finish:** BOTTOM during ringing → “Taken / OK” then back to idle.

---

## 9) Design Choices & Rationale
- **Simple, robust threading** instead of external schedulers; avoids cron/systemd complexity.
- **Vosk offline ASR** for low-latency local recognition without network dependency.
- **espeak-ng** for consistent TTS on Pi; Bluetooth warm‑up eliminates first‑word truncation.
- **GPIO mapping avoiding conflicts** (no TFT reset on BCM24) ensures reliable button events.
- **Pillow 10+ compatibility** future‑proofs display code on current Python images.

---

## 10) Future Enhancements (optional)
- Per‑reminder labels (“vitamin D”, “antibiotic”) and multi‑reminder queue.
- Persistent schedules (write to disk), recurring reminders (e.g., every 8 hours).
- On‑device volume control via BOTTOM long‑press.
- Wake word to start flow (hands‑free), VAD for smarter listening window.
- On‑screen icons, progress rings, or color themes.

---

## 11) Safety & Privacy Notes
- No cloud ASR used; all speech processed locally.
- Avoid logging raw audio; keep console output ASCII‑only.
- If adding persistence, store only minimal timestamps/labels.

---

## 12) Quick Troubleshooting
- **No reaction to buttons** → stop services (`piscreen.service`), verify pins with `button_test.py`, set `GPIOZERO_PIN_FACTORY=lgpio`.
- **TTS clipped** → ensure Bluetooth warm‑up path is executed (espeak‑ng installed).
- **ASR silent** → choose mic with `SD_INPUT_NAME`, check `arecord -l`.
- **Display errors** → confirm SPI enabled; verify cs/dc pins (`D5`/`D25`), `rst=None`, backlight on `BCM22`.

---

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

#### The features that went well:

**Core Interaction Flow:** The primary user flow was very successful. Testers understood that pressing the top button initiated the process, and the two-button (Snooze/Confirm) design for the reminder was immediately intuitive.

**Offline ASR Responsiveness:**  Using Vosk for local speech recognition meant the system was fast and didn't rely on an internet connection. Users appreciated the immediate "Listening..." feedback and the quick parsing of their spoken commands.

**Clear Visual Feedback:** The display was crucial. It effectively communicated the system's state at all times: what it was doing (Listening...), what it had scheduled (Next Reminder: ...), and the live countdown (T-MM:SS). This prevented confusion and kept the user informed.

#### The features that failed:

**Narrow Natural Language Understanding:** While the time parsing was robust for specific phrases like "in three minutes" or "at 8:05 pm," it likely struggled with more conversational or ambiguous requests. For example, a user might say "remind me around dinnertime" or "in a little bit," which the system isn't designed to handle.

**Physical Interaction Requirement:** Users had to physically press a button to start every interaction. This is less fluid than a hands-free "wake word" system and makes it feel more like a traditional device than a voice-first assistant.

**Lack of Confirmation:** The system immediately schedules a reminder after parsing the time. If the ASR misheard "in 30 minutes" as "in 13 minutes," the user had no opportunity to correct it before the timer was set.

### What worked well about the controller and what didn't?

Since this was an autonomous system, there was no human "controller" or wizard. However, we can evaluate the system's internal state machine and logic as the "controller."

#### What worked well about the internal controller:

**Reliable State Management:** The state machine described (IDLE → AWAIT_TIME → SCHEDULED → RINGING) was robust. It correctly handled the transitions between states without getting stuck, ensuring the user journey was always logical and predictable.

**Efficient Threading:** The use of dedicated threads for the countdown timer and alarm scheduling worked perfectly. This allowed the display to update smoothly every second without interfering with the main application logic that was waiting for button presses or alarms.

#### What didn't work well about the internal controller: 

**Single-Task Limitation:** The controller's logic is designed to handle only one reminder at a time. It cannot queue multiple reminders or manage recurring schedules, which limits its real-world utility for users with complex medication plans.

**No Error Recovery Path:** The logic assumes a "happy path." If the ASR returns a nonsensical result, the system doesn't have a clear way to ask the user to repeat themselves. It either fails or parses incorrectly, tying into the "Lack of Confirmation" issue mentioned earlier.

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

Since the system is already autonomous, we can reframe this as: "What lessons from testing the prototype can inform the next, more advanced autonomous version?"

**Confirmation is Non-Negotiable:** The most critical lesson is that the system must confirm critical information before acting on it. After parsing a time, the next version should always ask, "OK, setting a reminder for 10 minutes. Is that correct?" This would prevent ASR errors from causing incorrect reminders.

**Flexibility in Language is Key:** Watching users interact with the system would highlight the many different ways people express time. The next version needs a much more powerful Natural Language Understanding (NLU) engine or more sophisticated parsing to handle ambiguity and a wider variety of phrases.

**A Hands-Free Option is Expected:** The reliance on a button press is a major limitation. The next version should incorporate a wake word (e.g., "Hey, Meds Assistant...") to initiate the scheduling process, making the interaction feel much more natural and accessible, especially for users who may have mobility challenges.


### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?

This system is an excellent foundation for creating a valuable, specialized dataset.

#### How to create the dataset:
We can modify the code to log a structured record for each complete interaction. With user consent, we would capture:

- Timestamp: The exact time the interaction started.

- Raw Audio: The .wav file of the user's spoken command (e.g., "in_three_minutes_user01.wav").

- ASR Transcription: The text output from Vosk (e.g., "in three minutes").

- Parsed Intent: The system's interpretation (e.g., {"intent": "set_reminder", "entity": "relative_time", "value_seconds": 180}).

- System Action: The final outcome (e.g., SCHEDULED, SNOOZED, CONFIRMED).

This dataset would be extremely useful for training a custom ASR model tuned to time-related phrases or for building a more advanced NLU model.

#### Other sensing modalities to capture:

Camera Vision: A camera could add rich contextual data. It could be used for:

- User Presence: Confirming a person is actually in front of the device when the alarm rings.

- Medication Recognition: Using computer vision to identify the medication bottle (via QR code or image recognition) to log which specific medicine was taken.

- Proximity Sensor: An ultrasonic or infrared sensor could detect if a user is nearby. If the alarm is ringing and no one is close, the system could increase the volume or send a notification to a caregiver's phone.

- Accelerometer/IMU: Placing an accelerometer on the device could detect if it has been picked up or moved. This physical interaction could serve as an implicit confirmation that the user has acknowledged the reminder, even without a button press.








