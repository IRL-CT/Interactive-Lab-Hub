# Chatterboxes

**Rawisara Chairat, Lamiah Khan, Xiaoxi Xu, Afroza Aktar**

[![Watch the video](https://user-images.githubusercontent.com/1128669/135009222-111fe522-e6ba-46ad-b6dc-d1633d21129c.png)](https://www.youtube.com/embed/Q8FWzLMobx0?start=19)

In this lab, we want you to design interaction with a speech-enabled device — something that listens and talks to you. This device can do anything *but* control lights (since we already did that in Lab 1). First, we want you to storyboard what you imagine the conversational interaction to be like. Then you will use wizarding techniques to elicit examples of what people might say, ask, or respond. We then want you to use the examples collected from at least two other people to inform the redesign of the device.

We will focus on **audio** as the main modality for interaction to start; these general techniques can be extended to **video**, **haptics** or other interactive mechanisms in the second part of the Lab.

A note on what you are building with. Speech interfaces are usually taught as two boxes — speech-in, speech-out — and that framing hides the part that actually determines whether an interaction works. Between listening and speaking sits the question of **whose turn it is**: when does the device decide you have finished talking, and how long does it make you wait before it answers? This lab gives you direct control over both, and we will ask you to notice what changes when you move them.

## Prep for Part 1: Get the Latest Content and Pick up Additional Parts

### Pick up Web Camera If You Don't Have One

### Get the Latest Content

As always, pull updates from the class Interactive-Lab-Hub to both your Pi and your own GitHub repo.

**\[recommended\]** Option 1: On the Pi, `cd` to your `Interactive-Lab-Hub`, pull the updates from upstream (class lab-hub) and push the updates back to your own GitHub repo. You will need the *personal access token* for this.

# Part 1

## A. Text to Speech
### The classic engines
### Neural TTS with Piper



\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
(This shell file should be saved to your own repo for this lab.)

We wrote our own shell file and uploaded it in "Part 1(A)". 

\*\***Then answer: Is the same greeting, in these different voices, the same greeting? Describe one concrete way the voice changed what the utterance seemed to mean or who seemed to be speaking.**\*\*

We preferred Piper because it sounded like a friendly assistant. The greeting felt warm and personal. Its smoother rhythm and more natural pauses made “Hello Afroza, KM, CICI, Lamiah” sound like someone welcoming us.

eSpeak sounded more like a machine, so the same greeting felt more like an automatic announcement. Festival sounded somewhat more human, but the rhythm felt less smooth than Piper.

Even though the words were the same, the greeting did not feel the same. The voice changed who seemed to be speaking and how welcoming the message felt.

## B. Speech to Text

\*\***Record a few seconds of your own speech (`arecord -d 5 -f cd -c 1 -r 16000 test.wav`) and transcribe it with at least two model sizes. Report the real-time factor for each. At what point does the accuracy improvement stop being worth the delay, for a system that has to answer you?**\*\*

Answer: We tested the same five-second recording using tiny.en, base.en, and small.en. Their real-time factors were 0.20, 0.42, and 1.04, respectively.

All three models returned the digit sequence 01234. The base model added hyphens between the digits, but the numbers remained the same. Tiny took 0.99 seconds, base took 2.12 seconds, and small took 5.19 seconds.

For this recording, increasing the model size did not improve the digit sequence, so the additional delay was not worthwhile. We would choose tiny.en for this interaction because it gave the same digits with the shortest waiting time. More varied recordings would be needed to see whether larger models perform better on difficult speech.

\*\***Write your own script that verbally asks for a numerical input (a phone number, zipcode, number of pets) and records the answer the respondent provides.**\*\* 

Answer: We created `speech-scripts/ask_number.sh`. The script uses Piper to ask the respondent for a five-digit ZIP code, records the answer through the USB microphone, and transcribes the recording with faster-whisper.

We tested the spoken sequence “one one two one eight.” The microphone was the USB PnP Sound Device on capture card 3. I compared tiny.en, base.en, and small.en using the same recording. The models sometimes displayed the digits as a continuous number, separated digits, or digits separated by hyphens. I compared the real-time factor and whether each model preserved all five digits, including the leading one.

The main challenge was that digit strings can be formatted differently even when the recognized digits are correct. For an interactive system, I would repeat the recognized number back to the user and ask for confirmation before accepting it. All the file regarding part B is uploaded in "Part 1 (B)" folder. 

## C. Turn-taking: knowing when someone has stopped talking

\*\***Try both extremes, and something in between. Describe what each one feels like to talk to. Note specifically: at 0.2s, what kinds of normal speech get cut off? At 1.5s, what does the delay make the system seem like?**\*\*

<img width="810" height="287" alt="Screenshot (33)" src="https://github.com/user-attachments/assets/955858f1-e66f-4131-8692-fa248e6acd9b" />


<img width="1028" height="195" alt="Screenshot (34)" src="https://github.com/user-attachments/assets/7c8b1e86-95e7-41ef-8c98-7e888c7ef3df" />


<img width="1165" height="190" alt="Screenshot (35)" src="https://github.com/user-attachments/assets/d3f9f2fc-3b33-4401-8eb6-8fb3bfc49281" />



Answer: At the 0.2-second threshold, the system responded quickly but often treated normal pauses, breathing, or thinking pauses as the end of my turn. It split my speech into short and sometimes incomplete phrases, so it felt impatient.
At the 1.5-second threshold, the system kept more of my sentence together and correctly recognized most of my speech. However, it waited longer before responding, which made it feel slow. The system transcribed my 6.2-second speech in 1.29 seconds.
The 0.2-second setting was faster but interruptive, while the 1.5-second setting was more patient but less responsive. A middle value, such as 0.8 seconds, would likely provide a better balance.

## D. Storyboard

\*\***Post your storyboard and diagram here.**\*\*
Our idea for a speech-enabled device is creating a bedside voice assistant that acts like a personal storyteller. The interaction is intentionally hands-free so the user can stay comfortable in bed, and hopefully if done well, can insure a good night's sleep for users of all ages. 
Verplank Diagram: 

<img width="737" height="488" alt="Screenshot 2026-09-24 at 9 05 19 PM" src="https://github.com/user-attachments/assets/23dfa129-887f-47bd-bce6-9907b0871850" />


Storyboard: 

<img width="538" height="487" alt="Screenshot 2026-09-24 at 8 58 56 PM" src="https://github.com/user-attachments/assets/fd41de42-fe6e-41a6-9f62-02a423116da4" />


Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses.
\*\***Please describe and document your process.**\*\*
To chart out how the dialogue should function, we first made a block diagram to showcase it: 

<img width="868" height="455" alt="Screenshot 2026-09-26 at 10 38 17 AM" src="https://github.com/user-attachments/assets/9be00845-1ce8-431c-9ada-d790861d03a9" />

Your script should include the pauses. Where does your device wait, and for how long? You now know from Part C that this is a parameter you have to choose, not something that happens for free. 

Our initial script: 
1. Starting the interaction
   
User: “I can’t sleep, please tell me a story.”

[Device waits 1 second]

Device: “Of course. What kind of story would you like to hear?”

[Device waits up to 4 seconds for a response]

3. Choosing a story
   
User: “Horror.”

[Device waits 1 second]

Device: “Alright then, here goes. In a faraway place, there was a haunted house…”

[Device continues speaking for a few seconds, then listens for interruptions.]

5. User may interrupt at any point of the story
   
User: “Wait, a haunted house or castle?”

[Device pauses (probably has a 1-2 second delay) the story and waits 1 second to make sure the user has finished speaking.]

Device: “It’s a haunted house, reader. And within the house, there was a spirit…”

[Device continues the story.]

The user can also interrupt with commands such as “pause,” “stop,” “continue,” or “change the story.” The device prioritizes the user's speech over the story whenever it detects an interruption.

7. Ending the story
   
[Story finishes]

[Device waits 2 seconds]

Device: “Hope that helped. Sweet dreams!”

[Device becomes idle/quiet and waits for the next interaction.]


## E. Acting out the dialogue


https://github.com/user-attachments/assets/0c0bc613-4ce0-4d80-bd9c-2192b5a68016


\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*


Acting out the dialogue showed us that timing and pauses were more important than we expected. We noticed that interruptions need to feel natural and the device should clearly switch between listening and speaking. Overall, the acting helped us focus not just on what the device says, but also when it listens and responds.

---

# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.

## Prep for Part 2 - BEDSY or BEDDY

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings.
There are two concrete things that could be improved:
a. Timing: 
- The 1s wait after the user speaks is probably too short. People who are sleepy pause and trail off mid-sentence. We'd use about 1.0s for one-word answers like "Horror" and about 1.5s for longer, open-ended speech like "I can't sleep, please…".
- The story should get a longer silence tolerance over time. If the user goes quiet, that's good, because they may be falling asleep. Silence shouldn't trigger a "Are you still there?" prompt.
  
b. Anticipating misunderstandings
- The interruption "Wait, a haunted house or castle?" is ambiguous. The device might treat it as a new genre request instead of a question about the current story. We'd have it answer briefly, then explicitly resume ("Shall I go on?").
- Mishearing is likely at night. People whisper, mumble, or speak into a pillow. If the device didn't catch the genre, it should ask once with options instead of guessing or restarting.
- We need a concrete way to interrupt the user, because often the voice it can be hearing could be its own audio, rather than the user's voice. 

2. What are other modes of interaction *beyond speech* that you might also use to clarify how to interact? In particular: how does someone know when the device is listening, and when it is thinking? You have a screen and an LED.
Speech-only interaction leaves the user guessing about the turn-taking state. The screen and LED can make the device's state visible at a glance, which matters in a dark room.
- Listening: Open, attentive "o" mouth, small eyes for the device's facial design.
- Thinking: Eyes closed, flat mouth
- Speaking: Round eyes, wavy/moving mouth
- Idle/asleep: Dimmed or off.

Moreover, some design choices we can make are keeping brightness low and colors warm. For example, bright blue light can work against sleep, so dimming the screen and LED, or turn them off once the user is likely asleep.

4. Make a new storyboard, diagram and/or script based on these reflections.
   <img width="737" height="488" alt="IMG_3766" src="https://github.com/user-attachments/assets/36d170a1-1d0e-45dd-9164-edb491e60ce6" />

   This is the refined story board, updated to include the joy stick & better engaging/natural facial expressions for the device.
   
6. (optional) Integrate [input devices](inputs.md) in the system
We will also be integrating Pushbutton to interrupt the device. 

## Project Description

I built a Raspberry Pi 5–based bedtime storyteller called **Bedsy**. The input and sensor devices are a USB PnP microphone, which detects the user’s speech, and a momentary pushbutton, which acts as an interruption sensor. The pushbutton is connected to GPIO21 using physical pin 40, with the other side connected to ground using physical pin 39. The output devices are a speaker and an Adafruit MiniTFT ST7789 display connected through SPI. The display shows an animated storyteller face and the current mode: `SPEAKING`, `LISTENING`, `THINKING`, or `STOPPED`.

When the program starts, Bedsy asks the user what type of story they want and then tells a fixed fictional horror story about four students working late at Cornell Tech. The story is divided into short sections so the user can interrupt it using the pushbutton sensor. When the button is pressed, the speaker stops and the system changes to listening mode. The USB microphone records the user’s question, and faster-whisper converts the speech into text. The question is shown in the laptop terminal, but the speaker does not repeat it.

The software uses Python, `gpiozero` for the pushbutton sensor, `arecord` for microphone recording, faster-whisper for speech-to-text, Piper for text-to-speech, `aplay` for speaker output, and the Adafruit ST7789 display library for the MiniTFT. The story and interruption responses are scripted, so this version does not use an LLM.

##**Video Link of BEDSY Story teller**

https://drive.google.com/file/d/1hKX2aMVuZPkSjAYvGI4n_aD4sj7d0-eb/view?usp=sharing

## Test the system

Try to get at least two people to interact with your system. (Ideally, you would inform them that there is a wizard *after* the interaction, but we recognize that can be hard.)

Answer the following:

### What worked well about the system and what didn't?
\*\**your answer here*\*\*

### What worked well about the controller and what didn't?
\*\**your answer here*\*\* HAD TO PRESS THE PUSHBUTTON FEW TIMES TO MAKE IT WORK 

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
