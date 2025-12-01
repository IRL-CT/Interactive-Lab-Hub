# Final Project

Using the tools and techniques you learned in this class, design, prototype and test an interactive device.

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
* 🔧 *(Optional)* A small servo animates the object for added immersion

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
| Movement *(optional)* | **9G Servo + Servo pHAT** | Small animations (e.g., typewriter arm movement) |

---

## 🛠️ Hardware Mapping

### **Input → Output Flow**

```
User touches object → MPR121 triggers →
Raspberry Pi identifies item →
Bluetooth speaker plays sound +
Mini PiTFT shows content +
LEDs light up →
(Optional) Servo animates object
```

### **Overall Mapping**

| Input Component                | Function          | Output Component  | Function           |
| ------------------------------ | ----------------- | ----------------- | ------------------ |
| MPR121                         | Touch detection   | Bluetooth Speaker | Audio playback     |
| APDS9960                       | Gesture/proximity | Mini PiTFT        | Display content    |
| Rotary Encoder / Qwiic Buttons | User navigation   | PCF8574 + LEDs    | Light feedback     |
| —                              | —                 | Servo Motor       | Optional animation |

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



