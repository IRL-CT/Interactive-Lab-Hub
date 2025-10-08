# Chatterboxes
**Melody Huang(yh2353) & Xiang Chang (xc529) & Dingran Dai (dd699)**
[![Watch the video](https://user-images.githubusercontent.com/1128669/135009222-111fe522-e6ba-46ad-b6dc-d1633d21129c.png)](https://www.youtube.com/embed/Q8FWzLMobx0?start=19)

In this lab, we want you to design interaction with a speech-enabled device--something that listens and talks to you. This device can do anything *but* control lights (since we already did that in Lab 1).  First, we want you first to storyboard what you imagine the conversational interaction to be like. Then, you will use wizarding techniques to elicit examples of what people might say, ask, or respond.  We then want you to use the examples collected from at least two other people to inform the redesign of the device.

We will focus on **audio** as the main modality for interaction to start; these general techniques can be extended to **video**, **haptics** or other interactive mechanisms in the second part of the Lab.

## Prep for Part 1: Get the Latest Content and Pick up Additional Parts 

Please check instructions in [prep.md](prep.md) and complete the setup before class on Wednesday, Sept 23rd.

### Pick up Web Camera If You Don't Have One

Students who have not already received a web camera will receive their [Logitech C270 Webcam](https://www.amazon.com/Logitech-Desktop-Widescreen-Calling-Recording/dp/B004FHO5Y6/ref=sr_1_3?crid=W5QN79TK8JM7&dib=eyJ2IjoiMSJ9.FB-davgIQ_ciWNvY6RK4yckjgOCrvOWOGAG4IFaH0fczv-OIDHpR7rVTU8xj1iIbn_Aiowl9xMdeQxceQ6AT0Z8Rr5ZP1RocU6X8QSbkeJ4Zs5TYqa4a3C_cnfhZ7_ViooQU20IWibZqkBroF2Hja2xZXoTqZFI8e5YnF_2C0Bn7vtBGpapOYIGCeQoXqnV81r2HypQNUzFQbGPh7VqjqDbzmUoloFA2-QPLa5lOctA.L5ztl0wO7LqzxrIqDku9f96L9QrzYCMftU_YeTEJpGA&dib_tag=se&keywords=webcam%2Bc270&qid=1758416854&sprefix=webcam%2Bc270%2Caps%2C125&sr=8-3&th=1) and bluetooth speaker on Wednesday at the beginning of lab. If you cannot make it to class this week, please contact the TAs to ensure you get these. 

### Get the Latest Content

As always, pull updates from the class Interactive-Lab-Hub to both your Pi and your own GitHub repo. There are 2 ways you can do so:

**\[recommended\]**Option 1: On the Pi, `cd` to your `Interactive-Lab-Hub`, pull the updates from upstream (class lab-hub) and push the updates back to your own GitHub repo. You will need the *personal access token* for this.

```
pi@ixe00:~$ cd Interactive-Lab-Hub
pi@ixe00:~/Interactive-Lab-Hub $ git pull upstream Fall2025
pi@ixe00:~/Interactive-Lab-Hub $ git add .
pi@ixe00:~/Interactive-Lab-Hub $ git commit -m "get lab3 updates"
pi@ixe00:~/Interactive-Lab-Hub $ git push
```

Option 2: On your your own GitHub repo, [create pull request](https://github.com/FAR-Lab/Developing-and-Designing-Interactive-Devices/blob/2022Fall/readings/Submitting%20Labs.md) to get updates from the class Interactive-Lab-Hub. After you have latest updates online, go on your Pi, `cd` to your `Interactive-Lab-Hub` and use `git pull` to get updates from your own GitHub repo.

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

### Text to Speech 

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
  
### Speech to Text

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

[#### Speech-to-ZIP (Whisper)]( https://github.com/Daidai1031/Interactive-Lab-Hub/blob/Fall2025/Lab%203/speech-scripts/ask_zip_whisper.sh)
##### Stack

STT: openai-whisper (Python)

TTS: gTTS (online) → fallback espeak (offline)

Audio I/O: arecord (ALSA), optional aplay for playback

Shell driver: Bash (#!/usr/bin/env bash, set -euo pipefail for robust error handling)

##### Pipeline

Prompt (TTS): uses gTTS to synthesize English prompt (falls back to espeak if gTTS/mpg123 unavailable).

Record: arecord -d 6 -f S16_LE -r 16000 -c 1 zip_input.wav.

Transcribe: whisper.load_model("tiny.en").transcribe(..., language="en").

Extract: re.findall(r"\d", transcript) → join → take first 5 digits.

Confirm (TTS): speaks back the 5-digit ZIP: “Great, your ZIP code is 10044.”

##### Config knobs

Model: WHISPER_MODEL="tiny.en" → for higher accuracy use base.en (slower).

Duration: RECORD_SECONDS=6 → increase to 8–10s for very short responses.

Audio device: set ALSA_DEV="plughw:1,0" after checking arecord -l.

TTS: TTS_ENGINE="gtts" (natural; needs internet) or espeak (offline).

##### Files produced

zip_input.wav – recorded audio (overwritten each run)

zip_transcript.txt – full transcription text

zip_digits.txt – extracted 5-digit ZIP

### 🤖 NEW: AI-Powered Conversations with Ollama

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
**problem:** 
` Error: HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=30) `


**My solution 1: Longer timeout** 

`timeout=30`  -> `timeout=600`

**My solution 2: Shorter & faster reply** 
```bash
def query_ollama(prompt, model="phi3:mini", timeout=60):
    """Short & fast reply from Ollama"""
    try:
        t0 = time.perf_counter()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": f"Answer concisely in <= 20 words. {prompt}",
                "stream": False,
                "options": {
                    "num_predict": 60,     
                    "temperature": 0.2,    
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1  
                },
                "stop": ["\n\n"]
            },
            timeout=timeout
        )
        elapsed = time.perf_counter() - t0
        print(f"[query_ollama] elapsed: {elapsed:.2f}s (timeout={timeout}s)")
        if response.status_code == 200:
            return response.json().get('response', 'No response')
        else:
            return f"Error: HTTP {response.status_code} – {response.text[:200]}"
    except Exception as e:
        return f"Error: {e}"
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

**YAZ (pill) voice assistant**

1. Pipeline (voice → AI → voice)

arecord (16 kHz mono) → Whisper (tiny.en) for STT → Ollama (phi3:mini) for short answers → gTTS/espeak for TTS.

**Ollama integration (short, fast answers)**

Use REST /api/generate; constrain output length & randomness.
```bash
requests.post(f'{OLLAMA}/api/generate', json={
    'model':'phi3:mini',
    'prompt': 'Answer concisely (<= 50 words): '+user_q,
    'stream': False,
    'options': {'num_predict':60, 'temperature':0.2, 'repeat_penalty':1.1},
    'stop':['\n\n']
}, timeout=REQUEST_TIMEOUT)
```
**Minimal UX flows**

1. Set time → ask → record → STT → parse → save → TTS confirm.

2. Query time → read file → TTS.

3. YAZ Q&A → ask → record → STT → Ollama (short) → TTS.

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


### Storyboard

Storyboard and/or use a Verplank diagram to design a speech-enabled device. (Stuck? Make a device that talks for dogs. If that is too stupid, find an application that is better than that.) 

**Concept at a glance**

**Who:** busy student/professional who often forgets a daily pill.

**What:** voice device with one big confirm button + LED ring + small display (optional). Local wake word (“Hey Remi”).

**Why:** reduce missed doses; make adherence quick and friendly without opening an app.


\*\***Post your storyboard and diagram here.**\*\*

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/faad9d69-d240-4156-9ba2-e7ee63cd3d4a" />


Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses. 


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

https://github.com/user-attachments/assets/f6bf10c9-58b7-4280-8227-05b0e1fe490d


\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*

**Chime before speech.** When we acted/wizarded it, a disembodied voice felt jarring, so we added a brief “ding” to cue attention.

**Improve:** Precede TTS with a sub-second earcon (or ≤2s musical lead-in) and keep barge-in enabled so users can reply immediately, with volume auto-reduced during quiet hours.

**Knowing when the user is done (endpointing). **The device hesitated to avoid cutting users off, creating awkward pauses.

**Improve:** Combine a short silence threshold with intent confidence for a “soft end,” then wait ~200 ms for any continued speech before responding (cancel if speech resumes).

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
<img width="1018" height="1857" alt="storyboard_;ab3_2" src="https://github.com/user-attachments/assets/b5d8c9d9-1e58-4663-9bf0-2a0070b737b7" />


https://github.com/user-attachments/assets/4b7e86a1-e5ef-414a-aebf-6dc980800fac


*Include videos or screencaptures of both the system and the controller.*
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
\*\**your answer here*\*\*

### What worked well about the controller and what didn't?

\*\**your answer here*\*\*

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

\*\**your answer here*\*\*


### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?

\*\**your answer here*\*\*





















