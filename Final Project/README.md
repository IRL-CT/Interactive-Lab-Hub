# Final Project

### Collaborator: Melody Huang (yh2353), Dingran Dai (dd699)

<details><summary><strong>Instruction</strong></summary>

Project plan - November 10  (updated documentation due in Canvas November 11)

** Peer feedback on Project plans: November 13 ** <-- this is part of class participation!

Functional check-off - December 1 

Final Project Presentations - December 8

Write-up and documentation due - December 15 

## Objective

The goal of this final project is for you to have a functioning and well-designed interactive device of your own design.
 
## Description
Your project is to design and build an interactive device to suit a specific application of your choosing, and *test the interaction with people*. 

## Deliverables

1. Project plan: Big idea, timeline, parts needed, fall-back plan.

2. Functioning project: The finished project should be a device, system, interface, etc. that people can interact with.

3. Documentation of design process
4. Archive of all code, design patterns, etc. used in the final design. (As with labs, the standard should be that the documentation would allow you to recreate your project if you woke up with amnesia.)
5. Video of someone using your project
6. Reflections on process (What have you learned or wish you knew at the start?)
7. Group work distribution questionnaire



## Change of Design

It is fine to change your project goals, but please resubmit the project plan for the new design when you do that.

## Grading rubric

20% Project planning: Allocation of needed resources (time, people, materials, facilities) anticipated well.

20% Design of project: Interaction, hardware and software aspects of projects planned well.

20% Testing of project: Functional or wizarded system tested with people

20% Prototype functionality: System capable of interaction, either through autonomous or wizarded mechanisms

20% Project documentation: Text, video, and photo of project illustratign capability and documenting plans and process

## Teams

You can and are not required to work in teams. Be clear in documentation who contributed what. The total project contributions should reflect the number of people on the project.

## Examples

