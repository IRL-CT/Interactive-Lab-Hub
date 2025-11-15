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

### 11/15 Log

**What We've Built So Far**

We have successfully created a system where:
1.  A user touches a sensor pad (connected to the **MPR121**).
2.  The `main.py` script detects this touch.
3.  It looks up the pad number in the `config.py` file.
4.  It tells the `audio_player.py` to play the correct `.mp3` sound.
5.  It loads the corresponding `.txt` file and tells the `display.py` class to show the object's name and its description on the **PiTFT screen**.
6.  The `display.py` class correctly wraps the text to fit the screen.

---

**Video Showcase**

https://github.com/user-attachments/assets/73619182-87a8-4e3f-9667-aa8d750fe627


---

**Next Steps**

The core loop works, but the user experience can be improved. Right now, a user can press multiple buttons rapidly, causing sounds to interrupt each other and the display to flash. Our next step is to manage the "state" of the exhibit and change the interaction to when users pick up the object, the device will play the sound.
