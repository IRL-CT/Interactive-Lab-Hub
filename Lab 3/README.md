# Chatterboxes
**Collaborator: Miriam Alex - mta64 ([Repo](https://github.com/miriam-alex/Interactive-Lab-Hub/tree/Fall2025/Lab%203))**

<details>
<summary>Lab Description</summary>
  
[![Watch the video](https://user-images.githubusercontent.com/1128669/135009222-111fe522-e6ba-46ad-b6dc-d1633d21129c.png)](https://www.youtube.com/embed/Q8FWzLMobx0?start=19)

In this lab, we want you to design interaction with a speech-enabled device--something that listens and talks to you. This device can do anything *but* control lights (since we already did that in Lab 1).  First, we want you first to storyboard what you imagine the conversational interaction to be like. Then, you will use wizarding techniques to elicit examples of what people might say, ask, or respond.  We then want you to use the examples collected from at least two other people to inform the redesign of the device.

We will focus on **audio** as the main modality for interaction to start; these general techniques can be extended to **video**, **haptics** or other interactive mechanisms in the second part of the Lab.

</details>

## Prep for Part 1: Get the Latest Content and Pick up Additional Parts

<details>
<summary>Show Instructions</summary>
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

</details>

## Part 1.
<details><summary><h3>Setup</h3></summary>

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
</details>

<details>
<summary><h3>Text to Speech</h3></summary>
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
> found in speech-scripts/greet.sh

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
<summary><h3>Speech to Text</h3></summary>

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
> found in speech-scripts/speech_text.sh

</details>

<details>
<summary><h3>🤖 NEW: AI-Powered Conversations with Ollama</h3></summary>  


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

</details>

<details>
<summary><h3>Serving Pages</h3></summary>

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


<details open>
<summary><h3>Storyboard</h3></summary>

Brainstorming Potential Ideas: 
- talking mirror
- talking table
- talking stove
- talking building (directory)
- talking trash can
- talking backpack
- talking lamp
- talking key-holder

>Initially, we explored two potential ideas to see which one would have more potential/provide better interactions.

**Device 1: Table Assistant**

\*\***Verplank diagram**\*\*
![IMG_0702](https://github.com/user-attachments/assets/7ae09a90-10ba-42d4-a126-634197837dab)


Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses. 

**Process:**
- Picked out a scenario for using my device, in this case, I decided to have it assist a user in building an interactive device.
- I came up with potential questions that the user may ask and drew up responses for each situation
- Tried to keep the interactions short and repeatable, ending with either helping the user, or not being able to help
- Made sure to include a catch-all for any commands/questions that my device couldn't respond to
![IMG_0703](https://github.com/user-attachments/assets/2673f814-3544-4995-bdd0-31858b0e8b18)

**Device 2: Key Holder**

\*\***Verplank diagram**\*\*
<img width="2360" height="1640" alt="interaction_diagram" src="https://github.com/user-attachments/assets/482b1195-8f98-48a8-a91e-3b9bafbaa6ab" />

**Process:**

>Since the use case of this project is relatively narrow, this process felt straightforward to me. I first imagined the process I go through manually in the morning (namely, gathering my keys, checking the weather, and then assembling an outfit). I then automated this interaction, though I did feel that this initial draft was a little restrictive.

<img width="700" alt="interaction_diagram_flowchart" src="https://github.com/user-attachments/assets/3b2c138f-4ff9-4952-b4c0-e94513b20ee3" />


</details>

<details open>
<summary><h3>Acting out the dialogue</h3></summary>

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing.  Please record this interaction (for example, using Zoom's record feature).  

▶️ [Watch the table interaction](https://drive.google.com/file/d/1X4qozkjWHV7CG7UEsd9Pb28_1pUznamv/preview)  
▶️ [Watch the key holder interaction](https://drive.google.com/file/d/1WJVCHFZDOf9HbCw9gRurgA3TDscG2uMM/view)

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*  
Table Assistant:  
>The user took on a much more of a conversational tone rather than just giving the table commands. This made it harder to decide how to respond or which part of the statement to respond to. It wasn't very clear to the user what capabilities the device had/what it could help with. Therefore, many of the interactions I had mapped out weren't used. Addionally, the search feature might not be as useful as we initially thought.

Interactive Key Holder:  
> The dialogue was significantly different when acted out. I imagined the device as more of the questioning figure, but my partner largely led the conversation, rather than waiting for questions from the device. This significantly altered my flowchart; I realized that my final version of the device would have to be significantly more flexible than the version currently implemented.
</details>

<details>
<summary><h3>Wizarding with the Pi (optional)</h3></summary>
  
In the [demo directory](./demo), you will find an example Wizard of Oz project. In that project, you can see how audio and sensor data is streamed from the Pi to a wizard controller that runs in the browser.  You may use this demo code as a template. By running the `app.py` script, you can see how audio and sensor data (Adafruit MPU-6050 6-DoF Accel and Gyro Sensor) is streamed from the Pi to a wizard controller that runs in the browser `http://<YouPiIPAddress>:5000`. You can control what the system says from the controller as well!

\*\***Describe if the dialogue seemed different than what you imagined, or when acted out, when it was wizarded, and how.**\*\*
</details>

# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.

## Prep for Part 2  

We chose to focus on the key holder device since we felt like it provided a more guided experience.

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings...
  - Timing!!! Know when user is leaving, also respond/prompt quickly
  - Wording: make it more obvious what the device can help with, possibly by stating it?
  - Have a catch-all for misunderstandings
3. What are other modes of interaction _beyond speech_ that you might also use to clarify how to interact?
  - Shaking keys as a reminder (visual)
  - Distance sensor to know if someone's walking by/is currently grabbing keys (tactile)
  - Having keys hanging and less electronics exposed might make the device less intimidating and the purpose more clear.
4. Make a new storyboard, diagram and/or script based on these reflections.

<img width="700" alt="Untitled_Artwork-2" src="https://github.com/user-attachments/assets/cf4e1fca-4f8d-406f-9947-7761c50bed60" />
<img width="700" alt="Untitled_Artwork-3" src="https://github.com/user-attachments/assets/250adee9-603c-4fc9-aca0-eb1e610ff645" />
<img width="700" alt="Untitled_Artwork-4" src="https://github.com/user-attachments/assets/141b42f4-5e42-4294-9c69-df1478e2a6dc" />

## Prototype your system

***Document how the system works***  
**The system uses the following components:**  
- Webcam: used to detect whether a person is walking by the device
- Proximity Sensor: used to detect when the user reaches for the keys
- Actuator: used to shake the keys when triggered
- Raspberry Pi: used to run the code
- Speaker: used for audio output
- Cardboard Shell: Used to house the device, laser-cut in the MakerLab :)

**Interaction Flow:**   
- The device holds the users keys, which are clipped onto a carabinger on the front of the device.
- The device waits until the camera detects a person walking by or entering the frame. We used an existing model: mobilenet-ssd for person detection.
- When the user is detected, it triggers the key shaking mechanism and the device starts prompting the user "Don't forget your keys"
- The key shaking is achieved by using an actuator, which the carabinger is attached to, that sweeps from 0 to 90 degrees. 
- Once the user reaches for the keys, the proximity sensor is able to detect it and trigger the actuator and prompts to stop.
- Then, the device asks if there is anything else it can help with, and provides a list of possible tasks.
- Based on the user's asks, the device can respond accordingly through wizarding. There are a few pre-set responses, but it can also speak whatever is typed into it. 

***Include videos or screencaptures of both the system and the controller.***  
▶️ [Watch demo](https://drive.google.com/file/d/1qCZAVFRZPhjGw6e46kcf-VXWHTivVRyO/view?usp=sharing)  

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
▶️ [Watch the interactions](https://drive.google.com/file/d/1lpc3bVY-RKFJTVEG3BpNxegezBsAOpbU/view?usp=sharing)  

Answer the following:

### What worked well about the system and what didn't?
> The system worked well at getting people's attention and conveying the general purpose of getting people to take their keys. However, the interactions were fairly short since many of our users did not see a need for further interaction with the device after getting their keys. Labeling the device as a key holder may have limited the scope of interaction since it inherently does not provide much purpose besides holding keys. Additionally, we did have some confusion about how to take the keys off of the device, so we might need to clarify that interaction in the future. 

### What worked well about the controller and what didn't?
> It worked well that our controller was fairly automated for the beginning of the interaction, however, we did have some problems with the proximity sensor not triggering at the correct moments, which added some confusion on how to remove the keys from the device. Additionally, the wizarding part of the controller to respond to the user was not as seamless since it took extra time to type out a reply, which made it less believable that the device was responding on its own. Having some pre-set responses worked well though whenever the user did ask the correct questions. 

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?
> One lesson we can take away is that it truly is hard to predict how a user will interact with our device. Therefore, in order to design a truly autonomous version of the system, implementing AI-powered responses might be necessary to cover all the unpredictable interactions. Additionally, it is important to make the purpose or capabilities of the device clear, or else users might not use it to its full potential. We had to give our users some background in order for them to understand how to interact with the device, but ideally, the design of the device should be able to convey this. 

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?
> We could use our system to record how many people forget their keys on the daily, and also what the most important information is that people want to know before leaving their house. To do this, we would need to record the input from the users using a microphone and some speech-to-text software. It could make sense to capture more imaging of what users are wearing, potentially 
to provide advice based on the weather. 


















