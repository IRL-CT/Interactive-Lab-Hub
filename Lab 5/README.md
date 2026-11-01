# Observant Systems: Overnight Sensation

**Team:** Ignorance is bliss

**Members:** Yan Shen (ys2473, ys2473), Yangchen Jin (yj645, MortalJin)

**Project name: Camera Fantasic Night**

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

\*\*\***Include a screenshot of `ollama list` showing your models.**\*\*\*

<img width="1088" height="144" alt="image" src="https://github.com/user-attachments/assets/3c1d195c-74d3-4496-8546-2bfc150c67b7" />



## Part B. 
### See: recognize people in real time with YOLO

**Successfully Recognized**

<img width="700" alt="Screenshot 2026-10-26 at 4 54 21 PM" src="https://github.com/user-attachments/assets/4d7e2c51-32d8-47a7-bf9b-bee5be355974" />

<img width="700" alt="Screenshot 2026-10-26 at 4 55 04 PM" src="https://github.com/user-attachments/assets/3bb104bc-08c4-4425-b0c3-bffed9a68528" />

<img width="700" alt="Screenshot 2026-10-26 at 4 55 28 PM" src="https://github.com/user-attachments/assets/f2cbfe42-f79f-4548-b825-34ad76fc5c24" />

<img width="700" alt="Screenshot 2026-10-26 at 4 55 42 PM" src="https://github.com/user-attachments/assets/24200ebf-73c5-4c59-9f3f-00b16cc03a03" />

**Unsuccessfully Recognized**

<img width="700" alt="Screenshot 2026-10-26 at 5 18 41 PM" src="https://github.com/user-attachments/assets/7c15fd92-af8d-45cf-b67d-1208b8308925" />

1. **Holding up a photo of a person on my phone:** YOLO boxed the man on my phone screen as a person (0.76), even though he was not in the room. It also found two extra "people" around my hand and arm (0.68 and 0.56), so it counted 4 objects when there was really just me and a phone. I think it can't tell a real person from a flat picture of one, because the photo looks the same to it. And a hand or arm close to the camera looks like part of a body, so it guesses "person".

<img width="700" alt="Screenshot 2026-10-26 at 5 19 37 PM" src="https://github.com/user-attachments/assets/c1b329d8-6b34-4b47-bbc5-0929b3325377" />

2. **Holding up a webcam box:** it called the box a "cell phone" (0.76). It still found me as a person (0.87) even with my face mostly covered, which was good. I think it picked "cell phone" because COCO has no "box" class, and a small rectangle held up next to a face looks a lot like someone holding a phone.


<img width="700" alt="Screenshot 2026-10-26 at 5 19 47 PM" src="https://github.com/user-attachments/assets/1271b048-4780-4d82-8592-152a7a284df3" />

3. **Holding a mouse close to the camera:** it called the mouse a "suitcase" (0.53), and in other frames a "cell phone" (0.60), so the label kept flipping. My hand at the bottom was detected as a separate person (0.41). Also, the person sitting behind the glass on the right was never detected. I think the mouse was too close and blurry, so the model only saw a big dark rounded shape. The person behind the glass was small, partly hidden, and seen through a reflection, so it missed them.

## Part C. 
### See more: hands and pose with MediaPipe

\*\*\***Include a screenshot or short video of the hand pose demo, and write how you might use face, hand or body pose tracking in your observant system.**\*\*\*

[Watch Video](https://youtu.be/5uTxqnljpyc)

We could use hand tracking for the "before bed" part of my idea. Instead of typing a command, we can show a goodnight gesture (like an open palm) to the camera, and that tells the Pi to take the desk photo and start the night. 
It's easier than finding a button in the dark.



## Part D. 
### Reason: run Qwen on the Pi with Ollama

\*\*\***Ask Qwen three questions to answer. Paste the questions, the answers and how long each took. Try one of them with `qwen3:0.6b` and compare.**\*\*\*

**Q1: What is the capital of France?**
qwen3.5:0.8b: The capital of France is **Paris**.
Time: 54.4s (total duration). Most of the time was spent on thinking (337 tokens at 6.84 tokens/s).

**Q2: Who wrote Romeo and Juliet?** (thinking off)
qwen3.5:0.8b: Romeo and Juliet was written by William Shakespeare. ... It consists of four acts ...
Time: 17.6s
Note: The author is correct, but it made up details. The play has five acts, not four, and it did not premiere at Stratford-upon-Avon.

**Q3: What is 12 times 8?** (thinking off)
qwen3.5:0.8b: ... Final Answer: 12 × 8 = 96.
Time: 25.8s
Note: The final answer is correct, but the first step-by-step method is wrong (it gets 30), and only the second method (80 + 16) is right.

**Comparison: What is 12 times 8? with qwen3:0.6b** (thinking off)
qwen3:0.6b: 12 multiplied by 8 equals **96**.
Time: 8.1s total, but 7.4s was loading the model. Generating the answer only took about 0.6s.

qwen3:0.6b was much faster than qwen3.5:0.8b (23.28 vs 6.71 tokens/s) and gave a short, correct answer. qwen3.5:0.8b took 25.8s and wrote a long explanation with one wrong method. For a simple question like this, the smaller model worked better.

## Part E. 
### Connect: from YOLO readings to Qwen reasoning

<img width="643" height="588" alt="6fdbcb92d2cd76aa3a823ae90ca7e148" src="https://github.com/user-attachments/assets/61e11d7b-46d1-45c7-a8ae-cf6cfb0dd2d7" />

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

<img width="1645" height="1279" alt="49f209699be69ce7671f768e68a0fe42" src="https://github.com/user-attachments/assets/4ebf3c31-77eb-4a2b-977b-b2caa9e953b9" />

## Prep for Part 2

1. Look at and give feedback on the Part F storyboards.
   **Put the feedback for your ideas here.**
2. [Update your Lab Hub](prep.md#get-the-latest-content) to get the latest content for Part 2.
3. Decide where the device will spend the night and who else lives there. Get their OK before the first run.
4. Revise your storyboard with the feedback and with what you learned in Part E about where the pipeline breaks.

\*\*\***Post your revised storyboard here.**\*\*\*

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
