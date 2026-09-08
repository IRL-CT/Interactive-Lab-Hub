# Recreating the Masters of Interactive Light

**COLLABORATORS:** Afroza Aktar, Dhanu

**THE MASTERWORK WE DREW FROM THE HAT:** The Nixie Tube — 1950s.

---

# The Report

## Part 0. Know Your Master

Our masterwork is the Nixie tube, an electronic numerical display that
became prominent during the 1950s. Early Nixie displays were developed
by Haydu Brothers Laboratories and introduced commercially by the
Burroughs Corporation. They were used in electronic measuring
instruments, counters, calculators, clocks, and other equipment before
LED and modern digital displays became common.

A Nixie tube is a sealed glass tube containing low-pressure gas,
usually including neon. Inside the tube are separate metal cathodes
shaped like the numerals 0 through 9. The numerals are physically
stacked behind one another. When electrical power is applied to one
selected cathode, the gas surrounding that numeral produces a warm
orange-red glow. Only the selected numeral becomes visible. When the
input changes, the first numeral stops glowing and a different
complete numeral appears.

The core interaction is that a person or electronic system provides a
numerical input, and the tube responds by making the corresponding
numeral glow. Unlike a modern seven-segment display, which constructs
a number from several reusable line segments, a Nixie tube contains a
separate complete shape for every numeral. The number therefore seems
to materialize as an individual glowing form inside the glass.

For our recreation, a technician turns a dial on a measuring
instrument. Each adjustment causes a different orange numeral to glow
inside our simulated Nixie tube. The actor reacts to the changing
reading and records the final result.

### Strengths
The Nixie tube presents each numeral as a complete, readable shape.
Its warm orange glow is distinctive and visually expressive. Because
the numerals are arranged at different physical depths, the display
has a dimensional quality that modern flat displays do not have. It
also represents an important transition from mechanical number
displays to electronic digital displays.

### Weaknesses
Nixie tubes require high voltage, are made of fragile glass, and can
eventually suffer from uneven glow or cathode deterioration. A single
tube normally displays only one character, so several tubes are needed
to show time or a large number. The stacked numeral shapes can
partially obstruct one another, and the technology is less practical
than modern LED or LCD displays.

## Part A. Plan

**Setting:** Our recreation takes place at a dark demonstration table.
The simulated Nixie tube is positioned beside the actor so that the
actor's hand and the glowing display are visible in the same camera
frame.

**Players:** The players are the actor, the simulated Nixie tube, and
a hidden wizard operating the laptop. The audience also participates
by comparing the number shown with the actor's fingers to the numeral
displayed by the tube.

**Activity:** The actor holds up different numbers using their fingers.
The hidden wizard observes each hand pose and selects the matching
numeral on the laptop. The phone responds by making that complete
numeral glow orange inside the simulated tube. When the actor lowers
their hand, the display returns to darkness.

**Goals:** The actor wants the tube to recognize and display the number
shown by their fingers. The tube's apparent goal is to translate a
human hand signal into a glowing numerical form. The wizard's goal is
to respond at the correct moment so the tube appears to recognize the
actor's gesture.

### Our three storyboards

**Storyboard 1: Basic finger interaction.**
The scene begins with the phone display dark. The actor sits or stands beside it and holds up two fingers. The hidden wizard selects 2 on the laptop, causing an orange 2 to glow on the phone. The actor then holds up five fingers. The 2 disappears and a glowing 5 appears. The actor looks at the display and understands that it is copying the finger numbers.

![Storyboard 1](Images/storyboard-1.jpeg)

**Storyboard 2: Add clearer transitions.**
The actor switches on the simulated Nixie tube, causing a brief orange flicker. The actor holds up one finger, and a glowing 1 appears. The actor lowers their hand, and the display becomes dark. The actor then holds up three fingers, and a glowing 3 appears. This version establishes a clear relationship between showing a number, displaying the number, and returning to darkness when no number is shown.

![Storyboard 2](Images/storyboard-2.jpeg)

**Storyboard 3: Final version.**
The scene begins with a close-up of the dark Nixie tube. The actor enters and says, "This tube turns numbers into light." The actor holds up one finger, and an orange 1 glows inside the tube. The actor lowers their hand, and the display briefly becomes dark. Next, the actor holds up three fingers, causing a complete orange 3 to appear. The interaction continues with five fingers and then eight fingers using both hands. Every numeral disappears before the next numeral glows into existence. At the end, the actor lowers both hands, and the tube returns to darkness.

![Storyboard 3](Images/storyboard-3.jpeg)

**Feedback from our breakout room:**
(to be added)

## Part B. Act Out the Interaction

We first acted out the interaction before using the working phone controller. One team member played the technician and showed different numbers using their fingers. The other team member pretended to be the hidden wizard and announced which number would appear on the display. We used a dark phone screen as the instrument and verbally described when each orange numeral should appear.

