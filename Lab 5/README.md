**Team:** Ignorance is bliss

**Members:** Yan Shen (ys2473, ys2473), Yangchen Jin (yj645, MortalJin)

**Project name:** Camera Fantastic Night

**Acknowledgements:** Thanks to Yan Shen for working on this lab together with me. We also used Claude (AI) to help with the code and the GitHub README formatting.

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

---

# Part 1

## Part A. 
### Set up your Pi for on-device AI

\*\*\***Include a screenshot of `ollama list` showing your models.**\*\*\*

<img width="1088" height="144" alt="image" src="https://github.com/user-attachments/assets/3c1d195c-74d3-4496-8546-2bfc150c67b7" />



## Part B. 
### See: recognize people in real time with YOLO

\*\*\***Include a short video or screenshots of your experiments with the person detection. Write down three situations where it did not see you, or saw a person who was not there, and what you think the cause was.**\*\*\*

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

We could use hand tracking for the "before bed" part of my idea. Instead of typing a command, we can show a goodnight gesture (like an open palm) to the camera, and that tells the Pi to start the night shift. 
It's easier than finding a button in the dark.



## Part D. 
### Reason: run Qwen on the Pi with Ollama

\*\*\***Ask Qwen three questions to answer. Paste the questions, the answers and how long each took. Try one of them with `qwen3:0.6b` and compare.**\*\*\*

#### Q1: What is the capital of France?
- **Model:** `qwen3.5:0.8b` (thinking on)
- **Answer:** The capital of France is **Paris**.
- **Time:** 54.4s
- **Note:** Most of the time was spent on thinking (337 tokens at 6.84 tokens/s).

#### Q2: Who wrote Romeo and Juliet?
- **Model:** `qwen3.5:0.8b` (thinking off)
- **Answer:** Romeo and Juliet was written by William Shakespeare. ... It consists of four acts ...
- **Time:** 17.6s
- **Note:** The author is correct, but it made up details. The play has five acts, not four, and it did not premiere at Stratford-upon-Avon.

#### Q3: What is 12 times 8?
- **Model:** `qwen3.5:0.8b` (thinking off)
- **Answer:** ... Final Answer: 12 × 8 = 96.
- **Time:** 25.8s
- **Note:** The final answer is correct, but the first step-by-step method is wrong (it gets 30). Only the second method (80 + 16) is right.

#### Comparison: Q3 with `qwen3:0.6b`
- **Model:** `qwen3:0.6b` (thinking off)
- **Answer:** 12 multiplied by 8 equals **96**.
- **Time:** 8.1s total, but 7.4s was loading the model. Generating the answer only took about 0.6s.

| Model | Time | Speed | Answer |
|---|---|---|---|
| `qwen3.5:0.8b` | 25.8s | 6.71 tokens/s | Correct, but long with one wrong method |
| `qwen3:0.6b` | 8.1s (0.6s without loading) | 23.28 tokens/s | Correct and short |

`qwen3:0.6b` was much faster and gave a short, correct answer. For a simple question like this, the smaller model worked better.

## Part E. 
### Connect: from YOLO readings to Qwen reasoning

<img width="643" height="588" alt="6fdbcb92d2cd76aa3a823ae90ca7e148" src="https://github.com/user-attachments/assets/61e11d7b-46d1-45c7-a8ae-cf6cfb0dd2d7" />

---

# Lab 5 Part 2: Overnight Sensation

## Part F. 
### Read Part 2 and storyboard your night-time interaction

\*\*\***Insert ideas, sketches, Verplank diagrams and storyboards for your night-time interaction here.**\*\*\*

<img width="700" alt="49f209699be69ce7671f768e68a0fe42" src="https://github.com/user-attachments/assets/4ebf3c31-77eb-4a2b-977b-b2caa9e953b9" />

**Idea: What your desk says about you while you sleep**

The objects on my desk watch me at night. In the morning, they tell me what they saw in a group chat. The camera watches the desk all night, YOLO finds the objects (monitor, laptop, keyboard, book, bottle), and Qwen turns what happened into the gossip they had about me. If YOLO gets something wrong, that object becomes an "impostor" in the chat.

## Prep for Part 2

**Feedback on our idea:** 

