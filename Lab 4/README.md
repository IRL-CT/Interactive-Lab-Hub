# Ph-UI!!!

<details>
	<summary><strong>Instructions for Students (Click to Expand)</strong></summary>
  
	**Submission Cleanup Reminder:**
	- This README.md contains extra instructional text for guidance.
	- Before submitting, remove all instructional text and example prompts from this file.
	- You may delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
	- Your final submission should be neat, focused on your own work, and easy to read for grading.
  
	This helps ensure your README.md is clear, professional, and uniquely yours!
</details>

---

## Lab 4 Deliverables

### Part 1 (Week 1)
**Submit the following for Part 1:**  
*️⃣ **A. Capacitive Sensing**
	- Photos/videos of your Twizzler (or other object) capacitive sensor setup
	- Code and terminal output showing touch detection

*️⃣ **B. More Sensors**
	- Photos/videos of each sensor tested (light/proximity, rotary encoder, joystick, distance sensor)
	- Code and terminal output for each sensor

*️⃣ **C. Physical Sensing Design**
	- 5 sketches of different ways to use your chosen sensor
	- Written reflection: questions raised, what to prototype
	- Pick one design to prototype and explain why

*️⃣ **D. Display & Housing**
	- 5 sketches for display/button/knob positioning
	- Written reflection: questions raised, what to prototype
	- Pick one display design to integrate
	- Rationale for design
	- Photos/videos of your cardboard prototype

---

### Part 2 (Week 2)
**Submit the following for Part 2:**  
*️⃣ **E. Multi-Device Demo**
	- Code and video for your multi-input multi-output demo (e.g., chaining Qwiic buttons, servo, GPIO expander, etc.)
	- Reflection on interaction effects and chaining

*️⃣ **F. Final Documentation**
	- Photos/videos of your final prototype
	- Written summary: what it looks like, works like, acts like
	- Reflection on what you learned and next steps

---

## Lab Overview
**NAMES OF COLLABORATORS HERE**


For lab this week, we focus both on sensing, to bring in new modes of input into your devices, as well as prototyping the physical look and feel of the device. You will think about the physical form the device needs to perform the sensing as well as present the display or feedback about what was sensed. 

## Part 1 Lab Preparation

### Get the latest content:
As always, pull updates from the class Interactive-Lab-Hub to both your Pi and your own GitHub repo. As we discussed in the class, there are 2 ways you can do so:


Option 1: On the Pi, `cd` to your `Interactive-Lab-Hub`, pull the updates from upstream (class lab-hub) and push the updates back to your own GitHub repo. You will need the personal access token for this.
```
pi@ixe00:~$ cd Interactive-Lab-Hub
pi@ixe00:~/Interactive-Lab-Hub $ git pull upstream Fall2025
pi@ixe00:~/Interactive-Lab-Hub $ git add .
pi@ixe00:~/Interactive-Lab-Hub $ git commit -m "get lab4 content"
pi@ixe00:~/Interactive-Lab-Hub $ git push
```