Some actions seemed clearer on paper than they did when we performed them. At first, the technician changed finger gestures too quickly, which did not give the hidden wizard enough time to recognize the number and respond. The transition also looked less believable when the actor immediately announced the result before the numeral appeared. We learned that the technician needed to hold each gesture for approximately two or three seconds, wait for the phone to respond, and then look at the display before speaking.

Acting out the scene also gave us a new idea: using finger gestures was more engaging than pretending to turn a dial. The finger gesture creates a clear relationship between the technician's body and the glowing number. For example, when the technician shows five fingers and the instrument displays `5`, the audience can immediately understand the input and output. We therefore changed our final storyboard from dial control to finger control.

We also realized that the actor's eye movement and reaction were important. The interaction felt more convincing when the technician looked at their own hands, turned toward the instrument, waited for the numeral to appear, and then reacted to the result. When the actor did not look at the display, the glowing number appeared disconnected from the performance.

Several moments could go in different directions during the interaction. The hidden wizard could accidentally select the wrong numeral, the wireless command could be delayed, or the actor could show an unclear finger gesture. To prepare for these possibilities, the actor holds each gesture until the correct number appears. If the wrong number appears, the actor pauses and repeats the gesture, allowing the wizard to correct it. When the actor lowers both hands, the wizard selects **OFF**, returning the display to darkness.

After acting out the scene, we updated the final storyboard to show the complete real-time loop: the technician presents a finger number, the hidden wizard observes it, the wizard selects the matching numeral on the laptop, the phone glows with that numeral, and the technician reads and responds to the result. This rehearsal helped us improve the timing, clarify the connection between the gesture and the light, and make the simulated instrument appear more responsive.

## Part C. Prototype the Light

We used the Tinkerbelle tool to turn the phone into a remotely controlled Nixie-tube display. The phone opened the Tinkerbelle webpage in display mode, while the laptop opened the same webpage in controller mode. Both devices were connected to the same Wi-Fi network. A Python Flask server running on the laptop carried messages from the laptop controller to the phone.

We modified the original Tinkerbelle interface specifically for the Nixie tube. Instead of controlling only the phone's background color, our laptop control panel included buttons for the numerals `0` through `9`, along with Power On, Power Off, and Blank Tube controls. When the hidden operator selected a numeral on the laptop, the Python server broadcast that value to the phone. The phone then displayed the selected numeral in a warm orange-red color against a dark background. The complete program is in [`nixie_phone.py`](nixie_phone.py) in this folder.

The phone in display mode, showing the unlit simulated tube with its glass outline and wire mesh:

<img src="Images/phone-display.jpg" alt="Phone acting as the Nixie tube display" width="300"/>

The laptop controller page used by the hidden wizard:

![Laptop controller interface](Images/laptop-controller.jpg)

We mapped the Nixie tube's light vocabulary to the controller in the following way:

* **Complete darkness** represented an instrument that was switched off.
* **A brief orange flicker** represented the tube receiving power and beginning to operate.
* **A complete glowing numeral** represented the selected numerical value.
* **A short dark interval** represented the transition from one shaped cathode to another.
* **A strong and steady orange glow** represented a stable final measurement.

We designed the phone display to resemble a glass Nixie tube. The screen included a dark background, a curved glass-like outline, a subtle reflection, a wire-mesh pattern, and an orange numeral surrounded by several layers of glow. When the selected value changed, the old numeral first faded into darkness. The new numeral then appeared with a short ignition flicker before settling into a steady glow.

We deliberately concentrated on the light behavior before decorating the phone or adding additional effects. We tested the orange color, brightness, darkness between values, startup flicker, and duration of each numeral. These behaviors needed to communicate the identity of the Nixie tube even when the phone was not yet hidden inside a costume.

The Tinkerbelle connection responded quickly enough for the wizard to change the numeral immediately after the technician turned the dial. The most difficult part was not the network delay but the human timing. If the wizard pressed a number too early, the display changed before the technician completed the physical action. If the wizard waited too long, the instrument appeared broken. The best result occurred when the wizard watched the technician's hand and selected the numeral immediately after the dial stopped moving.

## Part D. Wizard the Device

One collaborator performed beside the simulated Nixie tube while the
other remained outside the camera frame with the laptop controller.
The actor showed different numbers using their fingers. The hidden
wizard watched each gesture and selected the matching numeral from the
laptop. When the actor lowered their hand, the wizard selected Blank
Tube.

The interaction worked best when the wizard watched the actor instead
of following a predetermined timer. The wizard waited until the finger
pose was clearly formed and then selected the corresponding number.
This made the phone appear to recognize the actor's hand gesture in
real time.

