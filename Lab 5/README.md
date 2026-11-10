# Observant Systems: Overnight Sensation

**Team:**

**Members:** David Zhang (xz2229, davidzhanggg), Ziqiao Gao (zg375)

**Project name:** Dream Machine

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
<img width="908" height="124" alt="image" src="https://github.com/user-attachments/assets/8bb43997-8724-4e2b-9c1b-9ee1a648505d" />


## Part B. 

***Include a short video or screenshots of your experiments with the person detection. Write down three situations where it did not see you, or saw a person who was not there, and what you think the cause was.***
<img width="640" height="480" alt="image" src="https://github.com/user-attachments/assets/2b4c936d-a18f-486b-a34d-5079c2278f5a" />

1. Low lighting: When I turned off the lights, YOLO sometimes failed to detect me. This was likely because the camera could not capture enough visual details for the model to recognize a person.

2. Partially outside the frame: When I moved toward the edge of the camera view, YOLO sometimes stopped detecting me even though part of my body was still visible. This may have happened because the model did not have enough information to identify a complete person.

3. Person in a photo: When I showed a photo of a person to the camera, YOLO detected the person in the photo as a real person. This is because YOLO recognizes visual patterns associated with people but cannot necessarily distinguish a real person from an image of one.


## Part C. 
### See more: hands and pose with MediaPipe

\*\*\***Include a screenshot or short video of the hand pose demo, and write how you might use face, hand or body pose tracking in your observant system.**\*\*\*

https://drive.google.com/file/d/1wnjsfQrUTy4oALpYatzacbZTKukACG33/view?usp=drivesdk

Hand and body pose tracking could help our observant system understand a user's activities without requiring verbal input. For example, the system could recognize a hand gesture to activate sleep mode and use body movement to detect changes in activity during the night. This could make the interaction more natural and hands-free.

## Part D. 
### Reason: run Qwen on the Pi with Ollama

\*\*\***Ask Qwen three questions to answer. Paste the questions, the answers and how long each took. Try one of them with `qwen3:0.6b` and compare.**\*\*\*

Test 1:

Question: Tell me a bit about the history of Roosevelt Island.

Model: qwen3.5:0.8b

Response:

Roosevelt Island is an island located on Manhattan, New York City, originally built as part of the Great Wall of Manhattan to protect the harbor from pirates and storms. It was first developed in 1857 by John Quincy Adams and later became a significant landmark for American immigration and political history during the late 19th century.

Response Time: 65.6 seconds

Test 2:

Question: Tell me a bit about the history of Roosevelt Island.

Model: qwen3:0.6b

Response:

Roosevelt Island, located in the United States, was established in the 19th century as a residential area for the Roosevelt family. It played a significant role in the development of New York City and became a hub for the American West. The island is known for its historic architecture and the Roosevelt family's influence on the region.

Response Time: 43.5 seconds

Test 3: 

Question: What is in this photo?

Image: snap.jpg

Model: qwen3.5:0.8b

Response:

This photo features a young Asian man with dark hair and glasses, wearing a blue shirt. He is looking directly at the camera with a slight smile. In the background, there are two white wall plates and a black water bottle on a table.

Response Time: 99.0 seconds

The smaller Qwen3:0.6b model responded faster (43.5 seconds) than Qwen3.5:0.8b (65.6 seconds) when answering the same  question. However, both models generated inaccurate historical information, showing that language models can produce confident but incorrect responses.

For the image understanding task, Qwen3.5:0.8b took 99.0 seconds and generated a detailed description of the photo. Compared with YOLO's object detection, Qwen provided a more descriptive natural-language response.

Overall, the experiments demonstrated the trade-offs between response speed, factual accuracy, and multimodal capabilities when running AI models locally on a Raspberry Pi.

## Part E. 
### Connect: from YOLO readings to Qwen reasoning

---

# Lab 5 Part 2: Overnight Sensation

## Part F. 
### Read Part 2 and storyboard your night-time interaction

\*\*\***Insert ideas, sketches, Verplank diagrams and storyboards for your night-time interaction here.**\*\*\*

We brainstormed several ideas, including:
- **Notification tracker**: The user places their phone in front of the camera before sleeping, and the device will monitor when the screen lights up overnight. It will try to count and categorize notifications by app (e.g., WeChat, Calendar, etc). In the morning, it gives a summary of the notifications received and how frequently the phone was activated.
- **Night digital processor**: The user uploads a folder of unsorted photos before going to bed. Overnight, YOLO analyzes the images and categorizes them based on detected objects, such as people, animals, food, or vehicles. In the morning, the user receives an organized photo collection and a summary of its contents.
- **AI Dream Machine**: Before bed, the user uploads photos from their day, then YOLO analyzes them overnight and identifies objects, while Qwen uses these observations to come up with a creative, dream-like story. In the morning, the device reveals and narrates the dream using text-to-speech.

We ended up choosing our third idea, AI Dream Machine, and this is our initial storyboard:
<img width="3769" height="1279" alt="image" src="https://github.com/user-attachments/assets/ee87f53f-2861-4c1c-9180-23775d2a0121" />
<img width="1600" height="903" alt="image" src="https://github.com/user-attachments/assets/34b8728e-7c0b-4f9d-9019-3cceb28ace4c" />


## Prep for Part 2

