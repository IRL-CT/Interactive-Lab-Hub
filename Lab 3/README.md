# Chatterboxes

**Yangchen Jin**

---

# Part 1

## A. Text to Speech

\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*

I created [`greet_yangchen.sh`](speech-scripts/greet_yangchen.sh) to have the Pi greet me using Piper voice.

\*\***Then answer: Is the same greeting, in these different voices, the same greeting? Describe one concrete way the voice changed what the utterance seemed to mean or who seemed to be speaking.**\*\*

The words were the same, but the greeting did not feel the same. The eSpeak NG `en+f2` voice was less clear and sounded slightly tired or reluctant, which made the greeting feel almost forced. The Piper `en_US-lessac-medium` voice was clearer and more consistent, so it felt like a fully formed machine speaking to me rather than an uncertain person.

## B. Speech to Text

\*\***Record a few seconds of your own speech (`arecord -d 5 -f cd -c 1 -r 16000 test.wav`) and transcribe it with at least two model sizes. Report the real-time factor for each. At what point does the accuracy improvement stop being worth the delay, for a system that has to answer you?**\*\*

I recorded the seven-second audio file [`my_speech.wav`](speech-scripts/my_speech.wav) and used [`transcribe.py`](speech-scripts/transcribe.py) to transcribe the same recording with two Whisper model sizes.

| Model | Transcription | Audio Duration | Model Load | Transcription | Real-Time Factor |
|---|---|---:|---:|---:|---:|
| `tiny.en` | “Hi, my name is Yang Chen and I'm a student and co-ner attack.” | 7.00 s | 0.53 s | 1.18 s | 0.17x |
| `base.en` | “Hi, my name is Yang Chen and I'm a student in Corner Tech.” | 7.00 s | 0.65 s | 2.29 s | 0.33x |

The `base.en` model took 1.11 seconds longer and had about twice the real-time factor of `tiny.en`. However, its transcription of “Cornell Tech” as “Corner Tech” was much closer and easier to understand than “co-ner attack.” Both models were still faster than real time, so the accuracy improvement was worth the additional delay. Based on this test, I would stop at `base.en` for a conversational system because a larger model could introduce more waiting for a smaller improvement in accuracy.


\*\***Write your own script that verbally asks for a numerical input (a phone number, zipcode, number of pets) and records the answer the respondent provides.**\*\*

#### Numerical Input Test

I created [`ask_zipcode.sh`](speech-scripts/ask_zipcode.sh), which verbally asks:

> Please say your five-digit ZIP code after I finish speaking.

The script then records five seconds of audio and saves the response as [`zipcode_answer.wav`](speech-scripts/zipcode_answer.wav).

I intended to say the ZIP code `07306`, but I accidentally said `070306`. Whisper transcribed the six-digit number that I actually spoke. This was not a transcription error, but it revealed another problem: an accurate transcription can still contain invalid user input.

A more complete system should check the number of digits before accepting the answer. In this case, it could respond:

> I heard 070306. That is six digits. Please repeat your five-digit ZIP code.

## C. Turn-taking: knowing when someone has stopped talkin

#### Endpointing Test

| Silence Threshold | Experience |
|---|---|
| `0.2 s` | The system responded quickly, but it frequently ended the turn during normal pauses. Short breaths, filler words such as “uh,” and pauses between clauses caused one sentence to be divided into several fragments. For example, “And the team got a history for like, uh, 666 year” and “until now” were treated as separate turns. |
| `0.8 s` | This produced the most natural rhythm. It allowed short thinking pauses without interrupting me, while still responding soon after I finished. Some unusually long sentences were still transcribed imperfectly, but the interaction did not feel either rushed or unresponsive. |
| `1.5 s` | The system captured more complete utterances, but the silence after speaking felt noticeably long. Combined with approximately 1.1 seconds of transcription time, the total wait was around 2.6 seconds. This made the system seem slow and uncertain, as if it had not heard me or did not know that I had finished. |

I selected `0.8 seconds` as the best compromise. It gives users enough room for ordinary pauses and brief moments of thought without making the system feel unresponsive.

## D. Storyboard

## SATOR SQUARE Storyboard

*Speak now. Hear yourself later.*

<img width="428" height="348" alt="393e4957a9f310c57f0d86d54e2ca6f5" src="https://github.com/user-attachments/assets/87b9518e-0406-4f91-b689-022bdbb97bc6" />

*A voice interface that allows users to speak with a simulated future version of themselves and leave messages that return at a later point in time.*

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/f974ae2e-d20f-41c4-87da-39649dc14f90" />

**SATOR SQUARE:** Select a return point: tomorrow, one month, or one year.

**User:** One month.

**SATOR SQUARE:** Temporal channel open. This is a simulated connection to yourself one month from now. Tell me about a decision you have not been able to make.

