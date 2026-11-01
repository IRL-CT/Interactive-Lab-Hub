# Observant Systems: Overnight Sensation

**Team:**

**Members:** Yuqi Wang (yw2897)

**Project name:** Desk Night Watch

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
\*\*\***Include a screenshot of `ollama list` showing your models.**\*\*\*
![ollama](./ollama.png)




## Part B. 
\*\*\***Include a short video or screenshots of the person detection.**\*\*\*
![pb1](./P-B-1.png)
![pb2](./P-B-2.png)
![pb3](./P-B-3.png)
![pb4](./P-B-4.png)

## Part C. 
\*\*\***Include a screenshot or short video of the hand pose demo, and write how you might use face, hand or body pose tracking in your observant system.**\*\*\*
![pc1](./P-C-1.jpg)
![pc2](./P-C-2.jpg)
![pc3](./P-C-3.jpg)
![pc4](./P-C-4.jpg)

## Part D. 
### Reason: run Qwen on the Pi with Ollama
\*\*\***Ask Qwen three questions to answer. Paste the questions, the answers and how long each took. Try one of them with `qwen3:0.6b` and compare.**\*\*\*

I ran three questions with `qwen3.5:0.8b` using `ask_qwen.py`, then repeated the first question with `qwen3:0.6b`. Thinking was disabled. The script requested at most three short sentences and set a maximum of 120 generated tokens. The times below are the elapsed request times reported by the script.

### Question 1: Roosevelt Island history

**Question:** Tell me a bit about the history of Roosevelt Island.

**Model:** `qwen3.5:0.8b`  
**Elapsed time:** 12.9 seconds

**Original answer:**

> Roosevelt Island was originally built as a private residence for President Franklin D. Roosevelt, who lived there from 1935 to 1945. It is now a historic site and one of the most popular tourist destinations in New York City. The island's history includes its original construction by the Rockefeller family and its current status as a museum dedicated to FDR's life and work.

**Correctness check:**