The actor also paused and looked at the phone after each gesture. Their
reaction helped the audience understand that the glowing numeral was a
response to the human input. The hidden wizard allowed us to simulate
gesture recognition without building a computer-vision system.

**First wizarded test recording:** [lab1-initial.mov](Videos/lab1-initial.mov)

## Part E. Costume the Device

For our phone costume, we used a clear display dome with a rounded top and a wooden base. We selected this object because its transparent enclosure and curved shape resemble the glass body of a Nixie tube. The smartphone will be placed vertically inside the dome with its screen facing the audience. When an orange numeral appears on the screen, the clear enclosure will make the phone look more like a glowing electronic tube than an ordinary mobile device.

We will use a small black-cardboard support to hold the phone upright. We will arrange thin copper-colored wires near the bottom and behind the phone to suggest the internal cathode wires found inside an original Nixie tube. We also added a small label reading "Nixie Signal Unit" to give the base the appearance of a 1950s laboratory instrument.

We considered placing the dome on a larger cardboard box, but decided that a large box could make the prototype look bulky and distract from the clear tube.

The most important design concern was keeping the phone secure while ensuring that the screen remained clearly visible to the camera. The phone must also be easy to remove and must not be completely sealed because it could become warm during operation. Therefore, we will avoid permanent glue and use a removable cardboard holder or tape. The existing dome gives us an opportunity to make the simulated Nixie numeral appear enclosed inside glass, which helps the light read more convincingly as a physical tube.

Photo of the final costumed prototype:

<img width="2394" height="4000" alt="20260907_181415" src="https://github.com/user-attachments/assets/8fc5c1a6-a174-4569-9752-2472f948174e" />


## Part F. Record

Our final video sketch is approximately 60 seconds long, staged as a dimly lit 1950s electronics laboratory. The costumed phone sits inside its clear dome, dark at first. The technician sits down, says, "Let's check the signal," and shows numbers with their fingers — two, then five, then eight using both hands. After each gesture, the hidden wizard selects the matching numeral on the laptop, and a complete orange numeral glows inside the dome, with a brief darkness between values. The technician reads the final result ("Stable at eight"), writes it in a notebook, lowers both hands, and the wizard switches the tube **OFF**.

Our aim was the bar set at the top of the lab: someone who knows Nixie tubes should recognize the warm orange glow, glass enclosure, and one-numeral-at-a-time transitions, while someone who doesn't should still understand that the instrument answers the technician's finger count with a matching glowing numeral.

The technician's finger gesture, the wizard's hidden laptop command, and the phone's light formed a real-time interaction loop:

**Technician shows a number with their fingers → hidden wizard observes the gesture → wizard selects the matching numeral on the laptop → the command is sent to the phone → the matching numeral glows → technician reads and responds to the result.**

The storyboard communicates the order of events in the performance, while this interaction loop explains how the apparent device behavior was produced. The system did not automatically recognize the technician's fingers. Instead, the hidden wizard provided the intelligence by observing the gesture and manually selecting the correct number. This Wizard-of-Oz arrangement allowed us to recreate the experience of an interactive Nixie instrument without building an electronic hand-recognition system or a real high-voltage Nixie tube.

**Final video sketch:** [lab1.MOV](Videos/lab1.MOV)

### Collaborators and Influences

Afroza Aktar and Dhanu collaborated on the research, storyboards, acting, Tinkerbelle setup, costume construction, testing, and recording. One collaborator performed as the technician while the other operated the laptop as the hidden wizard. We exchanged roles during testing so that both collaborators could understand the actor's and operator's perspectives.

Our prototype was informed by the original Tinkerbelle project from the Interactive Lab Hub and by historical descriptions of Nixie-tube displays. We modified the Tinkerbelle code to communicate numerical values instead of only changing the phone's background color.

---

# Part 2 — ReMastering the Light

## Feedback from other groups