**User:** I am unsure whether I should commit to something that may not succeed.

*After the user stops speaking, the device waits for 0.8 seconds of silence before ending the turn.*

**SATOR SQUARE:** I heard that you are deciding whether to commit to something that may not succeed. Is that correct?

*The device waits for the user’s confirmation. If the user remains silent for five seconds, it says, “Take your time. The line is still open.”*

**User:** Yes.

*The Wizard listens to the dilemma and selects one appropriate reflection card.*

**Simulated Future Self:** I cannot tell you what happened. What would you regret not doing?

**User:** I would regret never finding out what I was capable of.

*After the user stops speaking, the device waits for 0.8 seconds of silence before sealing the answer.*

**SATOR SQUARE:** Your answer has been sealed. Return date: October 27, 2026. You will hear your own voice again in one month. Connection closed.

### Alternative Response Cards

- **Regret:** What would you regret not doing?
- **Fear:** Are you choosing this because you want it, or because you fear the alternative?
- **Control:** Which part of this decision is still under your control?
- **Identity:** Which choice is closer to the person you want to become?
- **Time:** Will this still matter to you one year from now?


## E. Acting out the dialogue

https://youtu.be/3asdAFzKRhc

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*

When I acted out the interaction, the opening instructions felt clear and natural. The problem appeared when SATOR SQUARE asked the user a reflective question. The question was broad and slightly abstract, so the participant was not sure how to respond. This showed me two possible directions: the question should either be simpler and more universal, or more personalized based on what the user has just said. I also started to question what the returned message means after one month. During the first interaction, the question already creates a useful moment of reflection. However, simply replaying the recording one month later may feel like only a time capsule. To give the return more meaning, the device could ask the user to compare their past concern with how they feel now, turning the message into evidence of change rather than just an old recording.


---

# Lab 3 Part 2

### Design Changes for Part 2

Feedback from Part 1 showed that the original future-self question was
too broad, and participants were sometimes unsure how to respond. The
revised system uses the speech transcript to select a question from a
small set of reflection cards. This keeps the questions open-ended while
making them more relevant to what the participant said.

The interaction was also changed from silence-based endpointing to
push-to-talk. The participant holds the green button while speaking and
releases it to finish, removing uncertainty about when the device stops
listening.

The screen and illuminated button communicate the system state. A dim
green light means the device is ready, a bright green light means it is
recording, and the light turns off while the system is processing. The
screen displays states including LISTENING, QUESTION RECEIVED, FUTURE
SELF CONNECTED, and MESSAGE SEALED.

The rotary encoder is used to select tomorrow, one month, or one year.
Pressing the encoder confirms the return point, and the illuminated
button controls both spoken responses.

---
### Redraft Interaction Dialogue

**Screen:** `A DECISION YOU KEEP AVOIDING?`

**SATOR SQUARE:** Think of one decision you keep avoiding. Choose when you want this message to return: tomorrow, one month, or one year.

*The user rotates the dial to select `ONE MONTH` and presses it to confirm.*

**SATOR SQUARE:** One month selected. Hold the green button and tell me what you are deciding—and what makes the decision difficult. Release the green button when you are finished.

**Screen:** `LISTENING...`  
*The green button remains fully illuminated while it is held.*

**User:** I am thinking about [decision], but I am worried about [concern].

*The user releases the green button.*

**Screen:** `QUESTION RECEIVED`  
*The green LED turns off while the automatic controller transcribes the recording and selects a relevant question.*

**Screen:** `FUTURE SELF CONNECTED`

**Future Self:** I cannot tell you what happened. [Selected reflection question]

**SATOR SQUARE:** Hold the green button to answer. Release it when you are finished.

**Screen:** `LISTENING...`

**User:** I think I am avoiding it because [answer].

*The user releases the green button.*

**Screen:** `MESSAGE SEALED`

**SATOR SQUARE:** Your answer has been sealed. It will return in one month. Connection closed.

---

### One Month Later

*The `TENET` row begins flashing.*

**Screen:** `MESSAGE RETURNED`

**SATOR SQUARE:** A message has returned. One month ago, you said:

*The device plays the user's original recording. It waits one second after the recording ends.*

**SATOR SQUARE:** That was you one month ago. What has changed?

**SATOR SQUARE:** Hold the green button to answer. Release it when you are finished.

**Screen:** `LISTENING...`

**User:** Since then, [new reflection].

*The user releases the green button.*

**Screen:** `MESSAGE SEALED`

**SATOR SQUARE:** Your new reflection has been sealed. Connection closed.

---

### Recovery Dialogue

*If the speech is missing or unclear:*

**SATOR SQUARE:** I may have missed that. Hold the green button and try again.

## Prototype