The answer contains major factual errors. Roosevelt Island was not built as FDR?s private residence, and the claim that he lived there from 1935 to 1945 is incorrect. His principal residence was Springwood in Hyde Park, New York. The Rockefeller construction story and the description of the entire island as an FDR museum are also inconsistent with its documented history. [FDR Presidential Library](https://www.fdrlibrary.org/roosevelt-homes)

The correct historical reference points are:

- The island was formerly called **Blackwell?s Island**.
- It became **Welfare Island in 1921**.
- It was renamed **Roosevelt Island in 1973**.
- Cornell Tech opened its Roosevelt Island campus in **2017**.

The first three facts are documented by the [National Park Service](https://www.nps.gov/places/blackwell-s-island-new-york-city.htm), and the campus opening is documented by [Cornell Tech](https://tech.cornell.edu/news/cornell-tech-campus-opens-on-roosevelt-island-marking-transformational-mile/). The model mentioned none of these four reference facts.

### Question 2: Can object detection establish whether someone is asleep?

**Question:** Can a person's bounding box and confidence score alone tell whether they are asleep? Explain briefly.

**Model:** `qwen3.5:0.8b`  
**Elapsed time:** 7.1 seconds

**Original answer:**

> Yes, but the system cannot definitively determine if someone is asleep solely based on these metrics. The user must also consider their physical state, such as breathing patterns or heart rate to confirm sleep onset.

**Correctness check:**

The answer is internally contradictory: it begins with ?Yes,? but immediately explains that these metrics alone cannot determine whether someone is asleep. The direct answer should be **No**.

A bounding box describes an object?s location and size, while the confidence score concerns its detected class. A high confidence score for ?person? is not a probability that the person is asleep. These outputs alone do not establish sleep state. [Ultralytics object detection documentation](https://docs.ultralytics.com/tasks/detect)

The model also mentions breathing and heart rate, but those signals were not measured by this experiment. Its suggestion should not be interpreted as a validated sleep-detection method.

### Question 3: Describe an image

**Question:** How many people are in this photo, and what are they wearing?

**Input:** The same `zidane.jpg` image used in Part A, supplied with `--image zidane.jpg`.

**Model:** `qwen3.5:0.8b`  
**Elapsed time:** 116.0 seconds

**Original answer:**

> There are two men in the photo. The man on the left is bald and wearing a black suit with a white shirt and black tie. The man on the right has gray hair and is also wearing a black suit with a white shirt and dark tie.

**Correctness check:**

The main description matches the image. There are two people, both wearing dark suits, light-colored shirts, and ties. The descriptions of the left person?s bald head and the right person?s gray hair also match the visible image.

The model answered the requested count and clothing questions reasonably well, although precise clothing colors depend on lighting. This image request took 116.0 seconds, considerably longer than either text-only request in this run.

### Comparison with `qwen3:0.6b`

I repeated Question 1 with the smaller model using exactly the same question.

**Question:** Tell me a bit about the history of Roosevelt Island.

**Model:** `qwen3:0.6b`  
**Elapsed time:** 6.9 seconds

**Original answer:**

> Roosevelt Island is a small island located in the Pacific Ocean, off the coast of the state of New York. It was originally a military base during World War II, and it became a significant site for the United States Navy. The island was later used as a research and development center for the United States Department of Defense. Today, it remains a popular destination for outdoor activities and is a symbol of the United States' commitment to the Pacific.

**Correctness check:**

The location is incorrect: Roosevelt Island is in New York City?s **East River**, not the Pacific Ocean. The military-base, Navy, and Department of Defense narrative is unsupported by the official historical accounts, which describe institutional uses including prisons and hospitals. [National Park Service](https://www.nps.gov/places/blackwell-s-island-new-york-city.htm), [New York City historical resources report](https://www.nyc.gov/html/oec/downloads/pdf/dme_projects/12DME004M/DEIS/12DME004M_DEIS_07_Historic.pdf)

This answer also contains four sentences, exceeding the script?s request for at most three.

| Aspect | `qwen3.5:0.8b` | `qwen3:0.6b` |
|---|---|---|
| Time for the same history question | 12.9 seconds | 6.9 seconds |
| Main factual problems | Invented FDR residence and island history | Incorrect location and unsupported military history |
| Answer length | 3 sentences | 4 sentences |
| Covered the four reference facts | 0 of 4 | 0 of 4 |

The smaller model completed this request **6.0 seconds sooner**, approximately **46.5% less elapsed time**. However, both models produced unreliable historical answers. The larger model followed the sentence limit, while the smaller one did not.

These are single-request measurements, not a controlled performance benchmark. Model loading, caching, and answer length can affect elapsed time. For my observant system, these results suggest keeping model questions narrow, supplying relevant observations, and checking unsupported claims before using an answer to trigger an action.


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

Before bed, I will start Desk Night Watch and receive an on-screen confirmation that monitoring has begun. 
While I sleep, the Raspberry Pi will sample the desk area with a webcam every 10 seconds and save detection records locally. 
In the morning, a short report will show the last time a person was detected, or state that no person was detected during sampling.

![storyboard](./storyboard.png)


## Prep for Part 2

Design Feedback

1. Make the hand-off clearer. Before starting, briefly check the camera framing and test detection under the intended overnight lighting. Display “Watch started” so the user knows recording has begun.
2. Separate camera failures from no detections. Continue sampling every 10 seconds, but record failed captures separately from valid samples containing no detected person. Keep timestamped detection results locally without retaining camera images.
3. Keep the morning report honest. Report the last recorded person detection and any gaps in the observations. If there are no detections, say “No person detected in valid samples,” without claiming that the desk was unused or that the user was asleep.
Revised Storyboard

The revised design adds a brief camera and lighting check before the bedtime hand-off. During the night, it will record detection results and flag camera failures. In the morning, it will present the last recorded detection alongside any missing observations, making the limits of the report visible.

![revised](./revised.png)



## Part G. 
### Design the interaction before

I designed a short voice interaction to hand the night over to Desk Night Watch. The original command was “Start night watch,” but speech recognition repeatedly misinterpreted it. I simplified the command to “Hello” for the successful test.

The small display first shows “LISTENING” and prompts the user to speak. After accepting the command, the system checks the camera and begins recording observations. Only after the first successful sample is saved does the display show “WATCHING — Watch started,” accompanied by the spoken confirmation “Night watch started.” Microphone recording then remains off, and the screen turns off shortly afterward while observation continues.

30-second test results
Time	Observed result
15:40:26	“Hello” was recognized and accepted on the first attempt.
15:40:29	Camera logging began, and the system confirmed that the watch had started.
15:40:43	The screen turned off while observation continued.
15:41:00	The demonstration completed normally and saved its log.


The test used a 30-second observation period with a 10-second sampling interval. It demonstrated the voice-triggered hand-off, display and speaker confirmation, and successful completion of a short recording session. A full overnight run remains to be tested in Part H.

## Part H. 
### Incorporate the observant system

Part H. Incorporate the Observant System

Desk Night Watch uses the Raspberry Pi and webcam to observe the desk and chair area. After the voice hand-off, desk_watch.py runs YOLO with a configured sampling interval of 10 seconds. Each sample records a timestamp, the detected person count, and a brief description of their position in night_log.jsonl. Camera or inference failures are recorded separately from valid samples with no person detected. The system keeps text records locally without saving camera images.

Short test

I completed a 30-second test before attempting an overnight run. The log contained three valid samples:
Time	Detection
15:40:29	One person at center/close
15:40:40	One person at center/close
15:40:50	No person detected


No sampling errors were recorded, and the session ended normally. These observations show two samples containing a person, rather than two distinct people. The last recorded person detection was at 15:40:40.

Overnight setup

For the overnight test, I will position the camera toward the desk and chair area and check detection under the intended lighting. I will run the system inside a tmux session so it can continue after I disconnect my Mac. The Pi will remain powered, and I will stop the recording the following morning.

Running-system evidence

Pending: add a photo or short video showing the device placement and the system running.

Overnight results

The overnight test has not yet been completed. After the home test, I will add the recording start and end times, detection results, any errors or recording gaps, and a link to the actual night_log.jsonl file.

## Part I. 
### Design the interaction after
The morning interaction answers one question: “When was a person last detected in the desk area?” After stopping the watch, the user runs desk_morning.py and reads a short text report in the SSH terminal. The report includes the last recorded person detection, the final sample, and any recorded errors or long gaps.

If valid samples contain no detections, the report states that no person was detected in those samples. If there are no valid observations, it states that presence cannot be assessed. Neither result establishes that the desk was unused or that someone was asleep.

Design Iteration

The original free-text report incorrectly described an hour-long observation, two people, and sleeping occupants. These claims were unsupported by the short-test log.

I revised the reporting pipeline so Python computes the facts directly from the log. Qwen receives these facts and returns structured JSON, which the program compares against the computed values. The displayed sentences come from a Python template, while Qwen’s original response and the comparison results are saved separately. This checks consistency with the log; it does not eliminate errors in the camera’s detections.

Short-Test Results

The approximately 30-second test contained three valid samples. Two samples detected a person, with a maximum of one person in any sample. The last person detection was at 15:40:40, and the final sample at 15:40:50 detected nobody. No sampling errors or long recording gaps were recorded.

The revised report matched these observations, and Qwen’s structured response passed the field-by-field comparison. This was a short functional test, not an overnight validation.

Overnight Results and Evidence

Pending: after the home overnight run, I will add the actual morning report, a screenshot of its presentation, links to the corresponding log and report files, and a video clip showing the morning interaction.

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
