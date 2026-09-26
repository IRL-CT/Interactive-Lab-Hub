# Chatterboxes

## A. Text to Speech

Link to shell file: https://github.com/chonjessica23/Interactive-Lab-Hub/blob/Fall2026/Lab%203/speech-scripts/hijessica.sh 

\*\***Then answer: Is the same greeting, in these different voices, the same greeting? Describe one concrete way the voice changed what the utterance seemed to mean or who seemed to be speaking.**\*\*

I would say yes, the greeting is the same despite the voices changes. I noticed that when I went from US to Scottish English, the only changes were a very subtle difference in how and how long vowels were pronounced. 


## B. Speech to Text

\*\***Record a few seconds of your own speech (`arecord -d 5 -f cd -c 1 -r 16000 test.wav`) and transcribe it with at least two model sizes. Report the real-time factor for each. At what point does the accuracy improvement stop being worth the delay, for a system that has to answer you?**\*\*

The base.en model had a real-time factor of 0.43x, while the small.en model had a real-time factor of 1.24x.  During this test, I found that base.en was faster but made a small transcription error, while small.en was more accurate but slower. My recorded phrase was "Hello, it's the weekend and I'm currently testing this." The small.en model was able to accurately transcribe fully, while base.en transcribed "weekend" as “week and.” However, small.en took longer than the five-second recording itself to transcribe. While I'd prefer accuracy for this example, I'd imagine the extra time for processing would be a significant downside for much longer speeches since responsivity is, I'd argue, most important. 

\*\***Write your own script that verbally asks for a numerical input (a phone number, zipcode, number of pets) and records the answer the respondent provides.**\*\* Numbers are a good stress test — transcription systems make characteristic errors on digit strings, and you will want to know what they are before you design around them.

Link to file: https://github.com/chonjessica23/Interactive-Lab-Hub/blob/Fall2026/Lab%203/speech-scripts/askforzip.sh 

## C. Turn-taking: knowing when someone has stopped talking

\*\***Try both extremes, and something in between. Describe what each one feels like to talk to. Note specifically: at 0.2s, what kinds of normal speech get cut off? At 1.5s, what does the delay make the system seem like?**\*\* There is no correct value. A system that takes drink orders and a system that listens to someone think out loud want very different thresholds, and the right one depends on what your users are doing with their pauses.

I noticed that for the 0.2-second session, the beginning of my sentences were getting cut off more often, especially when I paused briefly before continuing. For the 1.5 seconds, I felt slightly frustrated because I had to wait longer before the system moved on to my next sentence, which made the interaction feel slower.

## D. Storyboard

**Fortune Telling Device**

<img width="281" height="224" alt="Screenshot 2026-09-26 at 3 23 28 PM" src="https://github.com/user-attachments/assets/a2e973e9-5d93-4bd4-9784-7bf1948d8159" />

I took inspiration from both fortune cookies and paper fortune tellers (picture above) for this project. While brainstorming, I wanted to utilize the echo_bot.py but wanted a more back-and-forth interaction than having the device simply repeat what users said. I also wanted the interactions to feel somewhat natural adn not obvious what I'd program was preprogrammed responses. I then thought fortune telling would offer more controlled/workable responses, but be able to feel organic enough where it didn't feel overtly structured. Below is the speech flow I anticipate: 

<img width="506" height="683" alt="Screenshot 2026-09-26 at 3 24 31 PM" src="https://github.com/user-attachments/assets/9d9805ad-095e-4414-81bb-3a2700f78e77" />

After coming up with the dialogue, I went to storyboards, and found I needed to consider how to prompt the conversation since the program can't be running continuously. So, I added a button to start the experience and also see if I could experiment working with buttons. I didn't want everything to be purely verbal since part of the fun in doing paper fortune telling is picking out the numbers yourself. So, I think I'll incorporate the Adafruit MPR121 12-Key Capacitive Touch Sensor. Below are the storyboards.  

<img width="460" height="634" alt="Screenshot 2026-09-26 at 3 24 46 PM" src="https://github.com/user-attachments/assets/c94c5868-dd7f-4d05-8f11-7925cbd5f19a" />

<img width="461" height="305" alt="Screenshot 2026-09-26 at 3 25 44 PM" src="https://github.com/user-attachments/assets/2508d89d-f349-4010-811a-554e65b8d5fa" />

Since the dialogue will be semi-structured, I anticipate the pauses won't be too long nor take too long because it'll be mostly one word/very short sentences. So when I get to coding, I'll probably have to make the program anticipate brief silences and responses.

## E. Acting out the dialogue

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing. Please record this interaction (for example, using Zoom's record feature).

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*


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
