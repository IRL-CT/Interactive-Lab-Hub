# Chatterboxes
**Charlotte Lin (hl2575), Zoe Tseng (yzt2), Le-En Huang (lh764)**
**Use of AI for this lab: Claude Sonnet4 for image creation and debugging instructions for the code.**

[![Watch the video](https://user-images.githubusercontent.com/1128669/135009222-111fe522-e6ba-46ad-b6dc-d1633d21129c.png)](https://www.youtube.com/embed/Q8FWzLMobx0?start=19)

In this lab, we want you to design interaction with a speech-enabled device--something that listens and talks to you. This device can do anything *but* control lights (since we already did that in Lab 1).  First, we want you first to storyboard what you imagine the conversational interaction to be like. Then, you will use wizarding techniques to elicit examples of what people might say, ask, or respond.  We then want you to use the examples collected from at least two other people to inform the redesign of the device.

We will focus on **audio** as the main modality for interaction to start; these general techniques can be extended to **video**, **haptics** or other interactive mechanisms in the second part of the Lab.


### Text to Speech 

\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
(This shell file should be saved to your own repo for this lab.)

Run the following command to try this out - 
```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 3/speech-scripts $ ./greeting.sh 
```


### Speech to Text

\*\***Write your own shell file that verbally asks for a numerical based input (such as a phone number, zipcode, number of pets, etc) and records the answer the respondent provides.**\*\*

Run the following command to try this out - 
```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 3/speech-scripts $ ./inquiry.sh 
```

### 🤖 NEW: AI-Powered Conversations with Ollama

Want to add intelligent conversation capabilities to your voice projects? **Ollama** lets you run AI models locally on your Raspberry Pi for sophisticated dialogue without requiring internet connectivity!

\*\***Try creating a simple voice interaction that combines speech recognition, Ollama processing, and text-to-speech output. Document what you built and how users responded to it.**\*\*

#### Idea Box
I created a working prototype for Idea Box, an interactive voice assistant that uses AI to provide creative suggestions for ongoing party games.
It collects user input and guides users with creative suggestions that could make the party games more fun!

#### Features 
- Game Identification: Asks what game you're playing
- Punishment Suggestions: AI generates creative, fun consequences for losing teams
- Creative Enhancement: Provides themes, rule variations, and other game improvements
- Audio-Optimized: All AI responses designed for natural speech output
- Fallback Mode: Works without microphone using text simulation

#### How to run
Restart ollama so that the AI response would not time out.
```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 3 $ sudo systemctl restart ollama
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 3 $ ./run_party_game_assistant.sh 
```

Delete `/audio` files to save memory.

#### User feedback


### Storyboard

Storyboard and/or use a Verplank diagram to design a speech-enabled device. (Stuck? Make a device that talks for dogs. If that is too stupid, find an application that is better than that.) 

\*\***Post your storyboard and diagram here.**\*\*

<img src="interaction/storyboard/userflow.png" alt="frame 1" width="1200"/>

<img src="interaction/storyboard/ideabox.png" alt="frame 1" width="1200"/>

Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses. 

\*\***Please describe and document your process.**\*\*

I first used a user journey map to frame how I want my user journey to look like for a game night.
In the journey map, I used the following as the 4 aspects that I am designing for.
- users
- emotions
- dialogue
- goals

<img src="interaction/storyboard/userjourney.png" alt="frame 1" width="1200"/>

I then selected two scenarios that I want to create an interactive script for:
- creative facilitating mode
- ice breaker mode

[link to script](https://docs.google.com/document/d/1b2uQgRdphgMJYWD2WIDDTRGQw4Y3QLTUAXepUIx83Fg/edit?usp=sharing)


### Acting out the dialogue

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing.  Please record this interaction (for example, using Zoom's record feature).

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*

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

*Include videos or screencaptures of both the system and the controller.*

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






