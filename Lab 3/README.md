# Chatterboxes

**NAMES OF COLLABORATORS HERE**

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

# Part 1

## Setup

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

## A. Text to Speech

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

\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
(This shell file should be saved to your own repo for this lab.)

\*\***Then answer: Is the same greeting, in these different voices, the same greeting? Describe one concrete way the voice changed what the utterance seemed to mean or who seemed to be speaking.**\*\*

Although the three TTS engines deliver the same message, they create different feelings. I personally prefer Piper because its voice sounds more natural and pleasant. eSpeak sounds more robotic, which makes the greeting feel like a command from a machine. In contrast, Piper makes the same greeting feel more friendly and personal, almost like someone is actually talking to me. This shows how the choice of voice can affect the user's perception of a speech-enabled device.

## B. Speech to Text

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

\*\***Record a few seconds of your own speech (`arecord -d 5 -f cd -c 1 -r 16000 test.wav`) and transcribe it with at least two model sizes. Report the real-time factor for each. At what point does the accuracy improvement stop being worth the delay, for a system that has to answer you?**\*\*

<img width="371" height="502" alt="ss2026-09-23 下午10 57 14" src="https://github.com/user-attachments/assets/0f92d006-564a-4e8b-bf2c-a674800ba0f9" />

| Model    | Transcription Time | Real-Time Factor | Result                      |
| -------- | -----------------: | ---------------: | --------------------------- |
| tiny.en  |              1.10s |            0.22x | Correctly recognized Jindi  |
| base.en  |              2.16s |            0.43x | Recognized Jindi as Jin Dea |
| small.en |              6.16s |            1.23x | Correctly recognized Jindi  |



I recorded a five-second audio clip of myself speaking and tested it with three different Whisper models. Both tiny.en and small.en correctly recognized my name, while base.en transcribed it as "Jin Dea."

The tiny.en model was the fastest, with an RTF of 0.22x, while small.en took 6.16 seconds and had an RTF of 1.23x. In this experiment, the larger model did not provide a noticeable improvement in accuracy compared to tiny.en, but it required much more processing time.

For an interactive speech-enabled device, I think a smaller model would be more suitable for simple conversations because faster responses can make the interaction feel more natural. However, a larger model might still be useful when the system needs to understand more complicated speech.

\*\***Write your own script that verbally asks for a numerical input (a phone number, zipcode, number of pets) and records the answer the respondent provides.**\*\* Numbers are a good stress test — transcription systems make characteristic errors on digit strings, and you will want to know what they are before you design around them.

<img width="481" height="175" alt="ss2026-09-23 下午11 06 26" src="https://github.com/user-attachments/assets/880bced2-1de3-46a1-bea3-f86a13af3a24" />

I created a script using Piper to ask the user how many times they walk their dog every day. The device then records the user's spoken response. When I answered "three times," the tiny.en model successfully transcribed my response as "three times," with an RTF of 0.11x.

## C. Turn-taking: knowing when someone has stopped talking

Everything so far has worked on fixed audio files. A real conversational device does not get told when to start and stop recording — it has to decide. This is the problem that makes speech interfaces hard, and it is mostly not a speech recognition problem.

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

\*\***Try both extremes, and something in between. Describe what each one feels like to talk to. Note specifically: at 0.2s, what kinds of normal speech get cut off? At 1.5s, what does the delay make the system seem like?**\*\*


I tested three different silence thresholds: 0.2s, 0.8s, and 1.5s. I used the same sentence, "Can you remind me to walk my dog at seven tonight?", with a short pause before saying the time.

<img width="657" height="251" alt="截屏2026-09-23 下午11 20 08" src="https://github.com/user-attachments/assets/c75c8778-6bfa-4abe-ac1d-09f80d08165a" />

<img width="544" height="127" alt="截屏2026-09-23 下午11 19 01" src="https://github.com/user-attachments/assets/a2b2975e-220e-49fa-8e06-d88b658a270a" />

| Silence Threshold | Observation                                                                                                    |
| ----------------- | -------------------------------------------------------------------------------------------------------------- |
| 0.2s              | The system split my sentence into two separate utterances because of the pause.                                |
| 0.8s              | The system captured my entire sentence without splitting it, although some words were transcribed incorrectly. |
| 1.5s              | The system also captured my sentence as one utterance, but required a longer silence before processing it.     |


Reflection:

The 0.2s threshold was too sensitive to my natural pauses. When I stopped briefly to think about the time, the system treated it as the end of my sentence. This could be problematic for a conversational device because it might respond before the user finishes their request.

The 0.8s threshold worked better for my speaking pattern because it allowed me to pause without splitting my sentence. The 1.5s threshold also captured my complete request, but it required a longer waiting period after I finished talking.

I learned that choosing a silence threshold involves balancing responsiveness and allowing users enough time to express themselves. A shorter threshold can make the device respond faster but may interrupt users, while a longer threshold can accommodate natural pauses but make the interaction feel slower.