- Simin Xu asked if we could just record a few minutes and call it a night, since the objects on a desk don't move anyway. That was a fair question. A short test is enough to check that the code works, but it can't show what really happens overnight, like the lights going down, YOLO getting worse in the dark, or when I actually come back. So we ran it for a real night, from 01:33 to 09:54.
- We also asked ourselves: what if nothing at all happens during the night? We decided the system should be honest about it, so if the log is empty, the objects just complain that the night was boring instead of making something up.


\*\*\***Post your revised storyboard here.**\*\*\*

**Revised storyboard:** After Part E, we saw that one photo at bedtime is not enough, because nothing changes during the night. So we changed it to watch the desk all night with `overnight.py --all`, and turn the whole night's log into the group chat in the morning.

## Part G. 
### Design the interaction before

\*\*\***Describe the interaction before.**\*\*\*

Before bed, I run one command: `./goodnight.sh`. The screen says "Shh... they're waking up. Good night." and the camera starts watching the desk. I start it when I sit down at the desk in the evening, then dim the lamp when I go to sleep.

[goodnight.sh](goodnight.sh)

## Part H. 
### Incorporate the observant system

\*\*\***Screenshots or videos of the running system.**\*\*\*

The night shift ran from 01:33 to 09:54. It logged 1770 changes, mostly YOLO flickering in the dark.

<img width="700" alt="58429a42988db6fb624d461c4a30e6cd" src="https://github.com/user-attachments/assets/2f94bce9-6927-4549-b4df-89695a41d25a" />

Full log: [night_log.jsonl](night_log.jsonl)

## Part I. 
### Design the interaction after

In the morning, I stop the night shift and run `python desk_chat.py`. It first lists what changed during the night (things showing up or disappearing, me leaving, the lights going off). Then Qwen turns that list into a group chat between the objects on my desk, gossiping about me. The camera is always in the chat, since it saw everything. If nothing happened, the objects just complain that the night was boring.

[desk_chat.py](desk_chat.py)

<img width="700" alt="0299e338ad416d9c9ebba6a884d6a7b3" src="https://github.com/user-attachments/assets/12362bf8-96cc-4693-95d6-e3ce5704c278" />

Full chat: [morning_chat.txt](morning_chat.txt)

## Final documentation

\*\*\***Include a short video of the whole system**\*\*\*

[Watch the bedtime video](https://youtu.be/Cr4N5npGk0U?si=b-fSRWyauTeYW3gt) · [Watch the morning video](早上视频的链接)

- **Looks like:**

<img width="700" alt="2635b7ddb34abbcb5dcad366f90b590e" src="https://github.com/user-attachments/assets/75b2e3a0-3c26-4d63-8105-b86640e42589" />

The camera sits above the desk and looks down at the monitor, laptop, keyboard, book, and bottle. A dim lamp stays on at night.
- **Works like:** camera → YOLO (`overnight.py --all`) → night_log.jsonl → desk_chat.py → Qwen → group chat. This used a real night's data, from 01:33 to 09:54.
- **Acts like:** I hand over the night with one command and a dim lamp. In the morning, I get a group chat from my desk about what I did.

### Reflection

At first we worried that nothing on the desk moves at night. Then we realized the objects are not the story, they are the witnesses. The real events are about the person at the desk (when they really left, when the lights went off) and the cat. So we start the night shift when we sit down at the desk in the evening, not right before bed.

YOLO was not perfect. It called the monitor a "tv", and things like the mouse flickered on and off when the confidence was close to the limit. So desk_chat.py renames "tv" to "monitor" and ignores blips shorter than 60 seconds. The first few frames are also dark while the camera adjusts, so it skips the first 15 seconds.

The 0.8b model kept making up times that were not in the log (like 22:05 when the log only had 16:25 to 16:26), even when the prompt told it not to. So we added a check that drops any message with a time that is not in the log. This matches what we saw in Part D: small models are fun to write with, but you can't trust them on facts.

The real night showed how much YOLO struggles in the dark. The log had 1770 changes from 01:33 to 09:54, but almost all of them were things blinking on and off. The keyboard "disappeared" and "showed up" many times, even though nothing moved. After filtering, there were only 30 events, and the only real one was the person coming back to the desk at 09:53. So when the group chat says "the keyboard disappeared", it really means the camera couldn't see it well in the dim light.
