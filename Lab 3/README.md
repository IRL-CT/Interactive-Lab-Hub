# Chatterboxes

**Collaborators:** Ghaith Khalil and Aryan Palave

**Project:** One Thing

One Thing is a small desk companion for when there is too much to do and nothing gets started. It asks what we want to work on, how much time we have, and what the smallest first step could be. It reads that step back, lets us change it, and then stays quiet so we can begin.

# Part 1

## Setup

We used a Raspberry Pi 5, a USB microphone, a USB speaker, and the Mini PiTFT from Lab 2. The microphone is our sensor. The screen shows whose turn it is, and its two buttons let us confirm a plan, change it, or stop the device.

We checked the microphone, speaker, and screen together. The Pi detected both USB audio devices, played a spoken greeting, and captured microphone audio without overflow.

## A. Text to Speech

We wrote [greet.sh](greet.sh) to greet us by name. It takes a name as its first argument. Adding `compare` as the second argument plays the same greeting with espeak, Festival, and Piper.

We listened to the same greeting in espeak, Festival, and Piper, in that order. The first two sounded robotic to us. Piper sounded better, so we chose it for One Thing. The words were the same, but the first two voices made it sound more like a machine giving a prompt.

The samples are here: [espeak](audio/greeting-espeak.wav), [Festival](audio/greeting-festival.wav), and [Piper](audio/greeting-piper.wav).

## B. Speech to Text

We recorded one of us saying:

> I have fifteen minutes to work on my lab report. First, I will choose the photos.

[Our microphone recording](audio/own-speech.wav)

We ran the same recording through tiny.en and base.en on the Pi. Both used int8 and beam size 1. The recording is nine seconds long, including the silence around the sentence. The timings below exclude loading the model. Real-time factor is transcription time divided by those nine seconds.

| Model | Transcript | Time | Real-time factor |
| --- | --- | --- | --- |
| tiny.en | I have 15 minutes to work on my lab report. First I'll choose the photos. | 1.271 s | 0.141 |
| base.en | I have 15 minutes to work on my lab report. First I will choose the photos. | 2.067 s | 0.230 |

**Was the larger model worth the wait?** For this recording, no. We waited about 0.80 seconds longer for base.en, but both models kept the task, the number of minutes, and the first step. The difference was “I'll” versus “I will.” We started with tiny.en for the prototype. We would need more recordings to know whether that choice holds up with other voices or more background noise.

**Asking for a number:** Our [ask_number.py](ask_number.py) asks how many minutes are available, records the answer, transcribes it, and speaks the number back. It saves the audio and transcript so we can compare what was said with what was recognized. It keeps both numbers in a correction such as “ten, actually fifteen,” instead of silently choosing one.

The numbers were less reliable during the live demonstration. “Fifteen minutes” became “in minutes,” so the number disappeared. In a separate speaker-to-microphone replay, fifteen became `50`. That is why we kept the spoken readback. In our scripted demonstration, the plan used the agreed values; the system did not work out the missing number by itself.

## C. Turn-taking: knowing when someone has stopped talking

We replayed our Part B recording into Silero VAD at three silence settings. This kept the words and pauses the same each time. We supplied the audio in 512-sample blocks at 16 kHz and added two seconds of silence at the end. These were recorded-audio comparisons, not three live conversations. [Our measurements](media/turntaking-measurements.json).

| Silence setting | Turns detected | Turn ended, from start of recording | Transcription time |
| --- | --- | --- | --- |
| 0.2 s | 1 | 5.280 s | 1.015 s |
| 0.8 s | 1 | 5.856 s | 1.059 s |
| 1.5 s | 1 | 6.560 s | 1.001 s |

All three kept the whole sentence and produced the same transcript. Going from 0.2 to 1.5 seconds added 1.28 seconds before the device decided we were done. It did not improve the transcript in this example.

We then tried all three settings live, saying “I have ten... actually, fifteen minutes to work on my report,” with a pause after “ten.”

| Silence setting | First detected turn | Second detected turn |
| --- | --- | --- |
| 0.2 s | hand actually. | Actually 15 minutes to work on my report. |
| 0.8 s | I have 10. | actually 15 minutes to work on my report. |
| 1.5 s | I have 10. | actually 15 minutes to work on my report. |

All three split our correction into two turns. At 0.2 seconds, the first part was also misrecognized. The longer settings kept the words more accurately in these attempts, but still separated the original number from its correction. We did not measure the pauses between our words, so this does not show that the settings behave identically. Unlike the earlier replay, these were separate spoken attempts.

**How the settings felt:** At 0.2 seconds, the device felt too quick to decide we were finished. The pause before “actually” broke the correction into a separate turn. At 0.8 seconds, there was more room to pause, but our correction still got split. At 1.5 seconds, the wait felt slow, as though the device was taking too long to register the answer. Waiting longer also did not keep this attempt together.

We kept 0.8 seconds as a starting point. A pause before changing a number can still leave the device with an incomplete answer, so timing alone is not enough. Our wizard needs to keep listening for a correction and read the final plan back.

