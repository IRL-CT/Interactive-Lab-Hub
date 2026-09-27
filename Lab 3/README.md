# Chatterboxes

**NAMES OF COLLABORATORS HERE**

[![Watch the video](https://user-images.githubusercontent.com/1128669/135009222-111fe522-e6ba-46ad-b6dc-d1633d21129c.png)](https://www.youtube.com/embed/Q8FWzLMobx0?start=19)

---

# Part 1

## A. Text to Speech


### Neural TTS with Piper

\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
(This shell file should be saved to your own repo for this lab.)

my_greeting.sh

\*\***Then answer: Is the same greeting, in these different voices, the same greeting? Describe one concrete way the voice changed what the utterance seemed to mean or who seemed to be speaking.**\*\*

No, the same greeting felt different in different voices. I liked Piper the most because it sounded more natural and friendly. eSpeak sounded more robotic, so it felt more like a machine was talking to me, while Piper felt more like a real person.

## B. Speech to Text

\*\***Record a few seconds of your own speech (`arecord -d 5 -f cd -c 1 -r 16000 test.wav`) and transcribe it with at least two model sizes. Report the real-time factor for each. At what point does the accuracy improvement stop being worth the delay, for a system that has to answer you?**\*\*

I tested my recording with `tiny.en` and `base.en`. The real-time factor was 0.25x for `tiny.en` and 0.46x for `base.en`. In my test, `tiny.en` was actually more accurate, while `base.en` incorrectly transcribed “bye bye” as “I find you.” Since the larger model was slower without improving accuracy, I would choose `tiny.en` for a system that needs to respond quickly.

\*\***Write your own script that verbally asks for a numerical input (a phone number, zipcode, number of pets) and records the answer the respondent provides.**\*\* Numbers are a good stress test — transcription systems make characteristic errors on digit strings, and you will want to know what they are before you design around them.

I wrote a script that verbally asks, “How old are you?” and records the user’s response for 5 seconds. I answered “23,” and the speech recognition model correctly transcribed it as “23.” in the file number_question.py


## C. Turn-taking: knowing when someone has stopped talking

\*\***Try both extremes, and something in between. Describe what each one feels like to talk to. Note specifically: at 0.2s, what kinds of normal speech get cut off? At 1.5s, what does the delay make the system seem like?**\*\*

At 0.2s, the system was still usable for me. Some short pauses were cut off, but not every pause caused a problem. At 1.5s, the system felt noticeably slower because it waited too long after I finished speaking before responding. A middle value felt more natural because it allowed brief pauses without making the system seem unresponsive.

## D. Storyboard

Concept: Workout Check-in Device
I designed a simple voice-based workout check-in device. It asks the user whether they worked out that day, what body part they trained, and whether they did cardio. The goal is to make workout tracking quick and hands-free.

\*\***Post your storyboard and diagram here.**\*\*

<img width="4032" height="2268" alt="IMG_0476" src="https://github.com/user-attachments/assets/57e76daa-bf2d-4210-ba4c-2be682894488" />
Storyboard: The storyboard shows a short voice interaction where the device guides the user through a daily workout check-in. The user can complete the whole interaction through speech without using a screen.


However, after act it out, I realized that the conversation could not be completely linear because yes/no responses change what the device should ask next. I therefore draw another branching dialogue to show the different options might occur. 

<img width="2268" height="4032" alt="IMG_0477" src="https://github.com/user-attachments/assets/6bf5ef5b-6527-41fd-805f-2124e2aa4ec4" />


\*\***Please describe and document your process.**\*\*


First try dialogue script:


Device: “Did you work out today?”
Wait for user response. After the user stops speaking, wait 0.7 seconds before ending their turn.
User: “Yes.”
Wait 0.7 seconds.
Device: “What did you train?”
User: “Legs.”
Wait 0.7 seconds.
Device: “Did you do cardio too?”
User: “Yes.”
Wait 0.7 seconds.
Device: “Great job. Workout complete!”


Improved/final version of the dialogue:


Device: “Did you work out today?”
Wait for response; end turn after 0.7s of silence.  
If YES:
Device: “What did you train?”
User: “Legs.”
Wait 0.7s.
Device: “Did you do cardio too?”  
→ If YES: “Great job! Workout complete.”
→ If NO: “Got it! Workout complete.”  
If NO to the first question:
Device: “No worries. See you tomorrow!”


I first wrote a simple linear conversation with three questions: whether the user worked out, what they trained, and whether they did cardio. While making the storyboard and act it out, I realized that the conversation should change depending on the user’s yes/no responses. For example, if the user says “no” to the first question, the device should not continue asking what they trained. I therefore added branches for different responses. I also used what I learned from Part C to design the timing. Since 0.2 seconds sometimes cut me off and 1.5 seconds felt too slow, I chose about 0.7 seconds of silence before the device considers the user’s turn finished.

## E. Acting out the dialogue

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing. Please record this interaction (for example, using Zoom's record feature).

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*

While developing the dialogue, I realized that the conversation could not be completely linear because yes/no responses change what the device should ask next. I therefore used a branching dialogue flow and used the storyboard to show one common path through the interaction.

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
