# Chatterboxes

**NAMES OF COLLABORATORS HERE**
Alex Yen ( https://github.com/Alexyen04/Alex-Yen-Interactive-Lab-Hub/blob/Fall2026/Lab%203/README.md )

<details>
[![Watch the video](https://user-images.githubusercontent.com/1128669/135009222-111fe522-e6ba-46ad-b6dc-d1633d21129c.png)](https://youtu.be/LZ0VJClIlRI?si=Yy84mcyVYuVV19mn)

In this lab, we want you to design interaction with a speech-enabled device — something that listens and talks to you. This device can do anything *but* control lights (since we already did that in Lab 1). First, we want you to storyboard what you imagine the conversational interaction to be like. Then you will use wizarding techniques to elicit examples of what people might say, ask, or respond. We then want you to use the examples collected from at least two other people to inform the redesign of the device.

We will focus on **audio** as the main modality for interaction to start; these general techniques can be extended to **video**, **haptics** or other interactive mechanisms in the second part of the Lab.

A note on what you are building with. Speech interfaces are usually taught as two boxes — speech-in, speech-out — and that framing hides the part that actually determines whether an interaction works. Between listening and speaking sits the question of **whose turn it is**: when does the device decide you have finished talking, and how long does it make you wait before it answers? This lab gives you direct control over both, and we will ask you to notice what changes when you move them.

## Prep for Part 1: Get the Latest Content and Pick up Additional Parts


Please check instructions in [prep.md](prep.md) and complete the setup.

### Pick up Web Camera If You Don't Have One

Students who have not already received a web camera will receive their Webcam and at the beginning of lab. If you cannot make it to class this week, please contact the TAs to ensure you get these.

### Get the Latest Content

As always, pull updates from the class Interactive-Lab-Hub to both your Pi and your own GitHub repo.

**\[recommended\]** Option 1: On the Pi, `cd` to your `Interactive-Lab-Hub`, pull the updates from upstream (class lab-hub) and push the updates back to your own GitHub repo. You will need the *personal access token* for this.

```
pi@ixe00:~$ cd Interactive-Lab-Hub
pi@ixe00:~/Interactive-Lab-Hub $ git pull upstream Fall2026
pi@ixe00:~/Interactive-Lab-Hub $ git add .
pi@ixe00:~/Interactive-Lab-Hub $ git commit -m "get lab3 updates"
pi@ixe00:~/Interactive-Lab-Hub $ git push
```

Option 2: On your own GitHub repo, create a pull request to get updates from the class Interactive-Lab-Hub. After you have the latest updates online, go to your Pi, `cd` to your `Interactive-Lab-Hub` and use `git pull`.

---
</details>

# Part 1

## Setup
<details>
Create and activate a virtual environment for this lab:

```
pi@ixe00:~$ cd Interactive-Lab-Hub/Lab\ 3
pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ python3 -m venv .venv
pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ source .venv/bin/activate
(.venv) pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $
```

Install the Python dependencies:

```
(.venv) $ pip install -r requirements.txt
```

This takes a few minutes. If you would like it to take considerably less time, [`uv`](https://docs.astral.sh/uv/) is a drop-in replacement for `pip` that is dramatically faster on the Pi:

```
(.venv) $ pip install uv && uv pip install -r requirements.txt
```

Then run the setup script, which installs the classic speech synthesizers, downloads the voice activity detection model, and pre-fetches a neural voice and a speech recognition model so you are not waiting on downloads during lab:

```
(.venv):~$ cd speech-scripts
(.venv) $ ./setup.sh
```

Check your audio devices before going further. `arecord -l` lists capture devices and `aplay -l` lists playback devices; if your webcam microphone or Bluetooth speaker does not appear, fix that first — every script below assumes the system defaults are the ones you want.
</details>

## A. Text to Speech

<details>
Your Pi can speak in several quite different ways, and the differences are audible in a way that matters for design. In `speech-scripts/` there are shell scripts for each.

### The classic engines

```
(.venv) $ cd speech-scripts

(.venv) $ sudo apt update
(.venv) $ sudo apt install -y espeak festival festvox-kallpc16k

(.venv) $ ./espeak_demo.sh
(.venv) $ ./festival_demo.sh
```

You can run these `.sh` files by typing `./filename`, and read one with `cat filename`. You can also play audio files directly with `aplay filename` — try `aplay lookdave.wav`.

These are all decades-old technology and they sound like it. `espeak-ng` is a *formant synthesizer*: it generates speech from an acoustic model of the vocal tract, which is why it sounds robotic but also why the whole thing fits in a couple of megabytes and responds instantly. `festival` is *concatenative*: they stitch together recorded fragments of a real speaker, which sounds more human but breaks audibly at the seams.

### Neural TTS with Piper

Note that the Piper command line changed in version 1.x — voices are now downloaded explicitly with `python3 -m piper.download_voices`, and you invoke it as `python3 -m piper`. Tutorials you find online may show the old `echo ... | piper --model ...` form, which no longer works. Browse the [voice samples](https://rhasspy.github.io/piper-samples) and download a different one if you'd like:

```
(.venv) $ python3 -m piper.download_voices en_US-lessac-medium
```

[Piper](https://github.com/OHF-Voice/piper1-gpl) synthesizes speech with a small neural network, runs comfortably on the Pi 5, and sounds markedly better than the above.

```
(.venv) $ ./piper_demo.sh
```

The demo script also shows `--output-raw`, which streams audio to the speaker as it is generated rather than writing a file first. Listen for the difference in how quickly speech begins. In a conversational system this gap is the thing your user experiences as responsiveness.
</details>

\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
(This shell file should be saved to your own repo for this lab.)
<details>
look for file in this path Interactive-Lab-Hub/Lab 3/speech-scripts/greet_viktor.sh
</details>

\*\***Then answer: Is the same greeting, in these different voices, the same greeting? Describe one concrete way the voice changed what the utterance seemed to mean or who seemed to be speaking.**\*\*
<details>
No, not really. The words are the same, but each voice made a different "someone" say them.

* espeak sounded like a machine reading a label. My name came out pronounced sorta funky rather than something realistic as to what someone would say (Vik - ter, Ray-dev).

* festival sounded more human but choppy. It seemed like a recorded announcement, not someone talking to me.

* Piper (lessac, English) sounded like a polite assistant or receptionist. It was friendly but impersonal, and it said "Radev" the way an American reads an unfamiliar name.

* Piper (dimitar, Bulgarian) changed the meaning most. „Здравей, Виктор Радев" said my name the way my family says it, with the stress on РА-дев (Raw - dev). It stopped sounding like a device and more like a human who knows me.

One concrete change: the Bulgarian voice was fine-tuned from the English lessac voice, and you can hear it: there's a slight English accent under the Bulgarian. So even with correct words and pronunciation, it sounded like a foreigner who learned Bulgarian greeting me, not a native speaker. The language made it feel personal, but the voice changed who seemed to be speaking.

A second, accidental example: when an encoding bug garbled the Cyrillic text, the same natural-sounding voice read symbols like "±" aloud as "plus minus". It still sounded confident and human while saying nonsense. A good voice makes you trust the words, whether or not they're right.
</details>
## B. Speech to Text
<details>
We use [faster-whisper](https://github.com/SYSTRAN/faster-whisper), a reimplementation of OpenAI's Whisper model that runs several times faster on CPU and does not require PyTorch. All processing happens on the Pi; nothing is sent to a server.

```
(.venv) $ python transcribe.py lookdave.wav
```

The transcript is not the interesting output here — the timings are. Run it again with a larger model and compare:

```
(.venv) $ python transcribe.py lookdave.wav --model base.en
(.venv) $ python transcribe.py lookdave.wav --model small.en
#  noted that the first run may take longer because the model is downloaded, and that the HF unauthenticated-request warning is expected and not an error.
```

Available sizes, smallest first: `tiny.en`, `base.en`, `small.en`, `medium.en`. The `.en` variants are English-only and faster than their multilingual counterparts at the same size.
</details>
\*\***Record a few seconds of your own speech (`arecord -d 5 -f cd -c 1 -r 16000 test.wav`) and transcribe it with at least two model sizes. Report the real-time factor for each. At what point does the accuracy improvement stop being worth the delay, for a system that has to answer you?**\*\*
<details>
I recorded myself saying my raspberry pi's IP address ("[what you said 10.56.129.76]") and transcribed the same 5-second clip with four model sizes:

| Model | Transcription time | Real-time factor | Transcript |
| :--- | :--- | :--- | :--- |
| tiny.en | 1.07 s | 0.21x | IP address is 1056 or 12976 |
| base.en | 2.02 s | 0.40x | IP address is 1056, 12976. |
| small.en | 5.64 s | 1.13x | IP address is 1056 12976 |
| medium.en | 15.79 s | 3.16x | IP address is 1056.129.76 |

(medium.en's 187 s model load included downloading 1.5 GB. That's a one-time cost, not part of the response delay.)

Every model heard the same digits. What they got wrong was the structure. tiny.en even invented an "or" that I never said. base.en and small.en turned the dots into a comma or a space. Only medium.en recognized the dots, and it still grouped the numbers wrong. So the bigger models didn't hear better. They just guessed the formatting better.

The improvement stops being worth it after base.en. small.en has a real-time factor above 1, meaning it takes longer to transcribe than I took to speak. On top of the silence the system already waits to decide I'm done, that's almost 6 seconds of dead air, which feels like the device froze. medium.en took 16 seconds for a 5-second sentence, which is unusable in conversation. base.en answered in about 2 seconds with the same digits as the others. For a system that has to reply, base.en (or tiny.en for speed) is the sweet spot.

Design takeaway: a bigger model isn't the fix for numbers. It's better to use a fast model, clean up the digits in code, and read the number back for confirmation ("I heard 10, 56, 129, 76, is that right?").
</details>
\*\***Write your own script that verbally asks for a numerical input (a phone number, zipcode, number of pets) and records the answer the respondent provides.**\*\* Numbers are a good stress test — transcription systems make characteristic errors on digit strings, and you will want to know what they are before you design around them. 
<details>
For the script that verbally asks participant for a numerical input, go to: Interactive-Lab-Hub/Lab 3/speech-scripts/ask_number.py

Here is what it transcribed: Interactive-Lab-Hub/Lab 3/speech-scripts/number_log.csv

time,question,model,transcript,digits,length_ok,transcribe_seconds,rtf
2026-09-27T16:35:19,zip,base.en,My zip code is 10044.,10044,True,2.31,0.39
2026-09-27T16:37:50,phone,base.en,6 1 2 7 6 3 6 5 7,612763657,False,2.69,0.45
2026-09-27T16:38:33,pets,base.en,I have zero pets.,0,True,1.88,0.31

| Time | Question | Model | Transcript | Digits | Length OK | Transcribe Seconds | RTF |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-09-27T16:35:19 | zip | base.en | My zip code is 10044. | 10044 | True | 2.31 | 0.39 |
| 2026-09-27T16:37:50 | phone | base.en | 6 1 2 7 6 3 6 5 7 | 612763657 | False | 2.69 | 0.45 |
| 2026-09-27T16:38:33 | pets | base.en | I have zero pets. | 0 | True | 1.88 | 0.31 |

ask_number.py uses Piper to ask a question out loud, records the answer, transcribes it with faster-whisper (base.en), and pulls out the digits. It reads the number back and logs every answer to number_log.csv. The zip code ("10044") and pets ("zero") came out right in about 2 seconds (real-time factor around 0.3–0.4). The phone number only came back with 9 of 10 digits, because the fixed 6-second recording cut me off before I finished. The length check caught it ("That doesn't look like a full phone number"). Together with the IP address test, where Whisper heard the right digits but grouped them wrong, this showed me that number errors come from timing and formatting more than from mishearing. So a number-taking system should wait until the person has actually stopped talking, check the number's length, and read it back for confirmation.
</details>
## C. Turn-taking: knowing when someone has stopped talking
<details>
Everything so far has worked on fixed audio files. A real conversational device does not get told when to start and stop recording — it has to decide. This is the problem that makes speech interfaces hard, and it is mostly not a speech recognition problem.
</details>
<details>
We use a **voice activity detector** (VAD) to segment the microphone stream into utterances. `listen.py` runs Silero VAD continuously and hands each detected utterance to faster-whisper:

```
(.venv) $ cd speech-scripts
(.venv) $ python listen.py
```

Speak, pause, and watch it transcribe. Now change the endpointing threshold — the amount of silence the system requires before it decides your turn is over:

```
(.venv) $ python listen.py --min-silence 0.2
(.venv) $ python listen.py --min-silence 1.5
```
</details>
\*\***Try both extremes, and something in between. Describe what each one feels like to talk to. Note specifically: at 0.2s, what kinds of normal speech get cut off? At 1.5s, what does the delay make the system seem like?**\*\*
<details>
At 0.2 s the system felt jumpy, like someone who keeps interrupting. Any normal pause ended my turn: "My phone number is… 612" came out as two separate lines (and lost "My"), and a breath split "a long sentence… in the middle" in two. So thinking pauses, "uh"s and breaths get cut off, which is exactly where people pause when giving numbers. Short answers like "Yeah" worked fine, though. At 1.5 s nothing got split, and even "My phone number is 612" with a pause came through whole. But after I stopped talking I waited about 1.5 s of silence plus about 0.9 s of transcription, around 2.4 s total. That made the system seem slow or distracted, like it wasn't sure I was done. It also merged separate utterances: my instructions and my "yes" became one line. The default 0.4 s felt like the best middle ground for short back-and-forth. For a number-taking device I'd use around 0.8–1.0 s, so people can pause between digit groups without being cut off.

There is no correct value. A system that takes drink orders and a system that listens to someone think out loud want very different thresholds, and the right one depends on what your users are doing with their pauses.
</details>
### The complete loop
<details>
`echo_bot.py` puts the pieces together: it listens, endpoints, transcribes, and speaks a reply through Piper. The dialogue policy is deliberately trivial — it repeats what you said — so that everything you notice is a property of the timing rather than the content.

```
(.venv) $ python echo_bot.py
```
</details>
## D. Storyboard
<details>
Storyboard and/or use a Verplank diagram to design a speech-enabled device. (Stuck? Make a device that talks for dogs. If that is too stupid, find an application that is better than that.)
</details>
\*\***Post your storyboard and diagram here.**\*\*
<details>
<img width="1286" height="655" alt="storyboardimagelab3" src="https://github.com/user-attachments/assets/54cf6c41-267a-44e0-aca2-290770dc8430" />

Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses.
</details>
\*\***Please describe and document your process.**\*\*
<details>
##Voice Activated Recording Device
Our idea is to create an interactive, voice activated recording device that allows users to control a recording through a set of predefined voice commands.

Starting the Device
The recording device begins in an off state. The device will say "Welcome to the Voice Activated Recording Device!" Say:

"Help settings"

to get started.

The device will then verbally explain the available commands and the rules for using them.

Available Voice Commands
The device supports four main commands:

"Start recording"
Begins a new recording.

"Pause recording"
Pauses the current recording.

"Play recording"
Resumes a paused recording.

"End recording"
Stops and completes the current recording.

Command Rules
The device follows a specific set of rules to ensure that commands are used in the correct order: Note there will be a 2 second pause in between each interaction between user and device.

After entering the help settings, the first command must be "Start recording."
"Pause recording" can only be used while the device is actively recording.
"Play recording" can only be used when the recording is currently paused.
"End recording" can only be used while the recording is active.
Recording Process
After listening to the available commands and rules, the user says "Start recording" to begin.

While the recording is active, the user can say "Pause recording" to temporarily pause it. To resume, the user says "Play recording." This process can be repeated as needed throughout the recording session.

When the user is finished, they say "End recording." The device will stop the recording and upload the completed video to the connected computer, where the user can access and watch it. The device will say "uploading video" to indicate to the user that the video is processing.

Your script should include the pauses. Where does your device wait, and for how long? You now know from Part C that this is a parameter you have to choose, not something that happens for free.
</details>
## E. Acting out the dialogue
<details>
Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing. Please record this interaction (for example, using Zoom's record feature).

https://github.com/user-attachments/assets/8f1f7c83-d23e-4133-86db-e3a0befcbf1e
</details>
\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*
<details>
Overall the script we followed was almost perfect. There were some inconsistences regarding when the icons would show up, however it was overall pretty smooth. When we design this to work on our raspberry pi we will need to make sure that the icons show in the PiTFT screen to show what state the program is in. We had to redo our video a few times because timing the icons with the voice, and the actions was difficult.
</details>
---

# Lab 3 Part 2
For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.
<details>

1. Rohil Saraf, https://github.com/rohilsaraf97/Interactive-Lab-Hub/tree/Fall2026/Lab%203 - Great idea! In fact, it would have been really useful for recording these demos. Does this mean the device is always listening? Is there an indication of when it is? Also, in the final video, is the device's audio instruction recorded too? This is amazing though! I could see it being used for hands-free recording of tutorials, cooking videos, or lectures.

2. Jovian Wang, https://github.com/jovianw/Interactive-Lab-Hub/tree/Fall2026/Lab%203 - Very cool and functional application of speech recognition and audio! Small feedback: it should be more clear what the commands are. Is it "pause recording", or is it "Camera, pause", where the device recognizes that keyword "camera"? This wasn't clear in the acted out dialogue and definitely something to think more about. Overall, great idea!

3. Gaurav Patel, https://github.com/Nishant-Ray/Interactive-Lab-Hub/blob/Fall2026/Lab%203/README.md - I like the idea! I like how you can basically record and do everything you need without requiring a camera man. I think the idea might need some help for the start recording because you don't want it to start immediately. However is that what the 1,2,3 is for? I think every action you ask for should be responded with to confirm that whatever action is happening is actually happening. I also really like the immediate upload idea, but maybe you should have like an ask of whether or not they should upload instead of immediately uploading.
   
</details>
## Prep for Part 2
<details>

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings.
2. What are other modes of interaction *beyond speech* that you might also use to clarify how to interact? In particular: how does someone know when the device is listening, and when it is thinking? You have a screen and an LED.
3. Make a new storyboard, diagram and/or script based on these reflections.
4. (optional) Integrate [input devices](inputs.md) in the system
</details>

## Prototype your system
<details>
The system should:
* use the Raspberry Pi
* use one or more sensors
* require participants to speak to it
</details>
*Document how the system works.*
*Include videos or screencaptures of both the system and the controller.*
<details>
<a href="https://youtu.be/lPQywgG8UPU" target="_blank">
  <img src="https://youtu.be/lPQywgG8UPU" alt="Watch the video" width="600" height="338" border="10" />
</a>
</details>
## Test the system

Try to get at least two people to interact with your system. (Ideally, you would inform them that there is a wizard *after* the interaction, but we recognize that can be hard.)

Answer the following:

<details>

2 peoples feedback: 

David Zhang: The system is cool and video recording works well. In the beginning its difficult to know which commands to say and unclear where to start. Sometimes the voice recognition system wasn't that good and didn't parse the speech probably. The screen was displaying lots of text but it was difficult to see because it was very small and hard to keep track of the commands. 

Allen Lu: The system worked well overall and the recording features were easy to use once I understood the commands. At first, I was unsure what I was supposed to say because there were several different voice commands to remember. The voice recognition also occasionally misunderstood what I said, so I had to repeat certain commands. The screen helped show the current state of the system, but the text was small and there was too much information displayed at once. Using larger text and showing only the commands that are currently available would make the system easier to follow.

### What worked well about the system and what didn't?
The whole idea for the system, including the play/pause/record aspect worked as intended. When the user said certain commands, the machine would appropriately follow them and execute the proper interaction. One thing that could be improved is to use a different model for parsing the speech from the user. Sometimes the model would not interpret the speech very well and would get the wrong text. As a result, the user would often times have to mention the same command multiple times, causing a big inconvenience. 

### What worked well about the controller and what didn't?
For the controller, it was especially convenient for users who didn't want to use the voice to text functionality. It allowed users to directly input their commands into the terminal and operate the system through that method. However, one downside of this would be that if there were any typos in the command the user would often need to retype the commands again. Overall the controller provided very good information for the user that wasn't displayed in the system. Especially for the help settings commands or even seeing what the system parsed when using voice recognition, it gave the user a visual way to see these aspects. 

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?
The biggest lesson I take away from this WoZ interaction is that I should keep the amount of commands a lot of more concise and limited. The more complex the command the harder it is for the user to know what to say and to remember all the commands. For this interaction specifically there were many commands which made it difficult for users to know what to say once they reached the end of the recording process. There are many ways to say the same meaning in english which also makes its difficult for users to say a command if they forgot. For example, to pause a video you could say "pause recording", "pause", or "pause video". Overall, designing a more autonomous version of this system just requires less commands to give the user a more guided experience where they do not need to remember each step. 


### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?
During user interactions, we could record and save certain commands that users say to capture the more typical phrases. After then we can reduce the amount of commands and just focus on commands that are high use. In addition, we could also save how long the user takes a pause in between each voice interaction to better modify how much pause time there should be within each interaction. Some other sensing modalities that would make sense to capture would be physical touch interactions with the buttons. Often times users would like to be able to control the system through buttons.
</details>

<details>
  <summary><strong>Submission Cleanup Reminder (Click to Expand)</strong></summary>

  **Before submitting your README.md:**
  - This readme.md file has a lot of extra text for guidance.
  - Remove all instructional text and example prompts from this file.
  - You may either delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
  - Your final submission should be neat, focused on your own work, and easy to read for grading.
</details>
