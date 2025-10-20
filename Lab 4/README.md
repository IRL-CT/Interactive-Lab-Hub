

## Lab Overview
Sachin Jojode, Nikhil Gangaram, Arya Prasad, Jaspreet Singh

### Part A
### Capacitive Sensing, a.k.a. Human-Twizzler Interaction 

Twizzler Video Link: https://youtu.be/UR29FbM2_Zg


### Part B
### More sensors

Light/Proximity/Gesture sensor (APDS-9960)
Link: https://youtu.be/EVjcOtlsp9w

Rotary Encoder
Link: https://youtu.be/T9menfbH3-I

Joystick
Link: https://youtu.be/TCmgt5xkJVs

Distance Sensor
Link: https://youtu.be/fr77xgzWXX8

### Part C
### Physical considerations for sensing

The AstroClicker is an interactive device that guides users through the night sky. The joystick serves as the primary input, allowing users to select celestial objects and control their viewing distance.
<img width="748" height="660" alt="Screen Shot 2025-10-12 at 5 56 28 PM" src="https://github.com/user-attachments/assets/eaf7d708-e6ee-4bf3-9271-d9631242041c" />

Our next concept, the City Explorer, is a device that assists users in exploring new cities and uncovering hidden spots in places they already know. Using the joystick, users can select their next destination, and the device automatically records their travel history.
<img width="711" height="716" alt="Screen Shot 2025-10-12 at 5 57 38 PM" src="https://github.com/user-attachments/assets/7d548b3d-c66a-41e1-97a9-1baaacc21bb0" />

Our next concept, Remote Play, is designed to let users engage with their pets remotely. The device integrates a joystick input with a gyroscopic ball that responds to the user’s movements and commands.
<img width="746" height="733" alt="Screen Shot 2025-10-12 at 5 58 24 PM" src="https://github.com/user-attachments/assets/607ca226-e741-4005-9cd8-05cf8aaa5243" />

Our next concept, Flashcards, takes inspiration from platforms like Anki that use flashcards to support learning. This version introduces a joystick-based input system, creating a more interactive and engaging study experience.
<img width="744" height="752" alt="Screen Shot 2025-10-12 at 5 59 27 PM" src="https://github.com/user-attachments/assets/8f798fee-40d6-4291-b042-8ee2ad1a7c8a" />

Our final concept is the Store Navigator:  a device designed to help users find their way through complex grocery store aisles. It comes preloaded with the store’s layout, allowing users to locate aisles and check if their desired items are in stock.
<img width="727" height="725" alt="Screen Shot 2025-10-12 at 6 00 28 PM" src="https://github.com/user-attachments/assets/365ceee8-f86f-4d7c-8212-2ae5a2204b54" />

Some key questions that emerged from these sketches include:

- What problem does the device most effectively solve for users, and how can we clearly communicate that value?
- How can we refine the physical form and interface to make interactions feel natural and satisfying?
- What sensory feedback (visual, auditory, or haptic) could enhance the user’s sense of connection with the device?
- How can the technology within the device be optimized for accuracy, responsiveness, and durability in real-world conditions?
- In what ways can the overall experience be personalized to different types of users or environments?

After evaluating all the ideas, we’ve chosen to continue developing the **AstroClicker**.


### Part D
### Physical considerations for displaying information and housing parts

Astroclicker Designs:
<img width="935" height="600" alt="Screen Shot 2025-10-12 at 6 17 46 PM" src="https://github.com/user-attachments/assets/7b26d344-fdd8-41c8-81cc-27c0111f8f1e" />
<img width="894" height="653" alt="Screen Shot 2025-10-12 at 6 17 55 PM" src="https://github.com/user-attachments/assets/cd80aa19-c396-473b-a703-82054195534b" />
<img width="854" height="730" alt="Screen Shot 2025-10-12 at 6 08 02 PM" src="https://github.com/user-attachments/assets/a630e74a-7279-4e8f-8b24-b3d8ddca195d" />
<img width="1059" height="575" alt="Screen Shot 2025-10-12 at 6 08 12 PM" src="https://github.com/user-attachments/assets/6dd2ce10-5d82-4469-b56c-fbe873b4bedc" />
<img width="912" height="618" alt="Screen Shot 2025-10-12 at 6 08 28 PM" src="https://github.com/user-attachments/assets/ac11edc8-26c5-4739-9ae5-a8ec4d19f249" />

For our first design, which we based on Prototype 1, we focused on making the device comfortable and practical. Since it’s handheld, we placed the joystick in a spot that feels natural to use. We made sure the speaker faces the user so the sound doesn’t get muffled. We also planned space for ventilation to keep the Raspberry Pi from overheating, along with room for a battery. When building our cardboard prototype, we included these ideas using an Altoids can as a placeholder for the battery and adding a top cutout for airflow around the Raspberry Pi.

Astroclicker Prototype Video Link: https://youtube.com/shorts/sQySwPO-nW0?feature=share


# LAB PART 2

### Part 2