<img width="428" height="571" alt="2ad1e873b98163f0e95bd4a57de1b5d6" src="https://github.com/user-attachments/assets/76283920-9d14-46b1-926e-9add34d5af3a" />

**System:** Physical interaction with the screen, rotary encoder, illuminated button, microphone, and speaker.

<img width="1360" height="823" alt="image" src="https://github.com/user-attachments/assets/10a50f00-bbe3-4afe-a7a5-9db417ba0350" />

**Controller:** Terminal view showing transcription and question-card selection.

[Test Video](https://github.com/user-attachments/assets/e79375cc-f55c-4ff1-a955-85bd6f6f5a71)

YouTube Video: [Full Interaction Process](https://youtube.com/shorts/aM9rMaL1U2Q)

- [SATOR SQUARE Part 2 prototype](speech-scripts/sator_prototype_v2.py)
- [Automatic question controller](speech-scripts/wizard_controller.py)

SATOR SQUARE runs on a Raspberry Pi 5. A rotary encoder allows the
participant to select tomorrow, one month, or one year as the return
point. Pressing the encoder confirms the selection. The participant
then holds an illuminated green button while speaking and releases it
to finish recording.

A Mini PiTFT communicates the current state of the interaction,
including LISTENING, QUESTION RECEIVED, FUTURE SELF CONNECTED, and
MESSAGE SEALED. The green button remains dim when the system is ready,


becomes fully illuminated while recording, turns off while processing,
and flashes twice when the message has been sealed.

The Raspberry Pi records the participant through a USB microphone and
uses a local Whisper model to transcribe the recording. A keyword-guided
controller selects a reflection question from a set of question cards,
and Piper reads the question aloud through the speaker. The original
recordings, transcripts, selected questions, return point, and timestamps
are saved together as one session.

The controller view runs in the terminal and displays the selected
return point, user transcript, drawn question card, and the question
sent to the device. An earlier Wizard of Oz version allowed the wizard
to approve or replace the question; the revised prototype performs this
step automatically.




## Test the system

**Participant 1: Zining Yu**

**Participant 2: Junzhe Sun**

### What worked well about the system and what didn't?
The overall interaction flow worked well. The rotary encoder made the return-point selection physical, and holding the green button to speak was clearer than asking users to pause for a fixed amount of time. The screen and illuminated button also helped communicate when the system was ready, listening, processing, and finished. However, the screen was too small for some instructions, and the exposed components made the device look unfinished. The rotary shaft looked more like a screw than an intentional control. The tester suggested that the final device could resemble a compact MP4 player or iPod, integrating the screen, dial, button, microphone, and speaker into one portable enclosure. This familiar and personal form would fit an interaction based on private voice messages and memories. The current system also only supports English, which limits who can use it.

### What worked well about the controller and what didn't?
The controller successfully displayed the transcript, selected a reflection question, and recorded what was sent to the device. The automatic version allowed the interaction to continue without requiring me to type during the session. However, keyword matching and random selection from a small pool of questions did not always yield a relevant response. For example, when the topic was financial freedom, the system asked, “What are you protecting yourself from?” This made the controller feel as if it were randomly drawing from ten questions rather than understanding the participant. The earlier Wizard-of-Oz controller allowed me to replace an irrelevant question, but manually monitoring and typing could also create an awkward delay.

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?
The main lesson is that semantic relevance matters as much as timing. Even if the interaction runs smoothly, an unrelated question immediately makes the device feel less intelligent. A more autonomous version could use a constrained generative AI model to generate or rank one question based on the complete transcript. The model should only produce a short reflective question and should not predict the future, give direct advice, or reveal an outcome. The existing question cards could remain as a fallback when the model is unavailable or uncertain. A future version could also use multilingual speech recognition and matching text-to-speech voices while preserving the screen, LED, and push-to-talk feedback that helped users understand the interaction.

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?
Each session could become one structured data record containing the selected return point, original audio, transcript, question selected by the controller, spoken reflection, timestamps, and the participant’s later response when the message returns. I could also collect a short relevance rating for the selected question and record whether the wizard had to replace it. This dataset could help identify which questions work best for different concerns and could later be used to train or evaluate a more autonomous question-selection system. Additional useful signals include rotary and button-event timestamps, speech duration, pauses, response latency, and proximity to the device. With informed consent, video could also capture hesitation, gaze, and facial reactions, although voice and video data would need careful privacy protection and anonymization.

<details>
  <summary><strong>Submission Cleanup Reminder (Click to Expand)</strong></summary>

  **Before submitting your README.md:**
  - This readme.md file has a lot of extra text for guidance.
  - Remove all instructional text and example prompts from this file.
  - You may either delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
  - Your final submission should be neat, focused on your own work, and easy to read for grading.
</details>