1. Look at and give feedback on the Part F storyboards.
   **Put the feedback for your ideas here.**
2. [Update your Lab Hub](prep.md#get-the-latest-content) to get the latest content for Part 2.
3. Decide where the device will spend the night and who else lives there. Get their OK before the first run.
4. Revise your storyboard with the feedback and with what you learned in Part E about where the pipeline breaks.

\*\*\***Post your revised storyboard here.**\*\*\*

Some of the feedback we received was that it was not clear how the user would provide the Raspberry Pi with photos or what the morning interaction would look like. It was also unclear how the user would know when the device had started processing, so we were encouraged to add a physical button and clearer feedback to make the interaction more intuitive. There were also concerns about the privacy of the uploaded photos.

From Part E, we learned about several technical limitations of our system. YOLO can detect people and objects, but it cannot fully understand the context or meaning behind a photo. It can also miss or incorrectly identify objects, meaning the generated dream might not accurately reflect the uploaded images. Additionally, Qwen cannot see the images directly and relies entirely on the textual descriptions produced by the interpreter. We also noticed that Qwen takes a considerable amount of time to generate a story on the Raspberry Pi.

Based on this feedback and our observations, we decided to improve our design by:

1. Moving dream generation overnight, so the user doesn't have to wait for Qwen and Piper in the morning.
2. Using a single physical button to start the process before bed and reveal the dream in the morning.
3. Providing clear screen and voice feedback so users know when processing has started and when their dream is ready.
4. Improving the interpreter to include more useful details from YOLO detections, helping Qwen generate more meaningful stories.
5. Keeping all processing local on the Raspberry Pi to protect the privacy of the user's photos.


Our improved storyboard taking into account the feedback can be seen below:
<img width="2276" height="1280" alt="image" src="https://github.com/user-attachments/assets/423454ba-0967-4e4d-af2d-2fcd547f54cd" />


## Part G. 
### Design the interaction before

\*\*\***Describe the interaction before.**\*\*\*


Before going to bed, the user uploads 50 photos of their week  into a designated folder on the Raspberry Pi. Once the photos are ready, they press a physical button to activate the AI Dream Machine.

The device acknowledges the hand-off with a short audio message: “Good night! I'll dream about your week.”

The Raspberry Pi then begins processing the photos in the background using YOLO and Qwen. The user does not need to interact with the device again until the next morning.

The entire hand-off takes less than 30 seconds, assuming the photos have already been transferred.


## Part H. 
### Incorporate the observant system

\*\*\***Screenshots or videos of the running system.**\*\*\*

<img width="1856" height="607" alt="image" src="https://github.com/user-attachments/assets/6529a3cb-1f41-4879-9f5c-c31da49157b0" />
<img width="872" height="340" alt="image" src="https://github.com/user-attachments/assets/01c32333-a6f7-47e5-b37a-3775ec9fc8a0" />
<img width="1600" height="1120" alt="image" src="https://github.com/user-attachments/assets/7e22434a-4b4a-4f7b-8806-685393e00cd8" />


## Part I. 
### Design the interaction after

For our AI Dream Machine, we wanted the morning interaction to be simple and enjoyable, without requiring the user to wait for the AI to generate the dream. After processing the uploaded photos overnight, YOLO saves the detected objects into a log. Qwen then uses these observations to generate a short, creative dream story, and Piper converts it into audio. Both the story and narration are saved locally on the Raspberry Pi. In the morning, the user presses again the button to reveal their dream. The device plays the saved dream through a speaker, allowing the user to listen to it without having to read anything or interact with a computer.

We also considered situations where no objects were detected or no photos were uploaded. In these cases, the device informs the user rather than generate a dream that appears to be based on observations that were never made.


## Final documentation

Throughout the development of our AI Dream Machine, we made several improvements based on feedback and testing. Initially, Qwen generated the dream after the user pressed the button in the morning, but this took considerable time, so we moved the entire process overnight, so the dream and its narration are ready when the user wakes up. We also added visual feedback to the Pi screen to make the interaction clearer.

Looks like:


The device sits on a desk next to the user's bed, with a physical button, a Mini PiTFT screen, and a speaker. The screen displays different icons and messages depending on the current state.

Works like:


After the user uploads their photos and presses the button, YOLO detects objects, the interpreter converts them into text descriptions, and the observations are saved in a log. Qwen then generates a creative dream, and Piper converts it into audio. Everything is processed locally while the user sleeps. The code files are the following: dream_display.py, dream_machine.py, dream_morning.py, dream_overnight.py.
<img width="1200" height="1600" alt="image" src="https://github.com/user-attachments/assets/0fce93f4-b862-496a-86fd-61dee14ccbdc" />
<img width="1200" height="1600" alt="image" src="https://github.com/user-attachments/assets/e0c277c5-46fa-424f-acac-53ccadd51e7b" />

Acts Like:


Before bed, the user uploads their photos and presses the button to start the process. The screen confirms that the device is working. In the morning, the user presses the same button to immediately hear their personalized dream, starting with a greeting and the dream's title. They can press it again to replay the narration.

A demo video of our AI Dream Machine can be seen here:
https://drive.google.com/file/d/1R7dZj2wLami1X_ppWY9Ht1EsQm6G5xZF/view?usp=sharing



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
