# Chatterboxes

**Pallavi Srinivas (ps2269)**

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
In different voices, the tone and emotion that was invoked felt different. With the robotic voice, it can feel very impersonal. However, with another voice it can feel as if you are talking to another human being, which invokes more emotion.

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

(.venv) pi@raspberrypipallavi:~/Interactive-Lab-Hub/Lab 3/speech-scripts $  arecord -d 5 -f cd -c 1 -r 16000 test.wav
Recording WAVE 'test.wav' : Signed 16 bit Little Endian, Rate 16000 Hz, Mono
(.venv) pi@raspberrypipallavi:~/Interactive-Lab-Hub/Lab 3/speech-scripts $ python transcribe.py test.wav --model base.en

Hello, my name is Paul.

model            base.en (int8, beam=1)
audio duration   5.00s
model load       0.69s
transcription    1.83s
real-time factor 0.37x

(Model load is a one-time cost per process. In an interactive system you load once and keep the model resident  which is what listen.py does.)
(.venv) pi@raspberrypipallavi:~/Interactive-Lab-Hub/Lab 3/speech-scripts $ python transcribe.py test.wav --model small.en

Hello, my name is Polly.

model            small.en (int8, beam=1)
audio duration   5.00s
model load       1.25s
transcription    5.46s
real-time factor 1.09x

(Model load is a one-time cost per process. In an interactive system you load once and keep the model resident  which is what listen.py does.)
(.venv) pi@raspberrypipallavi:~/Interactive-Lab-Hub/Lab 3/speech-scripts $ 

As we can see, neither of the models registered my name (Pallavi) correctly. However, the smaller model took longer to transcribe than the audio recording took place, making the bse.en model a better choice.

\*\***Write your own script that verbally asks for a numerical input (a phone number, zipcode, number of pets) and records the answer the respondent provides.**\*\* Numbers are a good stress test — transcription systems make characteristic errors on digit strings, and you will want to know what they are before you design around them.

## C. Turn-taking: knowing when someone has stopped talking

Everything so far has worked on fixed audio files. A real conversational device does not get told when to start and stop recording — it has to decide. This is the problem that makes speech interfaces hard, and it is mostly not a speech recognition problem.

We use a **voice activity detector** (VAD) to segment the microphone stream into utterances. `listen.py` runs Silero VAD continuously and hands each detected utterance to faster-whisper:

```
(.venv) $ cd speech-scripts
(.venv) $ python listen.py
```

Loading models...
Input device: default
Endpointing after 0.4s of silence. Ctrl-C to stop.

[2.2s speech, 0.93s to transcribe]  Hello, my name is Paul of E.
^C
Stopped.


Speak, pause, and watch it transcribe. Now change the endpointing threshold — the amount of silence the system requires before it decides your turn is over:

```
(.venv) $ python listen.py --min-silence 0.2
(.venv) $ python listen.py --min-silence 1.5
```
\*\***Try both extremes, and something in between. Describe what each one feels like to talk to. Note specifically: at 0.2s, what kinds of normal speech get cut off? At 1.5s, what does the delay make the system seem like?**\*\*

At 0.2s, it felt as if the pauses between words make the phrase I spoke register as two different inputs. Additionally, the transcription isn't correct, with "Hello" reading as "below" and "Pallavi" reading as "Polivy". The slight pause between "Hello" and "my name is Pallavi" split the phrase.

0.2s:
Loading models...
Input device: default
Endpointing after 0.2s of silence. Ctrl-C to stop.

[0.5s speech, 0.83s to transcribe]  below.
[1.5s speech, 0.89s to transcribe]  My name is Polivy.
^C
Stopped.


At 1.5s, The whole phrase was transcribed together, with only my name being registered incorrectly, but that may be because of my ethnic name.

1.5s:
Loading models...
Input device: default
Endpointing after 1.5s of silence. Ctrl-C to stop.

[1.9s speech, 0.99s to transcribe]  Hello, my name is Paul Ovi.
^C
Stopped.

There is no correct value. A system that takes drink orders and a system that listens to someone think out loud want very different thresholds, and the right one depends on what your users are doing with their pauses.

### The complete loop

`echo_bot.py` puts the pieces together: it listens, endpoints, transcribes, and speaks a reply through Piper. The dialogue policy is deliberately trivial — it repeats what you said — so that everything you notice is a property of the timing rather than the content.

```
(.venv) $ python echo_bot.py
```

## D. Storyboard

Storyboard and/or use a Verplank diagram to design a speech-enabled device. (Stuck? Make a device that talks for dogs. If that is too stupid, find an application that is better than that.)

\*\***Post your storyboard and diagram here.**\*\*

Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses.

\*\***Please describe and document your process.**\*\*

Your script should include the pauses. Where does your device wait, and for how long? You now know from Part C that this is a parameter you have to choose, not something that happens for free.

<img width="5712" height="4284" alt="IMG_7285" src="https://github.com/user-attachments/assets/d3e5e280-5193-44fa-afba-1dbf8cb36d71" />



## E. Acting out the dialogue

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing. Please record this interaction (for example, using Zoom's record feature).


https://github.com/user-attachments/assets/87108adf-8704-4f1c-ad91-bbf5fd7cfc68




\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*
The dialogue obviously came out a little more forced given the fact that the action is intended to be remote (messenger should be able to be in a different location as compared to the elderly person). For that reason, the interaction felt a little bit robotic at times.

---

# Lab 3 Part 2


## Prep for Part 2

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings.
   I think the design of the web-based interface could be a little bit more fleshed out and explicitly designed. I don't have much front-end experience so this was a little difficult (needed assistance from Cursor) but if I made it have a better UI, it would be a much better user experience.
   
2. What are other modes of interaction *beyond speech* that you might also use to clarify how to interact? In particular: how does someone know when the device is listening, and when it is thinking? You have a screen and an LED.
   I think next time I would add the light as a visual reminder in addition to the audio reminder. This would be especially helpful given that there are a variety of impairements elderly face so it is good to consider from an accessibility point of view.
   

## Prototype your system

The system should:
* use the Raspberry Pi
* use one or more sensors
* require participants to speak to it

Elderly people face a multitude off health problems that require them to undergo treatments and take medication regularly. Additionally, many elderly people don't have immediate family nearby who can assist them physically, and text reminders can go over their heads as they aren't as "wired in" or "plugged in" to the world as younger people are.

With this device, family members and other loved ones can send reminders remotely with exact text-to-speech registration and enables real-time communication.
https://github.com/user-attachments/assets/de16243f-6a1e-470c-839a-1bb049a80f14



## Test the system


https://github.com/user-attachments/assets/a6674252-c84e-42e1-8cee-3260bcf7036f
https://github.com/user-attachments/assets/225a7053-3e49-46a2-8b71-6e74870b88ef







Answer the following:

### What worked well about the system and what didn't?
\*\**The system was very timely and the messages the "caretaker" sends to the system was delivered immediately. I think what could be improved is the accuracy of the model that is used for the transcriptions.*\*\*

### What worked well about the controller and what didn't?
\*\**The controller was good, again the biggest thing was that there could be an optimization of the model used to transcribe the speech sent through the mic. I think also the timing between the user speaking and the transcription appearing in the web app would be very beneficial.*\*\*

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?
\*\**your answer here*\*\*

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?
\*\**I think the dataset of interaction could entail gathering a CSV file of common phrases used in different conversations to be able to have the speaker speak certain phrases instead of relying on user input. It would also be interesting to add the use of a camera: in terms of interaction design it would be cool but maybe not good when considering user privacy.*\*\*