We exchanged feedback with three other groups:
[edmkong's group](https://github.com/edmkong/Interactive-Lab-Hub), the
[lightsaber group](https://github.com/ammarsyed/Interactive-Lab-Hub/tree/Fall2026/Lab%201),
and [wristabnd's group](https://github.com/khanlamiah019/Interactive-Lab-Hub/tree/Fall2026/Lab%201). 

- [edmkong's group](https://github.com/edmkong/Interactive-Lab-Hub) found the Part 0 research clear — especially the strengths, weaknesses, and core interaction — and liked that we modified the Tinkerbelle tool to fit our piece, calling the final video clear and well done. Their critiques focused on the storyboards: the phone display should actually be drawn dark in the frames where it is off; the descriptions talk about finger gestures, but the drawings never show the fingers; the frames are hard to follow scene by scene, particularly in Storyboard 1; and the actor should stay visible in every frame instead of disappearing mid-sequence.
- The [lightsaber group](https://github.com/ammarsyed/Interactive-Lab-Hub/tree/Fall2026/Lab%201) found the storyboards clear and the Nixie tube adaptation well done, and liked the front end with the full set of numerals and transition states. They caught a mismatch between the storyboard descriptions and the storyboard numbers.
- The [wristabnd's group](https://github.com/khanlamiah019/Interactive-Lab-Hub/tree/Fall2026/Lab%201) said the hand-gesture interaction itself was clear, but the *context* was not: what setting is this device used in, and who would be interacting with it? They pointed out that a viewer who has never heard of a Nixie tube needs more help understanding what it is and why it exists.

The context critique is the most useful one for our remix: our recreation shows *how* the tube behaves but not *where it lived* — the 1950s laboratory, the technician's job of reading and recording measurements. A stronger version would establish the scene (instrument panel, notebook, lab setting) before the first numeral ever glows.

For our updated version, We explored three possible contexts for transforming the Nixie-inspired display. Each storyboard examines the idea, metaphor, model, display, error, scenario, task, and control.

Storyboard 1: Sign-Language Interpreter
This storyboard explores using the Nixie-inspired device as a communication tool. A person performs the sign for “sorry,” the camera recognizes the gesture, and the word SORRY glows on the display. Tapping the screen for the first time also creates a humming sound. If the wrong word appears, the person can repeat the gesture.
<img width="1600" height="1031" alt="sign_nixie" src="https://github.com/user-attachments/assets/212dc7dd-32c1-4880-80a1-2ec22093aff5" />




Storyboard 2: Doctor’s Office
This storyboard shows the device in a doctor’s waiting room. The receptionist selects the next patient, and the patient’s name glows on the display. The glowing name acts like a gentle guide that tells the patient when it is time to enter the doctor’s room. If the wrong name appears, the receptionist can correct it.
<img width="1599" height="1198" alt="clinic_nixie" src="https://github.com/user-attachments/assets/dc6d2045-3003-4f50-bc1b-a30ae0b0fead" />



Storyboard 3: Tennis Score
This storyboard uses the Nixie-inspired display as a tennis scoreboard. The umpire presses a button whenever a player wins a point, and the display changes through the normal tennis scores: 0, 15, 30, and 40. If a point is given to the wrong player, the umpire can press Undo and correct the score.
<img width="1600" height="893" alt="tennis_nixie" src="https://github.com/user-attachments/assets/334e78dc-602c-47dd-85ee-177a93dee050" />



We selected turning the Nixie tube into a **sign language interpreter** because it gives the redesigned Nixie tube a clear user and purpose. It turns the glowing display into a communication bridge between someone using sign language and someone who does not understand it. The display keeps the original warm orange glow, glass enclosure, and one-value-at-a-time transitions, but instead of showing numerals it shows words. The performer signs a word such as "thank you", "sorry", or "please", and the tube glows with the matching word in the same Nixie style.

We updated `nixie_phone.py` so the laptop controller now has ten word buttons (Hello, Thank you, Sorry, Please, Yes, No, Help, Love, Friend, Goodbye) in place of the 0 through 9 keypad. The server only accepts words from its allowed list, and the tube text wraps and scales so a multi-letter word still fits inside the glass. The hidden wizard watches the sign and presses the matching word, exactly as they selected numerals before.

We also gave the tube a voice of its own, though not a spoken one. Real Nixie tubes run on high voltage, and their power supplies give off a faint high-pitched whine while the tube is lit. The phone now generates that hum with the browser's built-in audio synthesis: it fades in when the wizard presses Power On, fades out on Power Off, and a short static crackle plays each time a new word ignites. No audio files are needed, so the project is still a single Python file.

The phone in display mode, showing the words simulated tube with its glass outline and wire mesh:
<img width="876" height="1600" alt="WhatsApp Image 2026-09-07 at 4 05 30 AM" src="https://github.com/user-attachments/assets/a9b3708e-1a42-42ef-bb0a-6abd34e4cb26" />


The laptop controller page used by the hidden wizard:
<img width="768" height="497" alt="Screenshot (946)" src="https://github.com/user-attachments/assets/5a64cb5e-f21b-4987-95ee-bdd1e7296426" />


Final Lab1b video:

<img width="464" height="832" alt="Lab1b(1)" src="https://github.com/user-attachments/assets/01c9baf7-714f-4fa0-bf6f-62b5f3cabe31" />



Costume of our nixie tube 
<img width="2394" height="4000" alt="20260907_181415" src="https://github.com/user-attachments/assets/1bb8d122-8ca2-4356-951c-7d68b8e12fa7" />



This redesign changes the Nixie tube from a numerical readout into a communication aid, and it answers the context critique: the device now has a clear setting and a clear user, someone signing to a person who does not know sign language.