### The complete loop

With the 0.8-second setting, recognition took 1.059 seconds. Piper needed another 0.557 seconds to produce the first audio chunk of an echo reply. Adding the silence setting gives roughly 2.42 seconds before a reply could begin, before audio buffering and scheduling. This is an estimate from the components, not a measured live `echo_bot.py` conversation. Our rehearsal also showed that waiting for an operator through chat can add much more delay than the speech software itself.

## D. Storyboard

We considered a speaking Pomodoro timer, a checklist reader, and a next-step coach. We chose the coach because talking lets us explain that we are stuck, change our minds, or correct a number. That is useful here in a way that another timer button would not be.

![Our six-scene storyboard](images/storyboards.png)

| Scene | Person | Device |
| --- | --- | --- |
| Stuck | Sits down with several unfinished tasks. | Asks what they want to start. |
| Pick a task | “My lab report.” | Waits for the answer, then asks how much time is available. |
| Make it small | “Ten minutes.” | Asks for the smallest first step. |
| Read it back | “Write the first paragraph.” | Repeats the step and the time. |
| Change it | “Actually, photos first.” | Updates the plan and asks again. |
| Begin | Agrees and starts working. | Says “Ready when you are,” then stays quiet. |

### Our dialogue, with pauses

**Device:** What is one thing you want to get started on?<br>
*Wait for the answer, then 0.8 seconds of silence.*<br>
**Person:** My lab report.<br>
**Device:** How many minutes do you have?<br>
*Wait for the whole answer.*<br>
**Person:** Ten.<br>
**Device:** What is the smallest first step you could take?<br>
*Leave room to think. This answer is harder than giving a number.*<br>
**Person:** Write the introduction... actually, choose the photos first.<br>
**Device:** Ten minutes to choose the photos. Does that sound right?<br>
*Wait for agreement or a correction.*<br>
**Person:** Yes.<br>
**Device:** Ready when you are.

We worked backwards from the ending: someone starts doing one thing. The device only needs a task, a time, and a first step to get there. We then added branches for the places where that could break down:

- **Unclear number:** ask “Was that fifteen or fifty?”
- **Step too big:** ask what could be done in the first two minutes.
- **No task in mind:** offer studying, chores, or something else as starting points.
- **Correction:** repeat the changed plan before accepting it.
- **Long pause:** the wizard can say “Take your time” and keep listening.

These are options for the wizard to choose, not automatic decisions made by the device.

## E. Acting out the dialogue

We acted it out together without sharing the script with the partner beforehand. One of us asked the device's questions, and the other answered with a real task: getting started on a startup.

[![Our acted-out dialogue](images/acted-dialogue-poster.jpg)](media/acted-dialogue.mp4)