There is no correct value. A system that takes drink orders and a system that listens to someone think out loud want very different thresholds, and the right one depends on what your users are doing with their pauses.

### The complete loop

`echo_bot.py` puts the pieces together: it listens, endpoints, transcribes, and speaks a reply through Piper. The dialogue policy is deliberately trivial — it repeats what you said — so that everything you notice is a property of the timing rather than the content.

```
(.venv) $ python echo_bot.py
```

**Echo Bot Test**

<img width="667" height="121" alt="截屏2026-09-23 下午11 23 22" src="https://github.com/user-attachments/assets/e087f99c-cb83-4204-a581-46300521dcb5" />

I also tested the complete interaction loop using echo_bot.py. The system successfully listened to my speech, transcribed it, and responded using Piper. The ASR process took 0.95 seconds, and Piper needed another 0.46 seconds to generate the first audio, resulting in a total reported gap of 1.41 seconds.

However, when I said "Hi, my name is Jindi," the system recognized my name as "Cindy" and repeated the incorrect name back to me. This made me realize that speech recognition errors can directly affect the conversation, even when the system's response logic works correctly.


## D. Storyboard

Storyboard and/or use a Verplank diagram to design a speech-enabled device. (Stuck? Make a device that talks for dogs. If that is too stupid, find an application that is better than that.)

\*\***Post your storyboard and diagram here.**\*\*

<img width="3106" height="1619" alt="sbo 52" src="https://github.com/user-attachments/assets/4ae3a573-1c4a-4c46-b29d-c2ed440e64d8" />


Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses.

\*\***Please describe and document your process.**\*\*

Your script should include the pauses. Where does your device wait, and for how long? You now know from Part C that this is a parameter you have to choose, not something that happens for free.

### Process and Dialogue Timing

Our design is a voice-controlled cooking assistant that helps users follow a recipe while their hands are dirty or occupied. Our storyboard follows a cooking session from preparing ingredients to finishing the meal. It includes requests to repeat instructions, a missing ingredient, and correction of a misheard timer duration. We also recorded a video demonstration of the interaction.

The assistant gives one instruction at a time. After asking the user to chop an onion, it waits 20 seconds before asking, “Ready for the next step?” If the user replies, “Wait, I’m still cutting,” it says, “No problem. Let me know when you’re ready.” It then waits for the user to say “Next,” without a fixed deadline. This allows the user’s cooking pace to determine when the recipe advances.

Our dialogue also supports recovery. In a noisy kitchen, “Repeat that” makes the assistant repeat its previous instruction. When the user says, “I don’t have olive oil,” the assistant suggests vegetable oil and asks whether the user wants to continue. In the timer scene, the assistant mishears “five minutes” as “nine minutes.” The user corrects it, and the assistant acknowledges the correction.

### Pauses in Our Script

- **After a spoken command:** Our proposed endpointing threshold is 1.0 second of silence before processing the response. This applies to commands such as “Next,” “Repeat that,” and “No, five minutes.”
- **During food preparation:** The assistant waits 20 seconds before its initial progress check.
- **After “Wait, I’m still cutting”:** It waits until the user says “Next.” Silence does not mean that the cooking step is complete.
- **After a confirmation question:** We would allow 5 seconds for the user to begin answering. If there is no response, the assistant would repeat the question once and then wait quietly. Once speech begins, the endpointing threshold determines when the answer ends.
- **During the timer:** Once the duration is corrected to five minutes, the timer should count five minutes and then announce completion. The assistant should not assume that the entire meal is finished simply because the timer has ended.

### How Part C Informed Our Design

In our tests, a 0.2-second silence threshold split speech into short fragments. At 0.7 seconds, speech was still divided into several segments. The 1.5-second setting allowed a short phrase to remain together but introduced a longer wait before processing. These trials used different utterances, so they do not establish a single best threshold. We would start testing our cooking assistant at 1.0 second and adjust it using the same sentences under realistic kitchen conditions.

Intentional pauses are separate from processing delays. Our echo-bot test reported 5.24 seconds for speech recognition, 0.22 seconds to the first synthesized audio, and a total gap of 5.45 seconds. Choosing a silence threshold therefore does not guarantee an equally fast reply.

A further improvement would be to confirm the timer duration before starting it: “I heard five minutes. Is that correct?” This would give the user an opportunity to correct a number before the device acts.