Option 2: On your own GitHub repo, [create pull request](https://github.com/FAR-Lab/Developing-and-Designing-Interactive-Devices/blob/2021Fall/readings/Submitting%20Labs.md) to get updates from the class Interactive-Lab-Hub. After you have latest updates online, go on your Pi, `cd` to your `Interactive-Lab-Hub` and use `git pull` to get updates from your own GitHub repo.

Option 3: (preferred) use the Github.com interface to update the changes.

### Start brainstorming ideas by reading: 

* [What do prototypes prototype?](https://www.semanticscholar.org/paper/What-do-Prototypes-Prototype-Houde-Hill/30bc6125fab9d9b2d5854223aeea7900a218f149)
* [Paper prototyping](https://www.uxpin.com/studio/blog/paper-prototyping-the-practical-beginners-guide/) is used by UX designers to quickly develop interface ideas and run them by people before any programming occurs. 
* [Cardboard prototypes](https://www.youtube.com/watch?v=k_9Q-KDSb9o) help interactive product designers to work through additional issues, like how big something should be, how it could be carried, where it would sit. 
* [Tips to Cut, Fold, Mold and Papier-Mache Cardboard](https://makezine.com/2016/04/21/working-with-cardboard-tips-cut-fold-mold-papier-mache/) from Make Magazine.
* [Surprisingly complicated forms](https://www.pinterest.com/pin/50032245843343100/) can be built with paper, cardstock or cardboard.  The most advanced and challenging prototypes to prototype with paper are [cardboard mechanisms](https://www.pinterest.com/helgangchin/paper-mechanisms/) which move and change. 
* [Dyson Vacuum Cardboard Prototypes](http://media.dyson.com/downloads/JDF/JDF_Prim_poster05.pdf)
<p align="center"><img src="https://dysonthedesigner.weebly.com/uploads/2/6/3/9/26392736/427342_orig.jpg"  width="200" > </p>

### Gathering materials for this lab:

* Cardboard (start collecting those shipping boxes!)
* Found objects and materials--like bananas and twigs.
* Cutting board
* Cutting tools
* Markers


(We do offer shared cutting board, cutting tools, and markers on the class cart during the lab, so do not worry if you don't have them!)

## Deliverables \& Submission for Lab 4

The deliverables for this lab are, writings, sketches, photos, and videos that show what your prototype:
* "Looks like": shows how the device should look, feel, sit, weigh, etc.
* "Works like": shows what the device can do.
* "Acts like": shows how a person would interact with the device.

For submission, the readme.md page for this lab should be edited to include the work you have done:
* Upload any materials that explain what you did, into your lab 4 repository, and link them in your lab 4 readme.md.
* Link your Lab 4 readme.md in your main Interactive-Lab-Hub readme.md. 
* Labs are due on Mondays, make sure to submit your Lab 4 readme.md to Canvas.


## Lab Overview

A) [Capacitive Sensing](#part-a)

B) [OLED screen](#part-b) 

C) [Paper Display](#part-c)

D) [Materiality](#part-d)

E) [Servo Control](#part-e)

F) [Record the interaction](#part-f)


## The Report (Part 1: A-D, Part 2: E-F)

### Quick Start: Python Environment Setup

1. **Create and activate a virtual environment in Lab 4:**
	```bash
	cd ~/Interactive-Lab-Hub/Lab\ 4
	python3 -m venv .venv
	source .venv/bin/activate
	```
2. **Install all Lab 4 requirements:**
	```bash
	pip install -r requirements2025.txt
	```
3. **Check CircuitPython Blinka installation:**
	```bash
	python blinkatest.py
	```
	If you see "Hello blinka!", your setup is correct. If not, follow the troubleshooting steps in the file or ask for help.

### Part A
### Capacitive Sensing, a.k.a. Human-Twizzler Interaction 

We want to introduce you to the [capacitive sensor](https://learn.adafruit.com/adafruit-mpr121-gator) in your kit. It's one of the most flexible input devices we are able to provide. At boot, it measures the capacitance on each of the 12 contacts. Whenever that capacitance changes, it considers it a user touch. You can attach any conductive material. In your kit, you have copper tape that will work well, but don't limit yourself! In the example below, we use Twizzlers--you should pick your own objects.


<p float="left">
<img src="https://cdn-learn.adafruit.com/guides/cropped_images/000/003/226/medium640/MPR121_top_angle.jpg?1609282424" height="150" />
 
</p>

Plug in the capacitive sensor board with the QWIIC connector. Connect your Twizzlers with either the copper tape or the alligator clips (the clips work better). Install the latest requirements from your working virtual environment:

These Twizzlers are connected to pads 6 and 10. When you run the code and touch a Twizzler, the terminal will print out the following

```
(circuitpython) pi@ixe00:~/Interactive-Lab-Hub/Lab 4 $ python cap_test.py 
Twizzler 10 touched!
Twizzler 6 touched!
```

### Part B
### More sensors

#### Light/Proximity/Gesture sensor (APDS-9960)

We here want you to get to know this awesome sensor [Adafruit APDS-9960](https://www.adafruit.com/product/3595). It is capable of sensing proximity, light (also RGB), and gesture! 
 
<img src="https://cdn-shop.adafruit.com/970x728/3595-06.jpg" width=200>
 

Connect it to your pi with Qwiic connector and try running the three example scripts individually to see what the sensor is capable of doing!

```
(circuitpython) pi@ixe00:~/Interactive-Lab-Hub/Lab 4 $ python proximity_test.py
...
(circuitpython) pi@ixe00:~/Interactive-Lab-Hub/Lab 4 $ python gesture_test.py
...
(circuitpython) pi@ixe00:~/Interactive-Lab-Hub/Lab 4 $ python color_test.py
...
```

You can go the the [Adafruit GitHub Page](https://github.com/adafruit/Adafruit_CircuitPython_APDS9960) to see more examples for this sensor!

#### Rotary Encoder 

A rotary encoder is an electro-mechanical device that converts the angular position to analog or digital output signals. The [Adafruit rotary encoder](https://www.adafruit.com/product/4991#technical-details) we ordered for you came with separate breakout board and encoder itself, that is, they will need to be soldered if you have not yet done so! We will be bringing the soldering station to the lab class for you to use, also, you can go to the MakerLAB to do the soldering off-class. Here is some [guidance on soldering](https://learn.adafruit.com/adafruit-guide-excellent-soldering/preparation) from Adafruit. When you first solder, get someone who has done it before (ideally in the MakerLAB environment). It is a good idea to review this material beforehand so you know what to look at.

<p float="left">

   
<img src="https://cdn-shop.adafruit.com/970x728/377-02.jpg" height="200" />
<img src="https://cdn-shop.adafruit.com/970x728/4991-09.jpg" height="200">
</p>

Connect it to your pi with Qwiic connector and try running the example script, it comes with an additional button which might be useful for your design!

```
(circuitpython) pi@ixe00:~/Interactive-Lab-Hub/Lab 4 $ python encoder_test.py
```

You can go to the [Adafruit Learn Page](https://learn.adafruit.com/adafruit-i2c-qt-rotary-encoder/python-circuitpython) to learn more about the sensor! The sensor actually comes with an LED (neo pixel): Can you try lighting it up? 

#### Joystick 


A [joystick](https://www.sparkfun.com/products/15168) can be used to sense and report the input of the stick for it pivoting angle or direction. It also comes with a button input!

<p float="left">
<img src="https://cdn.sparkfun.com//assets/parts/1/3/5/5/8/15168-SparkFun_Qwiic_Joystick-01.jpg" height="200" />
</p>

Connect it to your pi with Qwiic connector and try running the example script to see what it can do!

```
(circuitpython) pi@ixe00:~/Interactive-Lab-Hub/Lab 4 $ python joystick_test.py
```

You can go to the [SparkFun GitHub Page](https://github.com/sparkfun/Qwiic_Joystick_Py) to learn more about the sensor!

#### Distance Sensor


Earlier we have asked you to play with the proximity sensor, which is able to sense objects within a short distance. Here, we offer [Sparkfun Proximity Sensor Breakout](https://www.sparkfun.com/products/15177), With the ability to detect objects up to 20cm away.

<p float="left">
<img src="https://cdn.sparkfun.com//assets/parts/1/3/5/9/2/15177-SparkFun_Proximity_Sensor_Breakout_-_20cm__VCNL4040__Qwiic_-01.jpg" height="200" />

</p>

Connect it to your pi with Qwiic connector and try running the example script to see how it works!

```
(circuitpython) pi@ixe00:~/Interactive-Lab-Hub/Lab 4 $ python qwiic_distance.py
```

You can go to the [SparkFun GitHub Page](https://github.com/sparkfun/Qwiic_Proximity_Py) to learn more about the sensor and see other examples

### Part C
### Physical considerations for sensing


Usually, sensors need to be positioned in specific locations or orientations to make them useful for their application. Now that you've tried a bunch of the sensors, pick one that you would like to use, and an application where you use the output of that sensor for an interaction. For example, you can use a distance sensor to measure someone's height if you position it overhead and get them to stand under it.


**\*\*\*Draw 5 sketches of different ways you might use your sensor, and how the larger device needs to be shaped in order to make the sensor useful.\*\*\***

### We chose the distance sensor

**1. Automatic Lamp** 

A desk lamp that will automatically turn on the light if your hand is placed below the light (for a certain distance), for example, while writing or typing. Pull your hand away, and it dims. The sensor is mounted on the underside front edge of the lamp head, pointing down and slightly forward. This position allows it to detect hands on the desk surface below while keeping the lamp's light unobstructed.

<img src="https://github.com/user-attachments/assets/862fd07f-8bb8-491e-95c4-d700211fc40b" width="600">


**2. Monster Box** 

This design features a classic treasure-chest-style box. A cute, fluffy creature is attached to the lid from the inside. When no hand is near (distance > 5cm), the lid is open, and the creature peeks out. The distance sensor is flush-mounted on the front face of the box. When a hand approaches (distance < 5cm), the servo pulls the lid shut, making the creature "hide."


<img src="https://github.com/user-attachments/assets/1f816097-3146-4aba-8a15-ff357d96ddb8" width="600"/>

**3. The Interactive Picture Frame** 

A special frame for art. The distance sensor is mounted below the picture or near a specific character/object on the page, pointing outwards. When someone points their finger at that picture (getting close to the sensor's detection range) for a certain amount of time, it triggers an associated audio clip (e.g., a character's voice, a sound effect, or an introduction)

<img src="https://github.com/user-attachments/assets/21fced76-f58c-4b39-94fd-f25c1f9373cb" width="600"/>

**4. The Personal Space Detector** 

A small, subtle device that sits on your desk or on the edge of a personal workspace. The distance sensor is aimed outwards, creating an invisible "personal bubble" zone. If someone (or something) breaches that zone (e.g., comes too close while you're focused), it could trigger a gentle, non-alarming notification: a soft chime, a subtle LED color change, or a vibration.

<img src="https://github.com/user-attachments/assets/3d990cb3-6e1a-4069-9916-331720d9a0c0" width="600"/>

**5. Mirror, Mirror on the Wall** 

A human-sized dressing mirror that uses a distance sensor to react to your presence. As a person approaches, a discreetly placed distance sensor detects their presence. This triggers a soft, diffused LED light strip hidden behind the mirror's border, causing the frame to glow and illuminate the user. When no one is near, the lights remain off, saving energy and maintaining a minimalist appearance.

<img src="https://github.com/user-attachments/assets/668b7a2b-8cdd-43fe-a7f5-776907852b80" width="600"/>


**\*\*\*What are some things these sketches raise as questions? What do you need to physically prototype to understand how to anwer those questions?\*\*\***

**1. Automatic Lamp:** Should the sensor be on the base, pointing up, or in the lampshade, pointing down? How does that choice change the user's interaction?

**2. Monster Box:** How can we design the box to hide the sensor and servo mechanism while still inviting someone to interact with it? How to open the lid while popping up the monster?

**3. The Interactive Picture Frame:** How can the picture frame or book page be designed to hide the sensor and wiring, yet still guide the user to the "interactive" spots where they should point their finger?

**4. The Personal Space Detector:** How can the device be designed to blend into a workspace, making the sensor almost invisible, while still effectively defining and detecting breaches of a "personal space" boundary? How does the device's orientation influence the shape of the detection zone?

**5. Mirror, Mirror on the Wall:** Where is the optimal position for the distance sensor? If placed at the bottom, will it reliably detect people of different heights? If at the top, will it be too far away?

**\*\*\*Pick one of these designs to prototype.\*\*\***

## The Shy Creature Box

<img src="https://github.com/user-attachments/assets/c1fc7ca5-0244-4df6-b596-d0941596a756" width="600"/>

**Physical Form ("Looks Like"):**
The device is housed in a rectangular cardboard box, creating a small stage-like environment. The front panel features clean cutouts for the input components, giving it the feel of an interactive display. The main character is a small, whimsical figurine with a pink bow, positioned to peek over the front edge of the box.

**Components & Interaction ("Works Like"):**

Primary Input: A distance sensor is prominently mounted on the front-right of the box. Its purpose is to detect when a user's hand or an object comes within a close range.

Mechanism: A servo motor, visible inside the box, is connected to the duck figurine. This motor acts as the "muscle" that makes the creature move.

Core Interaction: The intended behavior is that when the creature is peeking out, and the distance sensor detects an approaching hand, the servo motor will activate. It will quickly pull the figurine down behind the front wall, making the creature appear "shy" and hide from the user.

Secondary Input: A joystick is mounted on the front-left, suggesting the potential for additional modes of interaction, such as manually controlling the creature or navigating a menu on a display (not yet implemented).


### Part D
### Physical considerations for displaying information and housing parts



Here is a Pi with a paper faceplate on it to turn it into a display interface:


<img src="https://github.com/FAR-Lab/Developing-and-Designing-Interactive-Devices/blob/2020Fall/images/paper_if.png?raw=true"  width="250"/>


This is fine, but the mounting of the display constrains the display location and orientation a lot. Also, it really only works for applications where people can come and stand over the Pi, or where you can mount the Pi to the wall.

Here is another prototype for a paper display:

<img src="https://github.com/FAR-Lab/Developing-and-Designing-Interactive-Devices/blob/2020Fall/images/b_box.png?raw=true"  width="250"/>


Your kit includes these [SparkFun Qwiic OLED screens](https://www.sparkfun.com/products/17153). These use less power than the MiniTFTs you have mounted on the GPIO pins of the Pi, but, more importantly, they can be more flexibly mounted elsewhere on your physical interface. The way you program this display is almost identical to the way you program a  Pi display. Take a look at `oled_test.py` and some more of the [Adafruit examples](https://github.com/adafruit/Adafruit_CircuitPython_SSD1306/tree/master/examples).

<p float="left">
<img src="https://cdn.sparkfun.com//assets/parts/1/6/1/3/5/17153-SparkFun_Qwiic_OLED_Display__0.91_in__128x32_-01.jpg" height="200" />

</p>


It holds a Pi and usb power supply, and provides a front stage on which to put writing, graphics, LEDs, buttons or displays.

This design can be made by scoring a long strip of corrugated cardboard of width X, with the following measurements:

| Y height of box <br> <sub><sup>- thickness of cardboard</sup></sub> | Z  depth of box <br><sub><sup>- thickness of cardboard</sup></sub> | Y height of box  | Z  depth of box | H height of faceplate <br><sub><sup>* * * * * (don't make this too short) * * * * *</sup></sub>|
| --- | --- | --- | --- | --- | 

Fold the first flap of the strip so that it sits flush against the back of the face plate, and tape, velcro or hot glue it in place. This will make a H x X interface, with a box of Z x X footprint (which you can adapt to the things you want to put in the box) and a height Y in the back. 

Here is an example:

<img src="https://github.com/FAR-Lab/Developing-and-Designing-Interactive-Devices/blob/2020Fall/images/horoscope.png?raw=true"  width="250"/>

Think about how you want to present the information about what your sensor is sensing! Design a paper display for your project that communicates the state of the Pi and a sensor. Ideally you should design it so that you can slide the Pi out to work on the circuit or programming, and then slide it back in and reattach a few wires to be back in operation.
 
**\*\*\*Sketch 5 designs for how you would physically position your display and any buttons or knobs needed to interact with it.\*\*\***

**1.Classic Treasure Chest**

**Looks Like:**

A rectangular treasure chest shape with a small decorative latch on the front. The distance sensor is hidden under the latch area. When the lid is open, the creature peeks out; when the lid closes, it completely hides inside.

**Works Like:**

- The distance sensor detects when a hand comes near.
- When a hand approaches → the servo motor closes the lid.
- When the hand moves away → the lid slowly opens, and the creature peeks out again.

<img src="https://github.com/user-attachments/assets/707354e8-a950-4ff0-ab1a-2db33e87f9b8"  width="400"/>


**2. Stage Box**

**Looks Like:**

An open-front “mini stage” box where the creature sits in the center. A paper curtain is attached to the top and can move up and down to hide or reveal the creature.

**Works Like:**

- The distance sensor is mounted on the right side of the stage frame.
- When someone approaches → the servo pulls the curtain down, hiding the creature.
- When the person moves away → the curtain rises, revealing the creature again.

<img src="https://github.com/user-attachments/assets/e40bef64-18be-4032-9582-f2bef71f2e10"  width="400"/>


**3. Peek-A-Boo Dome**

**Looks Like:**

A half-sphere or dome-shaped cover made of paper or transparent plastic, with the creature inside. The base holds the distance sensor and servo motor.

**Works Like:**

- The distance sensor is located on the front of the base.
- When the hand approaches → the servo pulls the creature down into the dome.
- When the hand moves away → the creature rises again to peek out.

<img src="https://github.com/user-attachments/assets/d3bc4a39-86e2-4d8d-8eb1-4de55f6671ed" width="400"/>


**4. Drawer Creature**

**Looks Like:**

A drawer-like box, with the creature hiding inside the sliding drawer. The distance sensor and a manual knob are mounted on the front face.

**Works Like:**

- The distance sensor detects proximity.
- When someone comes close → the servo retracts the drawer.
- When the person moves away → the drawer slides out again, letting the creature peek out.
- The knob can adjust movement speed or “mood mode” (slow = shy, fast = startled).

<img src="https://github.com/user-attachments/assets/2efe7b21-1d55-4ceb-bf02-61d44e3eec56" width="400"/>



**5. Curious Window Creature**

**Looks Like:**

A small “window box” or “house façade” made of cardboard, with a window cutout on the front. Behind the window sits the creature. Curtains or small shutters can open and close using the servo motor. The distance sensor is placed above or below the window frame.

**Works Like:**

- When no one is nearby → the window shutters are open, and the creature is visible, calmly looking out.
- When someone approaches → the distance sensor triggers the servo to close the shutters, making the creature “hide.”
- When the person moves away → the shutters reopen, and the creature peeks out again.
- A knob could control “mood mode” — adjusting how fast the shutters open (slow = shy, fast = startled).

<img src="https://github.com/user-attachments/assets/057ce4db-055b-4ce8-a9f5-87b459285859" width="400"/>

**\*\*\*What are some things these sketches raise as questions? What do you need to physically prototype to understand how to anwer those questions?\*\*\***

**1. Classic Treasure Chest:** Should the creature be attached to the lid or fixed inside for better stability?
**2. Stage Box:** How close to the front edge should the creature be placed to look natural?
**3. Peek-A-Boo Dome:** Should the distance sensor be tilted upward for better detection?
**4. Drawer Creature:** Should the sensor be mounted on the drawer front or the outer frame?
**5. Curious Window Creature:** How much space inside the box is needed for the servo linkage to move smoothly?


**\*\*\*Pick one of these display designs to integrate into your prototype.\*\*\***

We chose to prototype the "Classic Monster Box" design. This design is inspired by the "Curious Window Creature" concept but uses a simpler, more direct open-box form factor that is ideal for initial prototyping. It allows us to focus on the core interaction of a creature hiding in response to a sensor.


**\*\*\*Explain the rationale for the design.\*\*\*** (e.g. Does it need to be a certain size or form or need to be able to be seen from a certain distance?)


The rationale for choosing the simple cardboard box design was driven by the goals of rapid and effective prototyping:

**Feasibility and Speed:** A rectangular box is significantly faster and easier to construct from cardboard than a more complex house-shaped façade. This allowed us to quickly create a sturdy housing and move on to testing the electronics and the core interaction.

**Size and Scale:** The prototype is sized to be a compact desktop object. Its dimensions are primarily dictated by the need to comfortably house the internal components (Raspberry Pi, servo, wiring) while remaining small enough to not be obtrusive. This smaller scale is also a direct response to the distance sensor's effective range of about 20cm; the form factor encourages the user to bring their hand close, ensuring they are well within the sensor's detection zone for a reliable interaction.

**Viewing Distance:** This device is designed for close, intimate interaction, meant to be viewed from no more than a few feet away. The creature's hiding motion is a small, subtle action that would be lost from across a room. Furthermore, the use of the small OLED screen to display status messages like "Hiding!" requires the user to be close enough to read the text, reinforcing its function as a personal, one-on-one interactive experience rather than a public display.


**\*\*\*Document your rough prototype.\*\*\***

<img src="https://github.com/user-attachments/assets/96e55e56-79f5-45e0-8e9f-576cec14a891" width="400"/>

**Materials:** The prototype is constructed from a single piece of folded corrugated cardboard, forming a rectangular, open-top box. The material is lightweight yet rigid enough to support the components. The cutouts for the sensor, display, and joystick are done by hand, which is appropriate for a rapid, low-fidelity prototype.

**Components and Layout:** The front panel is the primary user interface and is laid out with three distinct components:

**Distance Input:** A small distance sensor is mounted on the right side. This is the main input for the hiding interaction, detecting when a user's hand approaches.

**Input (Left):** A joystick is mounted on the left side, providing a potential secondary input for future features like manual control or mode selection.

**Output (Center):** A small OLED screen is centrally located. This display is intended to provide real-time feedback about the creature's state, such as displaying the distance value from the sensor or showing text like "Hiding!" or "All Clear!".

**Mechanism (Internal):** A servo motor is mounted inside the box and connected to the duck figurine. When triggered, it pulls the creature down, making it disappear from view behind the front wall. The Raspberry Pi and all associated wiring are housed openly inside for easy access.

**Interaction Flow:** The intended interaction is that the creature starts in a visible, "peeking" state. As a user brings their hand toward the distance sensor, the OLED screen will update with the creature's status, and the servo motor will activate, pulling the creature down into the box in a "shy" hiding motion. When the hand is removed, the creature will return to its original position.

# LAB PART 2

### Part 2

Following exploration and reflection from Part 1, complete the "looks like," "works like" and "acts like" prototypes for your design, reiterated below.



### Part E

#### Chaining Devices and Exploring Interaction Effects

For Part 2, you will design and build a fun interactive prototype using multiple inputs and outputs. This means chaining Qwiic and STEMMA QT devices (e.g., buttons, encoders, sensors, servos, displays) and/or combining with traditional breadboard prototyping (e.g., LEDs, buzzers, etc.).

**Your prototype should:**
- Combine at least two different types of input and output devices, inspired by your physical considerations from Part 1.
- Be playful, creative, and demonstrate multi-input/multi-output interaction.

**Document your system with:**
- Code for your multi-device demo
- Photos and/or video of the working prototype in action
- A simple interaction diagram or sketch showing how inputs and outputs are connected and interact
- Written reflection: What did you learn about multi-input/multi-output interaction? What was fun, surprising, or challenging?

**Questions to consider:**
- What new types of interaction become possible when you combine two or more sensors or actuators?
- How does the physical arrangement of devices (e.g., where the encoder or sensor is placed) change the user experience?
- What happens if you use one device to control or modulate another (e.g., encoder sets a threshold, sensor triggers an action)?
- How does the system feel if you swap which device is "primary" and which is "secondary"?

Try chaining different combinations and document what you discover!

See encoder_accel_servo_dashboard.py in the Lab 4 folder for an example of chaining together three devices.

**`Lab 4/encoder_accel_servo_dashboard.py`**

#### Using Multiple Qwiic Buttons: Changing I2C Address (Physically & Digitally)

If you want to use more than one Qwiic Button in your project, you must give each button a unique I2C address. There are two ways to do this:

##### 1. Physically: Soldering Address Jumpers

On the back of the Qwiic Button, you'll find four solder jumpers labeled A0, A1, A2, and A3. By bridging these with solder, you change the I2C address. Only one button on the chain can use the default address (0x6F).

**Address Table:**

| A3 | A2 | A1 | A0 | Address (hex) |
|----|----|----|----|---------------|
|  0 |  0 |  0 |  0 |    0x6F       |
|  0 |  0 |  0 |  1 |    0x6E       |
|  0 |  0 |  1 |  0 |    0x6D       |
|  0 |  0 |  1 |  1 |    0x6C       |
|  0 |  1 |  0 |  0 |    0x6B       |
|  0 |  1 |  0 |  1 |    0x6A       |
|  0 |  1 |  1 |  0 |    0x69       |
|  0 |  1 |  1 |  1 |    0x68       |
|  1 |  0 |  0 |  0 |    0x67       |
| ...| ...| ...| ... |     ...      |

For example, if you solder A0 closed (leave A1, A2, A3 open), the address becomes 0x6E.

**Soldering Tips:**
- Use a small amount of solder to bridge the pads for the jumper you want to close.
- Only one jumper needs to be closed for each address change (see table above).
- Power cycle the button after changing the jumper.

##### 2. Digitally: Using Software to Change Address

You can also change the address in software (temporarily or permanently) using the example script `qwiic_button_ex6_changeI2CAddress.py` in the Lab 4 folder. This is useful if you want to reassign addresses without soldering.

Run the script and follow the prompts:
```bash
python qwiic_button_ex6_changeI2CAddress.py
```
Enter the new address (e.g., 5B for 0x5B) when prompted. Power cycle the button after changing the address.

**Note:** The software method is less foolproof and you need to make sure to keep track of which button has which address!


##### Using Multiple Buttons in Code

After setting unique addresses, you can use multiple buttons in your script. See these example scripts in the Lab 4 folder:

- **`qwiic_1_button.py`**: Basic example for reading a single Qwiic Button (default address 0x6F). Run with:
	```bash
	python qwiic_1_button.py
	```

- **`qwiic_button_led_demo.py`**: Demonstrates using two Qwiic Buttons at different addresses (e.g., 0x6F and 0x6E) and controlling their LEDs. Button 1 toggles its own LED; Button 2 toggles both LEDs. Run with:
	```bash
	python qwiic_button_led_demo.py
	```

Here is a minimal code example for two buttons:
```python
import qwiic_button

# Default button (0x6F)
button1 = qwiic_button.QwiicButton()
# Button with A0 soldered (0x6E)
button2 = qwiic_button.QwiicButton(0x6E)

button1.begin()
button2.begin()

while True:
		if button1.is_button_pressed():
				print("Button 1 pressed!")
		if button2.is_button_pressed():
				print("Button 2 pressed!")
```

For more details, see the [Qwiic Button Hookup Guide](https://learn.sparkfun.com/tutorials/qwiic-button-hookup-guide/all#i2c-address).

---

### PCF8574 GPIO Expander: Add More Pins Over I²C

Sometimes your Pi’s header GPIO pins are already full (e.g., with a display or HAT). That’s where an I²C GPIO expander comes in handy.

We use the Adafruit PCF8574 I²C GPIO Expander, which gives you 8 extra digital pins over I²C. It’s a great way to prototype with LEDs, buttons, or other components on the breadboard without worrying about pin conflicts—similar to how Arduino users often expand their pinouts when prototyping physical interactions.

**Why is this useful?**
- You only need two wires (I²C: SDA + SCL) to unlock 8 extra GPIOs.
- It integrates smoothly with CircuitPython and Blinka.
- It allows a clean prototyping workflow when the Pi’s 40-pin header is already occupied by displays, HATs, or sensors.
- Makes breadboard setups feel more like an Arduino-style prototyping environment where it’s easy to wire up interaction elements.

**Demo Script:** `Lab 4/gpio_expander.py`

<p align="center">
    <img src="gpio_leds.gif" alt="GPIO Expander LED Demo" width="400"/>
</p>

We connected 8 LEDs (through 220 Ω resistors) to the expander and ran a little light show. The script cycles through three patterns:
- Chase (one LED at a time, left to right)
- Knight Rider (back-and-forth sweep)
- Disco (random blink chaos)

Every few runs, the script swaps to the next pattern automatically:
```bash
python gpio_expander.py
```

This is a playful way to visualize how the expander works, but the same technique applies if you wanted to prototype buttons, switches, or other interaction elements. It’s a lightweight, flexible addition to your prototyping toolkit.

---

### Servo Control with SparkFun Servo pHAT
For this lab, you will use the **SparkFun Servo pHAT** to control a micro servo (such as the Miuzei MS18 or similar 9g servo). The Servo pHAT stacks directly on top of the Adafruit Mini PiTFT (135×240) display without pin conflicts:
- The Mini PiTFT uses SPI (GPIO22, 23, 24, 25) for display and buttons ([SPI pinout](https://pinout.xyz/pinout/spi)).
- The Servo pHAT uses I²C (GPIO2 & 3) for the PCA9685 servo driver ([I2C pinout](https://pinout.xyz/pinout/i2c)).
- Since SPI and I²C are separate buses, you can use both boards together.
**⚡ Power:**
- Plug a USB-C cable into the Servo pHAT to provide enough current for the servos. The Pi itself should still be powered by its own USB-C supply. Do NOT power servos from the Pi’s 5V rail.

<p align="center">
    <img src="Servo_pHAT.gif" alt="Servo pHAT Demo" width="400"/>
</p>

**Basic Python Example:**
We provide a simple example script: `Lab 4/pi_servo_hat_test.py` (requires the `pi_servo_hat` Python package).
Run the example:
```
python pi_servo_hat_test.py
```
For more details and advanced usage, see the [official SparkFun Servo pHAT documentation](https://learn.sparkfun.com/tutorials/pi-servo-phat-v2-hookup-guide/all#resources-and-going-further).
A servo motor is a rotary actuator that allows for precise control of angular position. The position is set by the width of an electrical pulse (PWM). You can read [this Adafruit guide](https://learn.adafruit.com/adafruit-arduino-lesson-14-servo-motors/servo-motors) to learn more about how servos work.

---


### Part F

### Record

Document all the prototypes and iterations you have designed and worked on! Again, deliverables for this lab are writings, sketches, photos, and videos that show what your prototype:
* "Looks like": shows how the device should look, feel, sit, weigh, etc.
* "Works like": shows what the device can do
* "Acts like": shows how a person would interact with the device
 
## 🎯 Concept Overview
**The Shy Creature Box 2.0** brings a playful personality to life through sensors and expressive outputs.  
It reacts to the user’s proximity by changing its **facial expression**, **body motion**, and **voice**, creating a lifelike interaction loop.

When a user reaches toward the box, the “creature” senses the approach — the OLED shows a *shocked* or *scared* face 😳, the servo quickly pulls the creature down to “hide,” and the speaker plays a squeaky sound.  
When no one is near, the creature slowly reappears, smiling again. 😊

---

## 🧩 Hardware Components
| Category | Device | Function |
|-----------|---------|-----------|
| **Input 1** | Sparkfun Proximity Sensor Breakout Distance Sensor | Detects approaching hand distance |
| **Input 2** | Analog Joystick | Allows user to manually change creature “mood” (happy / curious / angry) |
| **Output 1** | SparkFun Qwiic OLED Display (0.91") | Displays animated creature faces and emotional states |
| **Output 2** | SG90 Servo Motor | Controls figurine or lid movement (hide / peek motion) |
| **Output 3** | Mini Speaker (PWM audio out) | Plays short “emotion” sounds when state changes |

---

## ⚙️ Interaction Logic

| State | Trigger | OLED Expression | Servo Motion | Speaker Sound |
|--------|----------|----------------|---------------|----------------|
| **Idle / Happy** | No hand detected | 😊 happy face | Peeking upright | Soft idle hum |
| **Shy Reaction** | Hand < 10 cm | 😳 surprised face | Quickly hides | Squeaky “eep!” sound |
| **Curious Mode** | Joystick up | 🤔 curious face | Slightly tilt up | “Hmm…” tone |
| **Angry Mode** | Joystick down | 😠 angry face | Fast twitch | Low “grr” buzz |

---


## 🧠 Interaction Diagram


<img src="https://github.com/user-attachments/assets/70ef4c71-3fbe-40b3-bf73-9346113ca33f" width="400"/>


### Interaction Flow
1. **Hand approaches** → distance sensor detects proximity (<10cm).  
2. **Microcontroller logic** → triggers “shy” reaction:
   - OLED shows 😳 shocked face  
   - Servo hides duck  
   - Speaker plays squeak sound  
3. **When user leaves**, after a delay, the creature calms down:
   - OLED returns to 😊 face  
   - Servo raises duck slowly  
   - Speaker plays soft hum  
4. **Joystick mode switch** → changes emotional theme (happy / angry / curious).



