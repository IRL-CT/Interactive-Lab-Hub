# Chatterboxes

**COLLABORATORS: Neeha Ravula (nr485), Gaurav Patel (gp438), Nishant Ray (nr487), Ammar Syed (as4422)**

---

# Part 1

## Setup

 > Successfully set up the following:
> - classic speech synthesizers
> - voice activity detection model
> - neural voice and speech recognition models
> - microphone and speaker

## A. Text to Speech

> We played around with all of the the different models and demos, including espeak, festival, and neural TTS with piper. It was very cool to see the differences in tone between each model, but we liked the piper one the most because it seemed the most human-like. We wrote a **text_to_speech.sh** script (under speech-scripts/) which successfully greeted our teammate, Gaurav, utilizing the piper model.

**Is the same greeting, in these different voices, the same greeting? Describe one concrete way the voice changed what the utterance seemed to mean or who seemed to be speaking.**
> When testing the models, we found that the greeting was NOT the same across all the different voices. For example, the espeak model renders the greeting with a very flat, almost mechanical-sounding tone, with very little variation in pitch. On the other hand, piper's neural voice adds natural inflections in tone including a rise towards the end of "How are you doing?" to indicate a question is being asked. The use of these natural inflections makes Piper the more "human-like" speech model.


## B. Speech to Text

**Whisper Models**

> We tested various models of OpenAI's [faster-whisper](https://github.com/SYSTRAN/faster-whisper), including `tiny.en`, `base.en`, `small.en`, `medium.en`.

> We recorded a few seconds of speech in speech-scripts/test.wav, and observed the following real-time factors across the following models:
> - tiny.en: real-time factor of 0.25x
> - base.en, real-time factor was 0.42x

**Record a few seconds of your own speech (arecord -d 5 -f cd -c 1 -r 16000 test.wav) and transcribe it with at least two model sizes. Report the real-time factor for each. At what point does the accuracy improvement stop being worth the delay, for a system that has to answer you?**
> We noticed the accuracy improvement stops being worth the delay when a larger model makes the conversation noticeably slower without meaningfully reducing transcription errors. base.en took 0.86 seconds longer than tiny.en but produced essentially the same words, so tiny.en offers the better trade-off for that recording. If it frequently misunderstands requests, a slower, more accurate model could be worth it. From these numbers, it seems that a model with a real-time factor greater than 1.0 would not be worth it as well.

**Speech to Text Experiment**

> We wrote a speech_to_text.sh script (under speech-scripts/) using the piper speech model and the faster-whisper transcription, which asks the user for their zip code, waits a specified duration for input (default of 5 seconds), and prints out what was transcribed in the terminal output.


## C. Turn-taking: knowing when someone has stopped talking

> We tested various extremes of the **voice activity detector** (VAD).

**Try both extremes, and something in between. Describe what each one feels like to talk to. Note specifically: at 0.2s, what kinds of normal speech get cut off? At 1.5s, what does the delay make the system seem like?**
> At 0.2 seconds, the system cut my voice short. I said "I'd like a coffee um with oat milk and acutally to make it a large" but it only captured "with oat milk and actually make it a large." Pauses and filler words were treated as the end of my turn. At 1.5s it captured the entire sentence but I had to wait for a bit in silence afterwards. The 1.5s made be a bit unsure on whether I was done or what the status was. In between at 0.6 seconds it caught my sentence and replied much quicker.


## D. Storyboard

> ![alt text](image.png)

> We chose a speech-enabled vending machine because it provides a simple, familiar interaction that can be completed through a short conversation. We started with the successful path: the machine asks what snack the user wants, the user chooses, and the machine confirms before announcing that the snack is ready. We then considered alternative responses, including an unavailable snack, an incorrect selection, and silence. These became branches in the diagram, allowing the machine to repeat the available options, accept a correction, or cancel the interaction. We chose a five-second listening window for selecting a snack and a three-second window for confirmation because choosing a snack may take longer than answering yes or no. We also simplified the system by making the snacks free and not having any payment, allowing us to focus on asking for a snack, recognizing the response, and confirming the selection.

## E. Acting out the dialogue