## E. Acting out the dialogue

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing. Please record this interaction (for example, using Zoom's record feature).

Demo Video: https://youtu.be/s8K_N4ap6eY

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*

Acting out the dialogue made us realize that the cooking assistant needed to follow the user’s pace rather than the timing we imagined in our storyboard. We had planned a progress check after 20 seconds, but that did not necessarily mean the user would be ready. The exchange “Wait, I’m still cutting” showed why the assistant should wait for an explicit “Next” instead of automatically continuing.

The interaction also felt less linear than the written script. Requests such as “Repeat that” and “I don’t have olive oil” interrupted the recipe instructions. These exchanges highlighted the need to remember the current step and return to it after answering the user.

The timer correction revealed another weakness. When the assistant interpreted “five minutes” as “nine minutes,” the user had to correct it. We would revise this interaction so that the assistant confirms the duration before starting the timer.

Overall, acting out the dialogue shifted our attention from what the assistant says to when it speaks, when it stays quiet, and how it handles corrections. Our next version would give the user more control over the pace and make confirmation of numerical inputs explicit.


---

# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.

## Prep for Part 2

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings.
2. What are other modes of interaction *beyond speech* that you might also use to clarify how to interact? In particular: how does someone know when the device is listening, and when it is thinking? You have a screen and an LED.
3. Make a new storyboard, diagram and/or script based on these reflections.
4. (optional) Integrate [input devices](inputs.md) in the system

## Prototype your system

The system should:
* use the Raspberry Pi
* use one or more sensors
* require participants to speak to it

*Document how the system works.*

*Include videos or screencaptures of both the system and the controller.*

## Prototype: Voice-Controlled Cooking Assistant

Our prototype is a voice-controlled cooking assistant that runs locally on a
Raspberry Pi. The system uses a USB microphone as its sensor, a speaker for
audio responses, and a 1.14-inch ST7789 screen for visual feedback.

The participant speaks directly to the microphone. Silero VAD detects when the
participant has finished speaking, and Faster-Whisper converts the recorded
speech into text locally on the Raspberry Pi. The Python program analyzes the
transcript and automatically selects an appropriate response. Piper then
converts the response into speech and plays it through the speaker.

The assistant understands recipe commands such as “start,” “next,” “repeat,”
and “wait.” It can suggest substitutions for missing ingredients and can
create, check, or cancel a timer.

### Screen Feedback

The screen uses a pastel color system to communicate the current interaction
state:

- **Pastel blue — Listening:** the participant can speak.
- **Pastel yellow — Processing:** the system is transcribing and interpreting speech.
- **Pastel green — Speaking:** the assistant is producing a spoken response.
- **Pastel red — Error:** the system encountered a problem.
- **Pastel purple — Timer:** a timer is active.

A chef-hat icon provides a consistent visual identity for the cooking
assistant. When a timer is active, the screen displays the remaining time in
`MM:SS` format and shows a progress bar.

### Interaction Flow

1. The screen displays the blue “Listening” state.
2. The participant speaks into the USB microphone.
3. Silero VAD detects the end of the speaking turn.
4. The screen changes to the yellow “Processing” state.
5. Faster-Whisper converts the speech into text.
6. The Python program analyzes the transcript and selects a response.
7. The screen changes to the green “Speaking” state.
8. Piper generates and plays the response through the speaker.
9. The system returns to the listening state.


*Include videos or screencaptures of both the system and the controller.*


The blue interface tells the participant that the microphone is active and
that the system is ready to receive a command.

<img width="4032" height="3024" alt="175337d83e22cbf8691ec289eea5ac7d" src="https://github.com/user-attachments/assets/bb214e64-eeca-4a35-80f5-a1b785f5a864" />


### Speaking State

The green interface indicates that the assistant is responding. The screen
also displays a shortened version of the spoken response.

<img width="3717" height="2367" alt="d67eb1ae7d7c7456e75f5171682b4eab" src="https://github.com/user-attachments/assets/0ee7ec35-a9ca-41e1-8d75-f06ef080aa7e" />


### Timer

After the participant confirms a timer duration, the screen changes to purple
and displays a live countdown and progress bar.


<img width="4032" height="3024" alt="1046b68caa358688b95fcd2f038ea0c2" src="https://github.com/user-attachments/assets/b0862d4d-5f0b-4db6-8cc1-eb06e00636bb" />


### Interaction Demonstration

The following video demonstrates a participant speaking to the cooking
assistant, the screen changing between interaction states, and the Raspberry
Pi producing a spoken response.



https://github.com/user-attachments/assets/eb0bd011-a1b5-45b8-91fb-e226d649e2ee

## Test the system

Try to get at least two people to interact with your system. (Ideally, you would inform them that there is a wizard *after* the interaction, but we recognize that can be hard.)

Answer the following:

### What worked well about the system and what didn't?
\*\**your answer here*\*\*

### What worked well about the controller and what didn't?
\*\**your answer here*\*\*

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?
\*\**your answer here*\*\*

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?
\*\**your answer here*\*\*

<details>
  <summary><strong>Submission Cleanup Reminder (Click to Expand)</strong></summary>

  **Before submitting your README.md:**
  - This readme.md file has a lot of extra text for guidance.
  - Remove all instructional text and example prompts from this file.
  - You may either delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
  - Your final submission should be neat, focused on your own work, and easy to read for grading.
</details>