[Here is a list of good final projects from previous classes.](https://github.com/FAR-Lab/Developing-and-Designing-Interactive-Devices/wiki/Previous-Final-Projects)

</details>


# The Museum of Lost Sound


## 🎯 Big Idea

This project creates a **physical, touch-based interactive exhibit** where visitors can explore “lost sounds” of retro technologies—typewriters, rotary phones, cassette players, and more.

When a visitor touches or lifts a physical object:

* 🎵 A corresponding nostalgic sound plays through a Bluetooth speaker
* 🖥️ The Mini PiTFT displays historical information, images, or fun facts
* ✨ LEDs provide immediate visual feedback

The goal is to offer a **tangible, multisensory experience** that teaches, entertains, and invites curiosity about past technologies.

---

## 🧩 Interaction Design

### ▶️ **Input**

| Action                  | Sensor                             | Purpose                                                 |
| ----------------------- | ---------------------------------- | ------------------------------------------------------- |
| Touch object            | **MPR121 Capacitive Touch Sensor** | Identifies which item was touched                       |
| Hand approach / gesture | **APDS9960**                       | Pre-trigger reaction when a hand gets close             |
| Rotary selection        | **Rotary Encoder**                 | Switch between multiple sounds/info for the same object |
| Button input            | **Qwiic Buttons (Red / Green)**    | “Next sound,” “Replay,” or “Mode switch”                |

---

### ▶️ **Output**

| Output Type           | Component                 | Purpose                                          |
| --------------------- | ------------------------- | ------------------------------------------------ |
| Audio                 | **Bluetooth Speaker**     | Plays the corresponding nostalgic sound          |
| Visual                | **Mini PiTFT**            | Displays text, images, or facts                  |
| Light                 | **PCF8574 + LEDs**        | Light feedback when interacting                  |

---

## 🛠️ Hardware Mapping

### **Input → Output Flow**

```
User touches object → MPR121 triggers →
Raspberry Pi identifies item →
Bluetooth speaker plays sound +
Mini PiTFT shows content +
```

### **Overall Mapping**

| Input Component                | Function          | Output Component  | Function           |
| ------------------------------ | ----------------- | ----------------- | ------------------ |
| MPR121                         | Touch detection   | Bluetooth Speaker | Audio playback     |
| APDS9960                       | Gesture/proximity | Mini PiTFT        | Display content    |

---

## 📦 Materials List

| Component                      | Purpose                          |
| ------------------------------ | -------------------------------- |
| Raspberry Pi 5 Model B         | Main controller                  |
| Pi Power Supply                | Power                            |
| 64GB MicroSD                   | Operating system & project files |
| Mini PiTFT                     | Visual display                   |
| MPR121 Capacitive Sensor       | Touch detection                  |
| APDS9960                       | Gesture & proximity detection    |
| Rotary Encoder + Qwiic Buttons | Navigation & control             |
| PCF8574 GPIO Expander + LEDs   | Light feedback                   |
| 9G Servo + Servo pHAT          | Optional object animation        |
| Bluetooth Speaker              | High-quality audio output        |
| Breadboard, wires, copper tape | Prototyping, touch connection    |

---

## 🗂️ Project Timeline

| Milestone                          | Date   | Notes                                                  |
| ---------------------------------- | ------ | ------------------------------------------------------ |
| **Hardware Setup**                 | Nov 15 | Set up Pi, PiTFT, sensors, audio; verify components    |
| **Module Development**             | Nov 18 | Build: touch detection → audio → display pipeline      |
| **Module Testing**                 | Nov 20 | Test each object individually                          |
| **System Integration**             | Dec 1  | Combine all objects, sensors, LEDs, audio              |
| **User Interaction Testing**       | Dec 5  | Observe behavior; tune sensitivity & feedback          |
| **Final Assembly & Documentation** | Dec 14 | Assemble final exhibit, record demo, finalize write-up |

---

## 🔍 Testing Plan

### ✔ Module Testing

* Each MPR121 touch point triggers correctly
* Audio playback has correct mapping
* PiTFT displays the proper text/images
* Gesture detection triggers pre-animations or light cues

### ✔ Integration Testing

* Switching between objects works reliably
* LED + audio + display timing is synchronized
* Servo movement (if used) is stable and safe

### ✔ User Testing

Focus on:

* Is it intuitive where to touch?
* Are visuals readable on the PiTFT?
* Do sounds feel meaningful and nostalgic?
* Do LEDs improve discoverability?

User testing data includes:

* Time to understand interaction
* Behavioral observations
* Confusion points
* Suggested improvements

---

## 🧯 Fallback Plan

| Situation              | Backup Plan                                                    |
| ---------------------- | -------------------------------------------------------------- |
| **MPR121 fails**       | Trigger audio manually using Qwiic buttons (Wizard-of-Oz mode) |
| **PiTFT malfunctions** | Output simplified info via terminal or LED blink codes         |
| **Bluetooth issues**   | Switch to wired speaker or piezo buzzer                        |
| **Time constraints**   | Build with 3–5 core objects instead of full set                |

---

## 📁 Final Documentation (to be completed at project submission)

The final submission will include:

* Design process documentation
* Wiring diagrams, flowcharts, and hardware layout
* Full source code with comments
* Photos of prototype, testing, and final build
* Demo video of user interaction
* Reflection & lessons learned

---

## 11/15 Log

**What We've Built So Far**

We have successfully created a system where:
1.  A user touches a sensor pad (connected to the **MPR121**).
2.  The `main.py` script detects this touch.
3.  It looks up the pad number in the `config.py` file.
4.  It tells the `audio_player.py` to play the correct `.mp3` sound.
5.  It loads the corresponding `.txt` file and tells the `display.py` class to show the object's name and its description on the **PiTFT screen**.
6.  The `display.py` class correctly wraps the text to fit the screen.

**Video Showcase**

https://github.com/user-attachments/assets/73619182-87a8-4e3f-9667-aa8d750fe627

**Next Steps**

The core loop works, but the user experience can be improved. Right now, a user can press multiple buttons rapidly, causing sounds to interrupt each other and the display to flash. Our next step is to manage the "state" of the exhibit and change the interaction to when users pick up the object, the device will play the sound.

---

## 12/01 Log

**What We've Built So Far**

We have upgraded the exhibit from a simple soundboard into a robust, state-aware interactive kiosk. The system now manages user flow, prevents audio overlapping, and offers a deeper visual history using the PiTFT buttons.

**1. Dual-Mode Visual Discovery:** We implemented a layered information system.
    * **Touch:** Plays audio and shows the object's description.
    * **Button Press (Action Shot):** Pressing the **Top Button** on the PiTFT switches the display to a historical photo of people *using* the object, overlaid with a "Popular Year" fact (e.g., *"1990s Storage: Only 1.44MB!"*).
    * **Button Press (Info):** Pressing the **Bottom Button** switches back to the text description.
    
**2. Intelligent Idle Mode:** If no interaction occurs for **30 seconds**, the screen automatically resets to a high-contrast "Pick up any Object" prompt, ensuring the exhibit is always ready for the next visitor.

**3. Input Locking (The 10-Second Rule):** To prevent audio chaos, the system "locks" input for **10 seconds** (or until the sound finishes) once a user touches an object. This forces the user to engage with the current content before switching.

**4. Auto-Debounce:** Added specific sleep timers to smooth out sensor readings and prevent accidental double-triggering.

**Code Explanation**

We moved away from simple `sleep()` commands to a non-blocking time-based state machine in `main.py`.

**1. Input Locking (The Busy State)**
We calculate a target `unlock_time`. If the current time is less than this target, the loop skips input detection.

```python
# main.py
if current_time < unlock_time:
    time.sleep(0.1)
    continue # Skip loop, effectively locking the system
```
**2. Idle Timeout We track the timestamp of the last_interaction. If the difference between now and then exceeds 30 seconds, we trigger the reset.**

```python
# main.py
if not is_idle_mode and (current_time - last_interaction_time > 30):
    screen.show_idle() # Reset screen to "Pick Up Object"
    is_idle_mode = True
    audio.stop()
```

**3. Context-Aware Buttons We track which object is currently active (current_active_pad) so the physical buttons know which specific photo to load.**

```python
# main.py
if not button_a.value and current_active_pad is not None:
    obj = OBJECTS[current_active_pad]
    # Shows the "Action Image" defined in config.py
    screen.show_photo(obj["action_image"], obj["year_text"])
```

**Video Showcase**

**1. Here is the demo video for the photo function**


https://github.com/user-attachments/assets/32da5358-9645-420e-91cc-b72d08f50262


**2. Here is the video for terminal**

https://github.com/user-attachments/assets/d3235dd2-5367-4f05-a2c6-8ce01d9400d5


**Next Steps: Physical Prototyping & Pilot Testing**

Based on feedback regarding the small size of the Mini PiTFT (1.14"), we are pivoting the physical design to create a more immersive viewing experience.

**1. "Peep Hole" Enclosure Design**

The Concept: To address the small screen size, we will design an enclosed "stage" or "peep box" for the display. This forces the user to lean in and focus on the screen through a small opening, creating an intimate, voyeuristic feeling ("looking into the past").

Goal: This controls the viewing angle and makes the small image feel larger and more significant.

**2. Low-Fidelity "Stage" Prototype**

Action: Before 3D printing the final casing, we will construct a cardboard prototype of the stage/enclosure.

Setup: This will house the PiTFT and conceal the wiring, leaving only the 3D-printed artifacts and the "peep hole" exposed to the user.

**3. Pilot Testing (Ergonomics & Visibility)**

Test: We will conduct a user test with the cardboard prototype to verify:

Height/Angle: Is the peep hole comfortable to look into?

Visibility: Can the user clearly read the text and see the photos through the opening?

Flow: Does the act of "peeking" distract from touching the objects, or enhance the mystery?


---

## 12/03 Log

**What We've Built So Far**

We finalized the "Stage" concept for the Museum of Lost Sounds. The design features a multi-layered box structure:

- Base Layer (Layer 1): Hides the Raspberry Pi and heavy wiring.

- Interaction Surface: designated spots for the artifacts (phone, typewriter, etc.) to sit.

Prototyping: We constructed a low-fidelity physical prototype using cardboard to test the ergonomics.

**Design Draft**

<img width='400' src='https://github.com/user-attachments/assets/502f1e80-a890-4fea-a184-1dddb341e417'>

**Prototype**

<img width='400' src='https://github.com/user-attachments/assets/f1ba68a4-a4d3-43ab-8fd5-e9a5ac34e792'>

---

## 12/04 Log

**What We've Built So Far**

We upgraded the interaction model from **"Touch to Activate"** to **"Lift to Activate"**. This creates a more intuitive, museum-like experience where visitors physically pick up artifacts to hear their sounds.

**1. Lift Detection Logic:** Instead of triggering when a user touches an object, the system now triggers when the object is **lifted** (circuit breaks). Objects rest on conductive pads, and removing them breaks the connection.

| Old Behavior | New Behavior |
|--------------|--------------|
| Touch pad → Trigger | Object rests on pad → Nothing |
| Release pad → Nothing | Lift object → **Trigger!** |

**2. State Tracking:** The MPR121 sensor only tells us "is it touched right now?" To detect a *lift*, we need to remember the previous state and detect the transition from `touched → not touched`.

**3. Automatic Idle Return:** After the audio finishes playing, the system waits **5 seconds** (allowing button presses), then automatically returns to the idle screen. This replaces the old 30-second timeout.

**Code Explanation**

**1. Lift Detection (State Transition)**

We added a `get_lifted()` method to `touch_input.py` that tracks state changes across frames:

```python
# touch_input.py
def get_lifted(self):
    for i in range(12):
        current = self.mpr121[i].value
        was_touched = self.previous_state[i]
        self.previous_state[i] = current
        
        # Was resting (True) -> Now lifted (False) = TRIGGER
        if was_touched and not current:
            return i
    return None
```

**2. Non-Blocking Idle Timer**

Instead of a blocking `time.sleep(5)`, we use a timestamp so buttons still work during the wait:

```python
# main.py
if not audio.is_busy() and audio_end_time is None:
    audio_end_time = current_time  # Start timer

if audio_end_time and (current_time - audio_end_time >= 5):
    screen.show_idle()  # Go to idle after 5 seconds
    is_idle_mode = True
```

**3. Button Press Resets Timer**

Pressing a button during the 5-second wait resets the countdown:

```python
# main.py
if not button_a.value and current_active_pad is not None:
    audio_end_time = current_time  # Reset 5 second timer
    screen.show_photo(obj["action_image"], obj["year_text"])
```

**Physical Setup**

Each object needs:
1. **Conductive base** (copper tape) that contacts the MPR121 pad
2. **Solid resting position** so the circuit is closed when "home"

```
OBJECT AT REST:              OBJECT LIFTED:
    ┌─────┐                      ┌─────┐  ← picked up
    │     │                      │     │
────┴─────┴────               ───────────
   MPR121 pad                  MPR121 pad
   (TOUCHED)                   (NOT TOUCHED)
   Circuit CLOSED              Circuit BROKEN → TRIGGER!
```



**3D Printing Challenges Solved**

In the previous prototype, we printed the objects using standard filaments and attached copper tape to the bottom. However, the filament was not conductive or stable enough to establish a threshold for triggering interaction. As a solution, we switched to conductive filament, and it worked! The next challenge we faced was that the temperature of the plate and the printing chamber was not high enough for the filament to adhere properly, failing three plates. We ended up turning one fan off and successfully printed all the objects.

<img width='400' src='https://github.com/user-attachments/assets/083f3151-aa38-4709-9ddb-99d5f71fba47'/>

Also, we designed the 3D render for our stage

<img width='400' src='https://github.com/user-attachments/assets/702be439-533b-4d37-928d-be1e54cf43e4'/>

**Video Showcase**

https://github.com/user-attachments/assets/1af45a15-8aae-41b8-ad2e-ded2f43b09ee

---

## 12/07 Log

**What We've Built So Far**

We added a **Vintage Microphone Recording Station** — a special interactive object that records the visitor's voice and plays it back transformed to sound like a 1940s radio broadcast.

**1. Unique Interaction Flow:** Unlike other objects that play pre-recorded sounds, the microphone has its own complete experience:

| Step | Display | Audio |
|------|---------|-------|
| Pick up mic | "Vintage Mic" | Piper TTS: "Speak into the microphone after the beep!" |
| Countdown | Giant **3, 2, 1, GO!** | Beep tones (low → high) |
| Recording | "RECORDING" + countdown | (silence - listening) |
| Processing | "Processing..." | (silence) |
| Playback | "Listen!" | Transformed vintage voice |
| Done | "Done!" | (silence) |

**2. Vintage Audio Effect Chain:** We process the recorded audio through multiple effects to simulate old radio equipment:

| Effect | What It Does |
|--------|--------------|
| Bandpass Filter (300Hz-3kHz) | Cuts bass and treble (old mics had limited range) |
| Tape Hiss | Adds subtle background noise |
| Vinyl Crackle | Random pops and clicks |
| Tube Saturation | Warm soft clipping distortion |

**3. Big Centered Display:** We created new display methods specifically for the microphone with larger, centered text for better visibility:

| Method | Purpose |
|--------|---------|
| `show_mic_message()` | Two-line centered message |
| `show_mic_countdown()` | Giant countdown numbers |
| `show_mic_recording()` | Recording status with seconds remaining |

**4. Separate Interaction Path:** The microphone is completely independent from standard objects:
- No audio file needed in config
- Buttons A/B are disabled during recording
- Goes directly to idle after completion

**Code Explanation**

**1. Special Object Type**

In `config.py`, the microphone is marked with `"type": "microphone"`:

```python
# config.py
4: {
    "name": "Vintage Microphone",
    "type": "microphone",  # Special handling!
    "record_duration": 8,
},
```

**2. Branching Logic**

In `main.py`, we check the object type and branch accordingly:

```python
# main.py
if obj.get("type") == "microphone":
    # Special microphone flow (record, process, play)
    ...
else:
    # Standard flow (play audio file, show info)
    ...
```

**3. Recording with Live Countdown**

We record in 1-second chunks so the display can update:

```python
# main.py
for remaining in range(8, 0, -1):
    screen.show_mic_recording(remaining)  # Update display
    
    chunk = sd.rec(...)  # Record 1 second
    sd.wait()
    all_audio.append(chunk)
```

**4. Piper TTS for Voice Prompts**

We use Piper (local TTS) to speak the instructions:

```python
# main.py
piper_cmd = f'echo "{message}" | /home/pi/piper/piper/piper --model /home/pi/piper/en_US-lessac-medium.onnx --output-raw | aplay -r 22050 -f S16_LE -t raw -q'
subprocess.run(piper_cmd, shell=True)
```

**5. Vintage Effect Processing**

The core audio transformation in `vintage_mic.py`:

```python
# vintage_mic.py
def apply_vintage_effect(self, audio):
    # 1. Bandpass filter (300Hz - 3kHz)
    b, a = signal.butter(4, [low, high], btype='band')
    audio = signal.filtfilt(b, a, audio)
    
    # 2. Add tape hiss
    audio = audio + np.random.normal(0, 0.02, len(audio))
    
    # 3. Add crackle
    audio = audio + self._generate_crackle(len(audio))
    
    # 4. Tube saturation
    audio = np.tanh(audio * 1.5)
    
    return audio
```

**Hardware**

- **Logitech C270 Webcam** — Used as USB microphone input
- **Piper TTS** — Local text-to-speech for voice prompts
- **Pygame** — Generates countdown beep sounds

---

---

## 12/08 Log

**What We've Built So Far**

We transitioned from software development to **physical prototyping and final assembly**. The exhibit came together as a complete, presentable installation ready for the final presentation.

**1. Wiring and Assembly:** We consolidated all hardware components into the stage enclosure

**2. Object Pedestals:** Each artifact sits on a dedicated conductive pad connected to the MPR121. Copper tape on the bottom of objects creates reliable contact for lift detection.

<img width='400' src='https://github.com/user-attachments/assets/41eb02c8-9dce-4766-bd75-356d5413ae22'>

**4. Final Presentation:** We demonstrated the complete Museum of Lost Sounds exhibit to the class, showcasing:

- **Lift-to-Activate interaction** — Picking up objects triggers sounds
- **Dual-mode display** — Text info + historical action photos


**Final Look**

<img width='400' src='https://github.com/user-attachments/assets/c51b0a18-3cb8-41b7-a42e-e88e34f33de3'>



https://github.com/user-attachments/assets/811d0f92-cba1-4f89-82d6-a9697cd7b4ba


**Final System Architecture**

```
┌─────────────────────────────────────────────────────┐
│                   RASPBERRY PI                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│   │  MPR121  │    │  PiTFT   │    │  C270    │      │
│   │  Touch   │    │ Display  │    │   Mic    │      │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘      │
│        │ I2C           │ SPI           │ USB        │
│        ▼               ▼               ▼            │
│   ┌─────────┐    ┌─────────┐    ┌──────────┐        │
│   │ Objects │    │  Screen │    │ Vintage  │        │
│   │ on Pads │    │  Output │    │ Recorder │        │
│   └─────────┘    └─────────┘    └──────────┘        │
│                                                     │
│                    ┌──────────┐                     │
│                    │ Speaker  │                     │
│                    │  Output  │                     │
│                    └──────────┘                     │
└─────────────────────────────────────────────────────┘
```

**Presentation Video Showcase**



https://github.com/user-attachments/assets/e0e0c30b-bcf3-434d-ad82-36b2d025348d



https://github.com/user-attachments/assets/4ea5e067-bf37-46f9-adbc-4c65084bd401



https://github.com/user-attachments/assets/b84fa3b6-8378-492a-b7a2-c8640757a14e



https://github.com/user-attachments/assets/942e80eb-3a02-402d-aafd-929c79a14102


---

## Reflections on Process

**What We Learned**

**1. Hardware-Software Integration Takes Time:** We underestimated how much debugging would happen at the hardware-software boundary. Issues like the C270 webcam rejecting certain sample rates, emoji encoding crashes on the Pi terminal, and Piper TTS path problems weren't predictable from reading documentation alone. Building in extra time for integration testing is essential.

**2. State Machines Are Your Friend:** Early versions of our code used simple time.sleep() calls, which blocked everything. Moving to a non-blocking state machine with timestamps (unlock_time, audio_end_time, last_interaction_time) made the system responsive and professional. This pattern is worth learning early for any interactive project.

**3. Small Screens Need Design Solutions:** The 1.14" PiTFT seemed limiting at first. Instead of fighting it, we embraced it with the "window" — turning a constraint into a feature. Constraints can drive creative solutions.

**4. Test with Real Users Early:** Watching classmates interact with our exhibit revealed assumptions we didn't know we had. Some tried pressing the objects instead of lifting them. User testing should happen earlier in the process.

**What We Wish We Knew at the Start**

| Topic | What We Wish We Knew |
|-------|----------------------|
| **Audio on Pi** | USB audio devices have specific sample rate requirements — always test early |
| **TTS Options** | Piper is great but requires correct paths; espeak is simpler but sounds robotic |
| **Touch Sensing** | Copper tape quality varies — get good adhesive contact for reliable detection |
| **Wire Management** | Plan cable lengths and routing before building the enclosure |
| **Pygame + Sounddevice** | They can conflict; be careful initializing both audio systems |
| **Font Support** | Pi doesn't have many fonts by default — add custom fonts to the project folder, not the system |

---

## Group Work Distribution

### Contribution Summary

| Team Member | Contribution Areas |
|-------------|-------------------|
| **Melody Huang (yh2353)** | Coding, idea generation, wiring, interaction design, debugging |
| **Dingran Dai (dd699)** | Stage design, physical assembly, aesthetics, object curation |

### Collaboration Notes

- **Daily syncs** — We communicated regularly to align software capabilities with physical design constraints
- **Iterative process** — Software features influenced stage design
- **Parallel workstreams** — Coding and stage construction happened simultaneously, merged during final assembly
- **Joint presentation** — Both team members contributed to the final demo