[Link to dialogue recording](https://drive.google.com/file/d/1If0gT5JYrgCUZfPp079eUhKI9P43WqOS/view?usp=sharing)

> The dialogue felt less natural when acted out than we had imagined. Our partner first asked what the options were, which showed that the machine should list the snacks in its opening question. They also said "Oh, okay how about cookies" instead of simply "Cookies." Repeating the options after that felt awkward because their choice was already clear. The fixed listening windows also created pauses even when my partner answered immediately. However, the confirmation step worked well when they changed their mind about chips, and asking whether they wanted another order made it easy to continue. We would improve the interaction by listing the options upfront, accepting more natural phrases, and responding sooner when the user finishes speaking if possible.

> Feedback from other groups:
> - **[Group 1](https://github.com/9JAyemi/Interactive-Lab-Hub/tree/Fall2026/Lab%203):** I like the overall idea for this project and I think the interface is cool. One piece of advice I would say is maybe have the machine not reply too fast in order to process the language of the chosen snack correctly.
> - **[Group 2](https://github.com/Morinzzz/Interactive-Lab-Hub/tree/Fall2026/Lab%203):** I really like the idea of vending machine and the states of the machine. I think the states you came up with covered every scenario possible. Maybe the machine can just ask for the snack, no need for welcome message, or maybe indicate how long the welcome message will last.
> - **[Group 3](https://github.com/LaboriouslyExquisite/Interactive-Lab-Hub/tree/Fall2026):** Your idea is very devious! Only letting me have 5 seconds to choose what I want to order is so short! The idea of using voice to order a snack from a vending machine seems super fun though, and perhaps will influence me to buy something without thinking through fully whether or not I actually need a snack. It might fun to have people perhaps maybe dictate how long the system listen for by using a button rather than just a preset 5 seconds. Otherwise, I really like the idea of it checking with me before it actually give me a snack by responding with "You chose X. Is that correct?". Overall very fun project and it would be cool to see it working in real life!

---

# Lab 3 Part 2

## Prep for Part 2

**1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings.**

> From the dialogue we found a few issues. Options were hidden, the first thing the partner said was what are the options and the machine doesn't really answer that question. It's also annoying for the transcriptoin to match the exact wording of the item and rely on that to select the snack. Another thing is that listening windows are very fixed and some snacks have a longer name or the user might be thinking a lot.

**2. What are other modes of interaction *beyond speech* that you might also use to clarify how to interact? In particular: how does someone know when the device is listening, and when it is thinking? You have a screen and an LED.**

> We can use the joystick for browsing through the vending machine items. This addresses the what are the options questions as users can see and figure it out themselves. The screen can show the currently selected item/menu one by one. We can show on the LED the current state on whether the device is listening or speaking or dispensing.

**3. Make a new storyboard, diagram and/or script based on these reflections.**
> <img width="3028" height="2069" alt="image" src="https://github.com/user-attachments/assets/9d9c610f-0b79-42f9-a71d-5f585e51a4ea" />


## Prototype your system

[Here is the video of our system!](https://youtu.be/gHbyDP6Z504?si=-SviBDzsK90jyTxh)

<img width="1528" height="604" alt="Screenshot 2026-10-04 225459" src="https://github.com/user-attachments/assets/38053019-6308-4ec4-ac26-89823d3bbaf3" />

<img width="2880" height="1140" alt="Screenshot 2026-10-04 230450" src="https://github.com/user-attachments/assets/335e533d-cb11-44bb-a3e4-1d177942323b" />

For the system to work, press the top button to browse through snacks and the bottom button to select one. Wait for “LISTENING,” then say "yes" to confirm or "no" to return to browsing. Each snack costs $2. Choose "cash" or "card" when prompted. For card payment, say a made-up four-digit number, one digit at a time. Telling the machine 0000 or an invalid number returns you to selection. For cash, state your amount. Telling it an amount that is $2 or more is accepted, while insufficient funds returns you to selection. Successful payment plays a dispensing animation and spoken confirmation. All payments and dispensing are simulated. Repeat the process to order another snack!

## Test the system

### What worked well about the system and what didn't?
The system was very clear about what needed to be done and what needed to be said. There was some very nice interactions between exactly what a vending machine would require just inside voice format. The animations also looked really nice for giving the snacks to us. It was sometimes difficult to wait for the vending machine and so we would say something earlier and it wouldn't work and would have to go back and say it again. Also sometimes, there are some versions of yes or no that we would say that wouldn't register as yes or no which is an issue like I would or I wouldn't. We struggled to connect the joystick alongside the screen, so we switched to the Adafruit buttons. This simplified the setup, although cycling through snacks with one button was less flexible than directional navigation.

### What worked well about the controller and what didn't?
The wizard controller (the webpage UI above) provided buttons for common responses and a text field for custom speech, making it possible to guide the interaction manually. Showing the current state helped the operator follow the flow. However, payment answers had to be submitted during the listening stage, so the operator still needed to coordinate their actions carefully with the machine's prompts.

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?
A more autonomous version should preserve the wizard's ability to handle unexpected answers and clarify misunderstandings. Clear listening cues and enough time to respond are especially important when someone is saying several digits. Instead of immediately restarting after an invalid payment response, the system could explain what went wrong and let the user try again.

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?
We could collect timestamped prompts, user responses, button presses, wizard interventions, and transaction outcomes to identify common interaction patterns and failures. With participants' consent, audio recordings could reveal recognition errors and awkward pauses, while video could capture gestures, hesitation, and attention to the screen. Comparing wizard decisions with automated responses would help guide improvements.