[Watch or download the video](media/acted-dialogue.mp4) · [YouTube](https://www.youtube.com/watch?v=CZMEIBN0Yo8)

**What changed when we acted it out?** We started with 20 minutes available. Then we landed on writing down ten ideas, which only needed ten minutes. Instead of repeating the first number, the device role asked another question about how long that step would take.

That was the useful difference from our written script. Time available and time needed are not always the same. We kept editable replies and a plan readback so the wizard can handle that adjustment instead of forcing the conversation through a fixed set of answers.

# Lab 3 Part 2

## Prep for Part 2

We wanted three things to be clearer: when the device had heard an answer, what plan it was proposing, and how to change that plan.

We added a face and state labels to the screen. Green bars respond to the microphone while listening. Amber dots show thinking. Blue bars animate while speaking. We kept text beside the colors so the interaction does not depend on recognizing a color alone.

![Our Pi interface states](images/interface-states.png)

*These are renders from our display code, not photographs of a test.*

The plan gets its own screen with the first step and number of minutes. The top button confirms it. The bottom button asks to change it. Once confirmed, the plan stays visible while the device stops talking.

### Revised interaction

| Moment | What our device does | What the person does |
| --- | --- | --- |
| Start | Speaks the task question, then shows LISTENING. | Says what they want to work on. |
| End of a turn | Shows THINKING after 0.8 seconds of silence. | Sees that the answer registered. |
| Find the time | Asks how many minutes are available. | Gives a number. |
| Clarify | The wizard checks an unclear number or asks how long the step needs. | Explains or corrects the answer. |
| Choose a step | Asks for a small first action. | Chooses something concrete. |
| Readback | Speaks the plan and shows it on screen. | Uses the top button to confirm or the bottom button to change it. |
| Correction | Asks what should change, then reads back the new plan. | Gives the correction aloud. |
| Finish | Says “Ready when you are. One small step is enough.” | Starts the task. |

## Prototype your system

We built the controller in [wizard.py](wizard.py), the Pi screen in [device_ui.py](device_ui.py), and the laptop interface in [controller.html](controller.html).

The microphone and speech processing run on the Pi. Silero detects when a turn ends, faster-whisper produces a transcript, and Piper speaks the reply. The wizard chooses what to say and fills in the task, time, and first step. The transcript helps with that choice but does not make the decision.

| Input or event | Result |
| --- | --- |
| Wizard selects a question or types a reply | Pi speaks it, then opens a listening turn |
| Person finishes speaking | Screen changes to THINKING; transcript appears on the controller |
| Wizard submits a plan | Pi reads it back and displays the task card |
| Top button on the task card | Confirm the plan |
| Bottom button on the task card | Ask what should change |
| Top button outside the task card | Open a listening turn |
| Bottom button outside the task card | Stop speech and cancel pending work |

We checked microphone capture, transcription, speech playback, stopping during a reply, and the full plan-confirmation sequence. We also fixed the speaker output rate: Piper produces 22.05 kHz audio, while our USB speaker needs 48 kHz. The code converts between them so speaking and microphone capture can run together.

### Our video

[![Our Pi demonstration](images/demo-poster.jpg)](media/one-thing-demo.mp4)

[Watch the 47-second demonstration](media/one-thing-demo.mp4)

One of us runs through the task, time, first step, correction, and confirmation. We used an agreed script for this take. To remove the delay from operating through chat, a prepared operator sequence advanced after each recognized turn and submitted the agreed plan values. The device was not independently deciding what those answers meant. Our [event log](media/demo-events.jsonl) records the screen changes and both button presses.

### Our controller

![Our live controller with plan fields and Pi preview](images/controller.png)

We captured this separately while documenting the interface. It shows the preset questions, custom reply field, editable plan, Pi preview, and session notes. The wizard can stop playback at any point. Keyboard shortcuts select the main prompts when a text field is not focused.

<details>
<summary>Run our prototype</summary>

Install the dependencies following [prep.md](prep.md). On our Pi:

```sh
cd ~/lab-hub/Lab\ 3
sudo cp one-thing.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start one-thing
```

On the laptop:

```sh
ssh -N -L 5050:127.0.0.1:5000 pi
```

Open `http://localhost:5050`. The controller connects through the SSH tunnel; the web server only listens locally on the Pi.

Our service file uses the `pi` account and `/home/pi/lab-hub/Lab 3`. Stop it with `sudo systemctl stop one-thing` before running the separate speech exercises. `sudo systemctl start window-clock.service` restores Lab 2. We have not enabled Lab 3 at boot.

</details>

## Test the system

We recorded a walkthrough with one of us and also had two friends try the prototype. Both thought it was really cool. Their feedback was positive, and we got the following changes: 
- Screen states: A friend paused after answering and looked at the device, unsure whether it was listening or processing, so we added visible LISTENING and THINKING labels.
- Plan confirmation: A friend wanted to change the suggested first step but was unsure whether saying a correction would replace the plan. We changed it to showing plan on screen, adding a button to request a change and reading the updated plan back before confirmation.

### What worked well about the system and what didn't?

We got through the whole correction. The first plan was choosing photos. The bottom button opened the correction, and the top button confirmed writing the introduction instead. Keeping the plan on screen made it clear what was being accepted.

Recognition was the weak point. In the recording, “My lab report” became “of my library for it,” and the number disappeared from “Fifteen minutes.” Our agreed script let the demonstration continue. An open conversation would need another question there.

We also caught a timing problem: LISTENING appeared before the microphone's short settling period had finished. An immediate answer could lose its beginning. After the recording, we changed the code to keep the speaking cue visible until the microphone is ready. Our video shows the earlier version.

### What worked well about the controller and what didn't?

The preset questions kept the common replies close at hand. We could still type a different reply or change the plan. Stop cancelled speech and pending replies, which mattered when a turn needed to be restarted.

The first rehearsal was too slow because each turn was being triggered through chat. The prepared sequence made the recorded take quicker, but it only covered our agreed script. We have not measured how quickly a wizard could handle an unexpected answer through the browser.

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

Hearing that a turn ended is different from understanding it. We would keep task, time, and first step as separate fields and confirm them before moving on. Missing numbers should cause another question. A correction should update the relevant field and trigger another readback. We would keep the buttons as a simple way to accept or change a plan when speech recognition gets something wrong.

These lessons come from our own walkthrough. Our friends’ positive reactions did not give us enough detail to draw further conclusions about usability.

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?

Our session logs already store replies, automatic transcripts, turn lengths, plan changes, button presses, and notes. With permission, we could add synchronized audio and correct the transcripts against it. That would let us compare what someone said with what the system heard and what the wizard did next.

A camera could add gestures and whether someone was looking at the device. We would only collect that if it answered a useful question and the person agreed. Our current controller does not save raw microphone audio, so its transcripts alone cannot tell us exactly what was said.

## Contributions and influences

AI helped us with planning and code. We used the [IRL-CT Lab 3 starter](https://github.com/IRL-CT/Interactive-Lab-Hub/tree/Fall2026/Lab%203) for the speech exercises and reused the display driver from Lab 2. The calm desk interaction in One More Window helped shape our starting point for One Thing.