Following exploration and reflection from Part 1, complete the "looks like," "works like" and "acts like" prototypes for your design, reiterated below.

### Part E

Software:

* We began prototyping the AstroClicker software, located in the astro_clicker_demo.py file.
* Our main design goal was to make the program user-friendly and intuitive, while avoiding an overwhelming or restrictive experience.
* After multiple rounds of prototyping and refinement, we finalized the following code structure:

1. Initialization and Data Structure

* Imports essential libraries for hardware interaction, timing, subprocess execution, and argument parsing.
* The speak_text function handles text-to-speech using the external espeak program and logs all outputs to the console, regardless of the current OUTPUT_MODE (speaker or silent).

Celestial data is divided into three layers based on their distance from Earth:

* Layer 0 (Closest): CONSTELLATION_DATA
* Layer 1 (Intermediate): SOLAR_SYSTEM_DATA
* Layer 2 (Farthest): DEEP_SKY_DATA

------------------------------------------------------------------------

2. The SkyNavigator State Machine

* The SkyNavigator class manages the user’s state, tracking:
* The layer_index (starting at 1, representing the Solar System).
* Which objects have been viewed, using a list called unseen_targets.

The _set_new_target() method:
* Randomly selects an available object from the current layer.
* Resets that layer’s availability once all objects have been viewed.
* The move(direction) method updates the state based on joystick input:
* ‘up’ / ‘down’: Adjusts layer_index to zoom in or out, switching between the three celestial layers.
* ‘left’ / ‘right’: Keeps the user within the current layer and selects a new random target.
* Built-in boundary checks prevent movement beyond Layer 0 or Layer 2.
* After every successful movement, the new location or target is announced using the speak_text function.


------------------------------------------------------------------------

3.
* The runExample function initializes the joystick and the SkyNavigator.
* A welcome message and the initial target's details are spoken aloud.
* An infinite while loop continuously reads the joystick's horizontal (x_val), vertical (y_val), and button state. It uses a **debounce timer** (MOVE_DEBOUNCE_TIME) to prevent rapid, accidental inputs.

| Input Action | Resulting Action | Output/Narration |
| :--- | :--- | :--- |
| **Joystick Button Click (Release)** | Stays at current target. | Reads the **`name`** and **`fact`** of the current target, followed by a prompt for the next action. |
| **Joystick Up** (Y-Value > 600) | Calls `navigator.move('up')` (Zoom Out/Farther). | Announces the zoom-out and the new target's name/type, or a boundary message. |
| **Joystick Down** (Y-Value < 400) | Calls `navigator.move('down')` (Zoom In/Closer). | Announces the zoom-in and the new target's name/type, or a boundary message. |
| **Joystick Left** (X-Value > 600) | Calls `navigator.move('left')` (Scan/New Target). | Announces a scan left and the new target's name/type. |
| **Joystick Right** (X-Value < 400) | Calls `navigator.move('right')` (Scan/New Target). | Announces a scan right and the new target's name/type. |

------------------------------------------------------------------------

4.
* The main()  function uses the argparse module to allow the user to optionally specify the output mode (mode speaker or mode silent) when running the script.
* The program can be cleanly exited by pressing **Ctrl+C**.

<img width="531" height="532" alt="Screen Shot 2025-10-19 at 9 55 23 PM" src="https://github.com/user-attachments/assets/8f02c490-1c40-485b-93a1-1369a3db61a0" />

Hardware

* We began developing the hardware prototype, focusing on the following main considerations:
* The device should be handheld, with the joystick positioned in an ergonomic spot for comfortable use.
* The speaker should face the user to ensure clear audio output and prevent muffled sound.
* The Raspberry Pi should have proper ventilation to avoid overheating, along with space for a battery to power the system.

Most of these considerations were carried over from the cardboard prototype, though we made several design adjustments to improve ergonomics and overall usability.

Below are images of the updated hardware prototype.

<img width="479" height="640" alt="Screen Shot 2025-10-19 at 9 56 42 PM" src="https://github.com/user-attachments/assets/f4aa2577-038f-418c-946d-f8771ce6a0ca" />
<img width="472" height="646" alt="Screen Shot 2025-10-19 at 9 56 48 PM" src="https://github.com/user-attachments/assets/85040e3b-4a8d-4f0f-9633-1a17303ec1b6" />
<img width="475" height="587" alt="Screen Shot 2025-10-19 at 9 56 56 PM" src="https://github.com/user-attachments/assets/414f6460-9a2e-482d-8b35-5af652287d54" />


### Part F

Here is our final video with a walkthrough of the AstroClicker prototype in both software and hardware:
https://youtu.be/bRyzQZdn2rA


### AI Contributions 

Throughout this lab, we got help from Gemini with: 

* Generating "final" images throughout the lab. We would often sketch a rough idea on paper, and then use Gemini to refine it into a presentable image. 
* Developing and documenting the code for the AstroClicker prototype.

Everything else (ideating, eliciting feedback, designing and building the prototypes) was done by ourselves.
