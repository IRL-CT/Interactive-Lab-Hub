# Observant Systems: Overnight Sensation

**Team: Tram Observers**

**Members:** Viktor Radev - Github: https://github.com/LaboriouslyExquisite/Interactive-Lab-Hub, Alex Yang - https://github.com/Alexyen04/Alex-Yen-Interactive-Lab-Hub

**Project name: Real Time Tram Locator**

<details>
	<summary><strong>Instructions for Students (Click to Expand)</strong></summary>
  
	**Submission Cleanup Reminder:**
	- This README.md contains extra instructional text for guidance.
	- Before submitting, remove all instructional text and example prompts from this file.
	- You may delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
	- Your final submission should be neat, focused on your own work, and easy to read for grading.
  
	This helps ensure your README.md is clear, professional, and uniquely yours!
</details>


For lab this week, we focus on creating interactive systems that can detect and respond to events or stimuli in the environment of the Pi, like the Boat Detector we mentioned in lecture. 
Your **observant device** could, for example, count items, find objects, recognize an event or continuously monitor a room.

This lab will help you think through the design of observant systems, particularly corner cases that the algorithms need to be aware of.

**New this year: the AI runs on the Pi.** Your Pi 5 can run an object detector ([YOLO](https://docs.ultralytics.com/)) and a small language model ([Qwen](https://ollama.com/library/qwen3.5) through [Ollama](https://ollama.com)) completely offline. In Part 1 you get both running and connect them: YOLO *sees*, Qwen *reasons* about what was seen. These models are slow, but they have all night. In Part 2 you use them to design a **night-time interaction**: what you tell the device before bed, what it does while you sleep, and what it shows you when you wake up.

**Please indicate anyone that helped with this Lab here.**
Be generous in acknowledging their contributions! And also recognizing any other influences (e.g. from YouTube, Github, Twitter) that informed your design. 

## Overview

**Part 1: the tools**

A) [Set up your Pi for on-device AI](#part-a)

B) [See: recognize people in real time with YOLO](#part-b)

C) [See more: hands and pose with MediaPipe](#part-c)

D) [Reason: run Qwen on the Pi with Ollama](#part-d)

E) [Connect: from YOLO readings to Qwen reasoning](#part-e)

**Part 2: Overnight Sensation**

F) [Read Part 2 and storyboard your night-time interaction](#part-f)

G) [Design the interaction before bed](#part-g)

H) [Incorporate the observant system during sleep](#part-h)

I) [Design the interaction when awake](#part-i)

The tools from earlier versions of this lab (MobileNet, Teachable Machine, Moondream, audio analysis, classic OpenCV) live in the [legacy folder](legacy/README.md). They are optional, but any of them can be the sensor in your Part 2 system.


## Prep for Part 1

Please check the instructions in [prep.md](prep.md) and complete them before lab. The installs in Part A take a while, so prep.md also tells you how to get a head start.

## The Report

This readme.md page in your own repository should be edited to include the work you have done. You can delete everything but the headers and the sections between the \*\*\***stars**\*\*\*. Write the answers to the questions under the starred sentences. Include any material that explains what you did in this lab hub folder, and link it in the readme.

---

# Part 1

## Part A. 
### Set up your Pi for on-device AI

Create a virtual environment and install the requirements. They include `ultralytics` (YOLO), which pulls in torch, so this takes a while:

```
pi@raspberrypi:~$ cd Interactive-Lab-Hub/Lab\ 5
pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python3 -m venv .venv
pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ source .venv/bin/activate
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ pip install -r requirements.txt
```

As in Lab 3, [`uv`](https://docs.astral.sh/uv/) is a much faster drop-in for `pip`: `pip install uv && uv pip install -r requirements.txt`.

### YOLO: download the nano model and export it for the Pi

We use the nano model of [YOLO26](https://docs.ultralytics.com/models/yolo26/), exported once to NCNN, the format that runs fastest on the Pi. This downloads the weights, so you need internet:

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python -c "from ultralytics import YOLO; YOLO('yolo26n.pt').export(format='ncnn')"
```
If every ultralytics message is followed by a `--- Logging error ---` traceback ending in `UnicodeEncodeError: 'latin-1' codec can't encode character`, fix your shell's locale once::

```
echo 'export LANG=C.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=C.UTF-8' >> ~/.bashrc
echo 'export PYTHONIOENCODING=utf-8' >> ~/.bashrc
source ~/.bashrc
```

Test it on an image from the internet. `project=runs` keeps the output in this folder; without it, ultralytics writes to a `runs/` folder at the top of your git repo, where you will not think to look.

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ yolo predict model=yolo26n_ncnn_model source=https://ultralytics.com/images/bus.jpg project=runs
```

The result is in `runs/predict/bus.jpg`: boxes around the people and the bus.

Now a photo of your own. Plug in the webcam and take one with `snap.py` (`--delay 3` gives you three seconds to get into the frame), or choose any picture you downloaded from the internet and put under this folder. Put your selected picture after the `source=` Then run the same command on it:

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python snap.py --delay 3
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ yolo predict model=yolo26n_ncnn_model source=snap.jpg project=runs
```

Every run gets its own numbered folder, so this one is in `runs/predict2/snap.jpg`; the command prints where it saved. Keep `snap.jpg`, you will show it to Qwen in Part D.

### Ollama: install it and pull Qwen

[Ollama](https://ollama.com) runs language models locally. Nothing leaves the Pi: no API key, no internet after the download.

```
pi@raspberrypi:~ $ curl -fsSL https://ollama.com/install.sh | sh
pi@raspberrypi:~ $ ollama pull qwen3.5:0.8b
pi@raspberrypi:~ $ ollama pull qwen3:0.6b
pi@raspberrypi:~ $ ollama list
```

| model | download | what it does |
|---|---|---|
| `qwen3.5:0.8b` | ~1.3 GB | text **and images**; the one we use in this lab |
| `qwen3:0.6b` | ~0.5 GB | text only, smaller and faster (~16 tokens/s on a Pi 5) |

\*\*\***Include a screenshot of `ollama list` showing your models.**\*\*\*

pi@vr373:~ $ ollama list
NAME            ID              SIZE      MODIFIED           
qwen3:0.6b      7df6b6e09427    522 MB    26 seconds ago        
qwen3.5:0.8b    de63045f2975    1.3 GB    About a minute ago 

<img width="561" height="135" alt="image" src="https://github.com/user-attachments/assets/55f621c6-7d5e-4c4e-9d1a-af7e3f308e53" />

## Part B. 
### See: recognize people in real time with YOLO

YOLO is an *object detector*: it finds every person, cup, cat and so on (the 80 [COCO](https://cocodataset.org/) classes), draws a box around each, and gives a confidence. For an observant system that is exactly what you want: *how many*, *where*, *how sure*.

Connect your webcam, connect to your Pi through **VNC** (the script opens a window), and run the person detector. Read `yolo_person.py` first; the loop at the bottom is the whole idea.

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python yolo_person.py
```

While it runs, walk in and out of the frame, sit down, turn your back, turn the lights off, hold up a photo of a person on your phone. Watch the confidence number on the box change with each.

Then press q to quit and run it again with a flag. Each one changes a single thing:

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python yolo_person.py --conf 0.2     # lower the bar: see what the model is unsure about
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python yolo_person.py --conf 0.7     # raise the bar: see what you lose
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python yolo_person.py --all          # all 80 classes, not only people: what else is on your desk, and what does it get wrong?
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python yolo_person.py --headless     # no window, only the printed readings: how it runs over ssh, and at night
```

\*\*\***Include a short video or screenshots of the person detection.**\*\*\*

<img width="1601" height="977" alt="image" src="https://github.com/user-attachments/assets/8f533f8d-b894-40ef-9888-e728632b852a" />

After running:  python yolo_person.py --all: It thought the phone is a remote and my pencil box is a tv, which shows the limitations of this data set!
<img width="1597" height="997" alt="image" src="https://github.com/user-attachments/assets/80cb3eea-a2d3-451d-9195-8247977091d8" />


## Part C. 
### See more: hands and pose with MediaPipe

YOLO tells you that a person is there. Google's [MediaPipe](https://mediapipe.dev/) tells you what their hands and body are doing: face, hand and body pose detection, fast on the Pi.

![Media pipe](Readme_files/mp.gif)

The demo plays a looping audio file, so make the helper script executable first:

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ chmod +x loop_audio.sh
```

Connect your webcam, connect to your Pi through **VNC**, and run the hand pose script:
(***it will not work if you use ssh from your laptop***)

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python hand_pose.py
```

Try the two main features of this script: 1) pinching for percentage control (the thumb-to-index distance sets the volume), and 2) "[Quiet Coyote](https://www.youtube.com/watch?v=qsKlNVpY7zg)" for instant percentage setting (the gesture mutes it). Notice how this example uses hardcoded positions and relates those positions with a desired set of events, in `hand_pose.py`: a hand is 21 landmark coordinates, and an *event* is a rule you write over them. That is the same job as `interpret()` in Part E.

Consider how you might use this position based approach to create an interaction, and write how you might use it on either face, hand or body pose tracking.

\*\*\***Include a screenshot or short video of the hand pose demo, and write how you might use face, hand or body pose tracking in your observant system.**\*\*\*

<img width="1002" height="1073" alt="image" src="https://github.com/user-attachments/assets/3ad4ccd8-77cc-40d0-b06c-63550441629e" />

<img width="1013" height="1078" alt="image" src="https://github.com/user-attachments/assets/b3115c01-a2d2-446b-ab8f-38f450caa616" />

<img width="1012" height="1078" alt="image" src="https://github.com/user-attachments/assets/01f41e82-a3d8-46c1-a8e6-41c754edcf98" />

Predefined poses and events are a great way to activate your raspberry pi from a state in which it's just observing. Events and poses are low cost triggers to help change our neutral observing raspberry pi into something that reacts in real time to it's environment! For example, my partner and I want to determine who leaves the bathroom lights on the most out of our three roommates, and pose estimation would be a great way to figure out when our raspberry pi should note when someone is leaving the bathroom vs when someone is entering the bathroom. And when this happens we can have the raspberry pi take an image with a note of who it infers is in the image and with that is we are able to verify who exactly is going into the bathroom and out of the bathroom and when. Then depending on who goes in and out of the bathroom we have to track when the lights are turned on and off, and we can take make this computationally heavy task only run when someone is entering or existing the room so it doesn't overload our raspberry pi's processor unnecessarily. Overall events and pose estimation of ap persons face, hand, or body is a helpful way to tell how our systems should react in real time at a low cost of computation.

## Part D. 
### Reason: run Qwen on the Pi with Ollama

Talk to the model in the terminal first. Qwen3 models "think" before they answer, which is slow on a Pi, so turn it off. Then ask about something you can check:

```
pi@raspberrypi:~ $ ollama run qwen3.5:0.8b
>>> /set nothink
>>> Tell me a bit about the history of Roosevelt Island. Three sentences.
>>> /bye
```

Roosevelt Island is a good first question because you know the ground truth: it was Blackwell's Island, then Welfare Island, got its current name in 1973, and Cornell Tech opened on it in 2017. Count how many of the model's facts are true.

From Python it is a dozen lines with `requests`; `ask_qwen.py` is that script. It turns thinking off, tells the model to answer in at most three sentences, and cuts it off after 120 tokens (`--max-tokens` changes that), because a small model left alone writes an essay. Read it, then run:

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python ask_qwen.py "Tell me a bit about the history of Roosevelt Island."
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python ask_qwen.py --model qwen3:0.6b "Tell me a bit about the history of Roosevelt Island."
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python ask_qwen.py --image snap.jpg "What is in this photo?"
```

Things in the [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md) worth knowing:

* `think: false` skips the reasoning trace. Always, on a Pi. `ask_qwen.py` sends it on every request; `--think` turns the trace back on for one question, so you can see what you are skipping and how long it takes.
* `format` makes the model answer as JSON with the fields you name (`--json`). Handy when a display or a servo has to read the answer.
* `images` sends a photo along with the prompt (`--image snap.jpg`, the photo from Part A). `qwen3.5:0.8b` can look at pictures.

A 0.8B model is slow and sometimes wrong. It will invent events that are not in the data and agree with a wrong premise. Give it the data, keep its job narrow, and decide what the device does when the model is unsure.

\*\*\***Ask Qwen three questions to answer. Paste the questions, the answers and how long each took. Try one of them with `qwen3:0.6b` and compare.**\*\*\*

<details>
  Q&A here

	**1. 0.8B output:**

```
(.venv) pi@vr373:~/Documents/GitHub/Interactive-Lab-Hub/Lab 5 $ ollama --verbose run qwen3.5:0.8b
Ã¢Â  
>>> /set nothink
Set 'nothink' mode.
>>> What is the weird symbol "a" you are generatitng before you start typing ou 
... t your answer? Is the sky blue? How full is the cup in front of me?
No, I cannot speak to what is happening in real life or observe the 
outside world directly. As an AI generated by a system running on servers, 
I do not have eyes, ears, physical presence, or direct access to your 
actual environment like a cup.

Regarding your question: **Is the sky blue?** Yes, when looking at it from 
this distance, the sky appears blue due to Rayleigh scattering of sunlight 
by particles in the atmosphere. It is generally clear and blue in summer 
days.

And **how full is the cup in front of me?** Since you are referring to a 
physical object (a cup), I cannot physically touch or see it. My current 
context window has 8192 tokens, and my memory of your conversations might 
be very limited right now, so I likely do not have enough data about what 
you have been holding to provide an accurate "fill" rate.

It seems like a conversation between two different characters, but let's 
just say that if there is a cup in front of someone who asks these 
specific questions, they are likely holding something small and colorful! Ã°	
Ã°Â¡

total duration:       1m55.386661622s
load duration:        1.761546ms
prompt eval count:    50 token(s)
prompt eval duration: 1.891353s
prompt eval rate:     26.44 tokens/s
eval count:           227 token(s)
eval duration:        1m53.490289s
eval rate:            2.00 tokens/s
```

**2. 0.6B output:**

```
pi@vr373:~/Documents/GitHub/Interactive-Lab-Hub/Lab 5 $ ollama --verbose run qwen3:0.6b
>>> /set nothink
Set 'nothink' mode.
>>> What is the weird symbol "a" you are generating before you start yping out y
... our ansewr? is the sky blue? How full is the cup in front of me? 
The question you're asking is a bit cryptic and not very clear. However, 
if you're referring to a specific symbol or object, here's some 
information:

1. **The "a" symbol**: In some contexts, "a" can represent a variety of 
things, such as a letter, a sound, or a concept. However, without more 
context, it's hard to pinpoint a specific meaning.

2. **The sky**: In many cultures, the sky is associated with the sky 
above, but without more details, it's hard to say what you're referring 
to.

3. **The cup**: If you're asking about a cup in front of you, it's 
possible that it's a specific object of interest, but without more 
information, it's hard to determine its state.

If you can provide more details, I'd be happy to help clarify the question.

total duration:       28.224813712s
load duration:        1.610325ms
prompt eval count:    53 token(s)
prompt eval cached:   17 token(s)
prompt eval duration: 566.082ms
prompt eval rate:     63.60 tokens/s
eval count:           179 token(s)
eval duration:        27.651955s
eval rate:            6.47 tokens/s
```


What I asked: one prompt with three questions to both models, with thinking turned off: (1) what the weird “â” symbol before each answer is, (2) whether the sky is blue, and (3) how full the cup in front of me is.

| Metric | Qwen3.5:0.8b | Qwen3:0.6b |
| :--- | :--- | :--- |
| **Total time** | 1 min 55 s | 28 s |
| **Tokens generated** | 227 | 179 |
| **Speed** | 2.0 tokens/s | 6.5 tokens/s |


qwen3.5:0.8b gave real answers but filled them with made-up details. It correctly said it can’t see my cup, and it explained that the sky is blue because of Rayleigh scattering, which is right. Then it invented things: it claimed an 8192-token context window as the reason it couldn’t answer about the cup, called the exchange “a conversation between two different characters,” and guessed the cup was “small and colorful.” It skipped the symbol question entirely. It also took almost 2 minutes.

qwen3:0.6b was about 4× faster but avoided answering. It hedged every question with some version of “without more context it’s hard to say,” including the sky question, which has a simple factual answer. It invented nothing, but it also told me nothing.

Takeaways: the bigger model is more useful but more confident in its fabrications. The smaller one is faster but evasive. Neither can answer a question about the physical world from text alone. The “â” symbol was a terminal encoding glitch in Ollama’s loading spinner (a locale setting), which no model could have known. This matches the README’s warning: give the model the data and keep its job narrow. That’s why Part E feeds Qwen YOLO readings rather than asking it open questions.

</details>

## Part E. 
### Connect: from YOLO readings to Qwen reasoning

An observant system is a pipeline: a **detector** turns pixels into boxes, an **interpreter** turns boxes into readings in words ("one person, left, close"), the readings pile up in a **log**, and a **reasoner** answers a question about the log. The language model never sees pixels, only the words you chose in the interpreter. That makes the interpreter the most important design decision in the system.

`yolo_to_qwen.py` is the pipeline in one file, one function per stage. Read it before you run it:

* `interpret(r)` is the interpreter. It takes one YOLO result and returns one reading. A person is *left*, *center* or *right* by which third of the frame the middle of their box is in, and *close* if the box is taller than 60% of the frame, *far* otherwise. The reading is a string like `1 person(s) at center/close`, or `nobody`. Fifteen lines, and they decide everything the model can know.
* `watch(seconds)` is the detector and the log. Twice a second it reads a frame, runs YOLO on it and calls `interpret()`. A time-stamped reading goes into the log **only when it differs from the previous one**, so a minute of sitting still is one line, not 120.
* `ask(log, question)` is the reasoner. It pastes the log and your question into one prompt, tells Qwen to answer in at most three sentences using only what is in the log, and sends it to Ollama with thinking off.

Run it through VNC and a window opens with YOLO's boxes, the current reading and the seconds left. Press q to stop watching early. Over plain ssh add `--headless` and you get the same thing minus the window.

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python yolo_to_qwen.py
```

It watches for a minute, saves the log to `watch_log.txt` and asks Qwen the default question. The terminal looks something like this:

```
14:02:11 nobody
14:02:19 1 person(s) at right/far
14:02:24 1 person(s) at center/close
14:02:51 nobody

4 lines saved to watch_log.txt
asking Qwen...

Qwen (18.4 s):
One person came in from the right, moved close to the camera, and left after about half a minute. ...
```

---

# Lab 5 Part 2: Overnight Sensation

For Part 2, you will use the observant system from Part 1 to design a night-time interaction. On-device AI is slow, so let it work while you sleep. The person meets the device twice: **before bed**, when they hand the night over, and **when awake**, when the device gives something back. In between, the pipeline from Part E runs on its own.

Two flavors, pick one or mix them:

* **Sense all night.** The Pi watches, listens or measures from bedtime until morning and keeps a log.
* **Process all night.** You already have the data (a day of phone photos, a long recording) and the Pi needs hours to get through it.

Two house rules. Sample rather than stream: one look every 5 to 30 seconds is plenty, and it keeps the Pi cool. And keep everything on the Pi: tell the people you live with, point the camera at things rather than at beds, and delete the snapshots after the demo.

## Part F. 
### Read Part 2 and storyboard your night-time interaction

Storyboard a night-time interaction built on your observant system, in three panels:

1. **Before bed.** How does the person hand the night over, and how does the device acknowledge it?
2. **While asleep.** What does the device watch or work through?
3. **When awake.** What is the one thing the person learns, and in what medium?

Stuck? A kitchen that tells you who raided the fridge. A desk that reports whether you actually went to bed. A window that names the quietest hour. A plant that describes its night. Find something better.

Use storyboards and/or [Verplank diagrams](https://ccrma.stanford.edu/courses/250a-fall-2004/IDSketchbok.pdf).

\*\*\***Insert ideas, sketches, Verplank diagrams and storyboards for your night-time interaction here.**\*\*\*

Original Light detector(Camera Sensor + Light Sensor): 

<img width="1237" height="646" alt="image" src="https://github.com/user-attachments/assets/8ffab655-9a16-4bb4-a49a-54690f5f5b97" />


Original Tram notifier idea:

<img width="768" height="1024" alt="img_8382_1024" src="https://github.com/user-attachments/assets/794f5cfd-8834-4bca-b3e0-22d4d79be31d" />

## Prep for Part 2

1. Look at and give feedback on the Part F storyboards.
   **Put the feedback for your ideas here.**4

"Instead of having the device check whether or not someone is turning off the lights in our apartment, why not help us figure out when the tram will arrive or leave the island?" - Nurain (roomate)

"Do you think it's actually possible to make an accurate preditiction of where the tram will be located when you can only see like 1/10 of where the tram travels?" - Pranav (friend)

"How are you going to see the tram at night?" - Elena (friend) [Invest in night time camera]
   
3. [Update your Lab Hub](prep.md#get-the-latest-content) to get the latest content for Part 2.
4. Decide where the device will spend the night and who else lives there. Get their OK before the first run.
5. Revise your storyboard with the feedback and with what you learned in Part E about where the pipeline breaks.

\*\*\***Post your revised storyboard here.**\*\*\*


Accurate tram arrival and departure notifier for night time!
<img width="768" height="1024" alt="img_8385_1024" src="https://github.com/user-attachments/assets/b1353d2d-4780-4702-9c0c-f5873d2f384c" />


## Part G. 
### Design the interaction before

The hand-off: the person tells the device what to watch tonight, and the device acknowledges it. Keep it to a thirty-second ritual. A button or a touch (Lab 4), a spoken sentence (Lab 3), a wave or a Quiet Coyote at the camera (Part C). The acknowledgement can be a line on the display, a tone, or an LED that dims rather than lights up. At its simplest, the hand-off just sets the question that the morning will answer.

\*\*\***Describe the interaction before.**\*\*\*



## Part H. 
### Incorporate the observant system

The Part E pipeline becomes the night shift. `overnight.py` runs your `interpret()` from `yolo_to_qwen.py` every few seconds, people only unless you pass `--all`, and writes the readings to `night_log.jsonl`; the reasoning waits for the morning. Start it inside `tmux` so it keeps running after you close your laptop, and stop it with Ctrl-C in the morning:

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ tmux new -s night
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python overnight.py
```

Fake a night first: run it for thirty seconds while you walk around, stop it, and run `morning.py` from Part I. When that looks right, run a real night. If your storyboard needs a sensor rather than the camera, swap in the Lab 4 example code and log its reading the same way.

\*\*\***Screenshots or videos of the running system.**\*\*\*

https://youtube.com/shorts/-ntIhPmZE9A 

## Part I. 
### Design the interaction after

The reveal. The night produced a log; the morning turns it into something a half-awake person can take in. `morning.py` is the smallest version: it asks Qwen for a three-sentence report.

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 5 $ python morning.py
```

Make it yours: show the report on the Mini PiTFT, read it aloud with Piper from Lab 3, plot the night as a timeline, or ask for JSON (`--json`, Part D) and move a servo. Whatever you pick, make sure it is honest about a night in which nothing happened.

## Final documentation

Document all the prototypes and iterations you have designed and worked on. The deliverables for this lab are writings, sketches, photos, and videos that show what your system:

* "Looks like": how the device sits in the room at night, and what it looks like at bedtime and in the morning.
* "Works like": the pipeline from detector to interpreter to log to reasoner, with a real night's data.
* "Acts like": how a person hands the night over and what they get back.

\*\*\***Include a short video of the whole system**\*\*\*

https://youtube.com/shorts/-ntIhPmZE9A 

As always, make sure you document contributions and ideas from others (and AI) explicitly in your writeup.



You are permitted (but not required) to work in groups and share a turn in; you are expected to make equal contribution on any group work you do, and N people's group project should look like N times the work of a single person's lab. Make sure the page for the group turn in is linked to your personal Interactive Lab Hub page.

## Deliverables & Submission for Lab 5

For submission, the readme.md page for this lab should be edited to include the work you have done:
* Upload any materials that explain what you did, including your code and night log, into your Lab 5 repository, and link them in your Lab 5 readme.md.
* Labs are due on Sundays, make sure to submit your Lab 5 readme.md to Canvas.

<details>
  <summary><strong>Submission Cleanup Reminder (Click to Expand)</strong></summary>

  **Before submitting your README.md:**
  - This readme.md file has a lot of extra text for guidance.
  - Remove all instructional text and example prompts from this file.
  - You may either delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
  - Your final submission should be neat, focused on your own work, and easy to read for grading.
</details>
