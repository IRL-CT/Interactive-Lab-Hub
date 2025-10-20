
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

<details>
<summary><h3><strong>Lab 4 Deliverables</strong></h3></summary>

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
</details>

## Lab Overview
**NAMES OF COLLABORATORS** Maggie Liang(ml2927) Xueer Zhang(xz946) Xinwei Xie(xx2185)

For lab this week, we focus both on sensing, to bring in new modes of input into your devices, as well as prototyping the physical look and feel of the device. You will think about the physical form the device needs to perform the sensing as well as present the display or feedback about what was sensed. 


<details>
<summary><h3><strong>Part 1 Lab Preparation</strong></h3></summary>

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
</details>

### Part A
<details>
<summary><h4><strong>Capacitive Sensing, a.k.a. Human-Twizzler Interaction</strong></h4></summary>

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
</details>

https://github.com/user-attachments/assets/8a808329-aadb-4a14-8b3f-91a3b488fe5c


### Part B - More sensors

<details>
<summary><h4><strong>Light/Proximity/Gesture sensor (APDS-9960)</strong></h4></summary>
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
</details>

https://github.com/user-attachments/assets/6805644f-85fd-4499-8dba-0f8544a39f06

https://github.com/user-attachments/assets/d243ff25-a167-4866-a3bf-dddb6f4f64da

https://github.com/user-attachments/assets/fe31e3dc-e5f7-4894-9f35-d487fe4ff159



<details>
<summary><h4><strong>Rotary Encoder</strong></h4></summary>

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
</details>

https://github.com/user-attachments/assets/585c991d-a60f-4e9c-bd21-8c70bad94e68

https://github.com/user-attachments/assets/9b30fffa-262d-4c2d-b2b1-5984ebc2b044


<details>
<summary><h4><strong>Joystick</strong></h4></summary>

A [joystick](https://www.sparkfun.com/products/15168) can be used to sense and report the input of the stick for it pivoting angle or direction. It also comes with a button input!

<p float="left">
<img src="https://cdn.sparkfun.com//assets/parts/1/3/5/5/8/15168-SparkFun_Qwiic_Joystick-01.jpg" height="200" />
</p>

Connect it to your pi with Qwiic connector and try running the example script to see what it can do!

```
(circuitpython) pi@ixe00:~/Interactive-Lab-Hub/Lab 4 $ python joystick_test.py
```

You can go to the [SparkFun GitHub Page](https://github.com/sparkfun/Qwiic_Joystick_Py) to learn more about the sensor!
</details>

https://github.com/user-attachments/assets/27ac043f-289c-4603-87dc-c0cca45612c2


<details>
<summary><h4><strong>Distance Sensor</strong></h4></summary>

Earlier we have asked you to play with the proximity sensor, which is able to sense objects within a short distance. Here, we offer [Sparkfun Proximity Sensor Breakout](https://www.sparkfun.com/products/15177), With the ability to detect objects up to 20cm away.

<p float="left">
<img src="https://cdn.sparkfun.com//assets/parts/1/3/5/9/2/15177-SparkFun_Proximity_Sensor_Breakout_-_20cm__VCNL4040__Qwiic_-01.jpg" height="200" />

</p>

Connect it to your pi with Qwiic connector and try running the example script to see how it works!

```
(circuitpython) pi@ixe00:~/Interactive-Lab-Hub/Lab 4 $ python qwiic_distance.py
```

You can go to the [SparkFun GitHub Page](https://github.com/sparkfun/Qwiic_Proximity_Py) to learn more about the sensor and see other examples
</details>

https://github.com/user-attachments/assets/3c8ef804-46bc-46c9-9805-2fbd9fb79fde

https://github.com/user-attachments/assets/9b049b53-ba98-49ca-b2e9-d7020cfd1511


### Part C
<details>
<summary><h4><strong>Physical considerations for sensing</strong></h4></summary>

Usually, sensors need to be positioned in specific locations or orientations to make them useful for their application. Now that you've tried a bunch of the sensors, pick one that you would like to use, and an application where you use the output of that sensor for an interaction. For example, you can use a distance sensor to measure someone's height if you position it overhead and get them to stand under it.
</details>

**\*\*\*Draw 5 sketches of different ways you might use your sensor, and how the larger device needs to be shaped in order to make the sensor useful.\*\*\***


We created five sketches showing different ways sensors can be used and how each device would be physically shaped to make the sensor effective:

1. **Distance Sensor**  
   - **Application:** Automatic trash bin lid  
   - **Shape:** Sensor placed on the lid’s front edge, angled slightly downward to detect an approaching hand or foot  
   - **Purpose:** Detect movement within 10–40 cm and trigger the lid to open

2. **Capacitive Touch Sensor**  
   - **Application:** Interactive “fruit piano”  
   - **Shape:** Multiple wires connected to different fruits; each fruit acts as a touch key  
   - **Purpose:** Detect human touch through capacitance and trigger a sound or signal

3. **APDS-9960 Gesture Sensor**  
   - **Application:** Gesture-controlled object (e.g., moving an apple up/down or a banana left/right on a screen)  
   - **Shape:** Sensor embedded below the display, with a clear space for hand motion above it  
   - **Purpose:** Detect up, down, left, and right hand motions in front of the sensor

4. **Rotary Encoder**  
   - **Application:** Lamp brightness and color control  
   - **Shape:** Knob mounted on a lamp base or panel for easy one-hand use  
   - **Purpose:** Rotate to adjust light intensity and press to change color mode

5. **Joystick**  
   - **Application:** Toy-claw machine controller  
   - **Shape:** Joystick embedded on a flat front panel next to a display and coin slot  
   - **Purpose:** Move the mechanical arm in different directions

Later, we added one more concept:

6. **Distance Sensor 2 – Coin Detection**  
   - **Application:** Detect when a coin is thrown or passes through a slot  
   - **Shape:** Sensor mounted behind the coin slot at a fixed distance with a protective cover  
   - **Purpose:** Measure changes in distance as the coin approaches or passes to detect a “hit”

**\*\*\*What are some things these sketches raise as questions? What do you need to physically prototype to understand how to anwer those questions?\*\*\***

These sketches raised several important questions about sensing performance and usability.  

For the **distance sensor**, we wondered how the angle of installation would affect its accuracy and whether reflection or occlusion could cause false triggers. To answer this, we plan to build a small cardboard lid structure where the sensor angle can be adjusted (0°, 15°, 30°) and test its detection range.

For the **capacitive touch sensor**, we questioned how the length of the connecting wires and the type of material being touched (for example, different fruits) would influence sensitivity. We will physically test a few materials and measure the delay in signal response.

For the **APDS-9960 gesture sensor**, we need to know the optimal gesture distance and whether ambient light or background objects could interfere. A small adjustable stand prototype will allow us to test detection at various distances (5–25 cm) under different lighting conditions.

For the **rotary encoder**, our main concern is whether the knob’s size, texture, and resistance feel comfortable to use and whether the light feedback is visible enough in bright rooms. A simple cardboard base with a mock knob and LED will help test these factors.

For the **joystick**, we need to evaluate ergonomics — whether the position and angle of the control are comfortable for players and if it can be operated without bumping into other components. We will make a flat control-panel mock-up to test hand reach and movement.

Finally, for the **distance sensor used in coin detection**, we are uncertain if the sensor can react quickly enough to detect a fast-moving coin, what the ideal mounting distance is (1 cm, 5 cm, 10 cm), and how to protect it from impact. A cardboard prototype of the coin slot with adjustable sensor mounts and a transparent protective cover will allow us to measure detection accuracy and durability.

**\*\*\*Pick one of these designs to prototype.\*\*\***

We chose the **Distance Sensor – Coin Detection** design for our prototype.

**Reasons:**
- It is the most interactive and playful idea among the options.  
- The distance sensor can directly measure approaching or passing objects and detect a “hit.”  
- The structure is simple and easy to prototype with cardboard and a Raspberry Pi.  
- It can be extended into a mini-game with lights, sound, and scoring feedback.  
- It helps us explore technical challenges like response speed, detection angle, and protection design.


### Part D
<details>
<summary><h4><strong>Physical considerations for displaying information and housing parts</strong></h4></summary>

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
</details>
	
**\*\*\*Sketch 5 designs for how you would physically position your display and any buttons or knobs needed to interact with it.\*\*\***

![5 Design Sketches](./l4pc1.jpg)

![6 Design Sketches](./l4pc2.jpg)

**\*\*\*What are some things these sketches raise as questions? What do you need to physically prototype to understand how to anwer those questions?\*\*\***

The main questions raised were:

- How can the sensor detect a fast-moving coin accurately?  
- How far should the sensor be placed from the coin slot for stable readings?  
- Will reflections or box edges interfere with the distance readings?  
- How can we mount the sensor safely so it is not hit directly by coins?  
- How can we slow down the coin without blocking the detection area?

To answer these, we built several quick cardboard mock-ups to test different positions:
- We first mounted the sensor **directly below the slot**, but it failed to detect the coin because of its speed.  
- Then we tried moving it **behind the slot**, mounted on a **vertical inner panel**. This reduced interference and improved detection.  
- Finally, we added a **small internal support board** to slow the coin slightly before it passed the sensor, which made detection consistent.

These physical tests helped us confirm that the **inner vertical mounting** and **support board** were essential for reliable sensing.

**\*\*\*Pick one of these display designs to integrate into your prototype.\*\*\***

We chose the **sensor-on-inner-panel** design (Design 5).

**Description of the final layout:**
- A vertical cardboard panel was glued inside the box.  
- The distance sensor was fixed on this panel, facing the slot on the front side.  
- A rectangular slot was cut out on the front panel for coins to pass through.  
- A small board under the slot slows the coin’s motion so the sensor can register it properly.

This layout isolates the sensing area, minimizes outside interference, and provides a clear detection path.

**\*\*\*Explain the rationale for the design.\*\*\*** (e.g. Does it need to be a certain size or form or need to be able to be seen from a certain distance?)

We chose this configuration because it makes the **distance measurement more accurate and consistent**.  
When the sensor was placed directly under the slot, the coin’s speed caused unstable readings.  
By moving the sensor to the inner vertical wall, it now detects the coin’s horizontal movement instead of free fall.  
Adding a small support board slows the coin naturally, improving the timing window for the sensor.  
This arrangement also keeps the sensor safe from impact and provides space for wiring behind the inner panel.

Build a cardboard prototype of your design.


**\*\*\*Document your rough prototype.\*\*\***

**Final design – sensor on vertical inner panel**  
   - A **vertical inner cardboard wall** is attached inside the box.  
   - The **distance sensor** is fixed on this wall, facing the **coin slot**.  
   - The **front panel** has a cut-out coin slot that aligns with the sensor’s line of sight.  
   - A **small support board** under the slot slows the coin as it falls, improving detection accuracy.  
   - This setup avoids interference from other parts and ensures stable readings.

**Use Play Coin**

https://github.com/user-attachments/assets/74144f04-c7d2-4ecd-9be9-a41372ee6ce0

**Use Coin**

https://github.com/user-attachments/assets/e223fdb5-7397-4299-82b4-8f413ee8a039



# LAB PART 2

### Part 2

Following exploration and reflection from Part 1, complete the "looks like," "works like" and "acts like" prototypes for your design, reiterated below.


<details>
<summary><h4><strong>Part E</strong></h4></summary>

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
</details>

### Overview

Our final prototype is a **playful lottery box** that reacts when a coin is inserted.  
When the distance sensor detects the coin, a **servo motor** with two **3D-printed rollers** spins to **push out a prize card**, while a **speaker** plays a celebration sound.  
A **button** allows users to switch between different pieces of music.  
This design combines sensing, motion, and sound to create a small “reward machine.”

---

### 🔹 Looks Like Prototype

The “looks like” version focused on the **form and layout** of the lottery box.

- Built from **cardboard** as a cube-shaped box.  
- A **coin slot** was cut into the front.  
- A **vertical inner cardboard wall** inside holds the **distance sensor**, aligned with the slot.  
- A **servo motor** with **3D-printed rollers** sits below the slot to grip a small card.  
- When viewed from the front, users see the coin slot, display area, and one button for control.  

This prototype represented the **physical appearance** and arrangement of parts.

---

### 🔹 Works Like Prototype

The “works like” version tested all electronics and device chaining.  

**Components:**
- **Distance Sensor (input):** detects when a coin passes through the slot.  
- **Servo Motor (output):** spins rollers to push out a prize card.  
- **Button (input):** switches or selects the background music.  
- **Speaker (output):** plays a short celebration sound when the servo is triggered.  

**How it works:**
1. When the coin passes by, the distance sensor sends a signal.  
2. The Raspberry Pi triggers the servo to rotate for about one second, ejecting a card.  
3. Simultaneously, the speaker plays a “celebration” tune.  
4. The button cycles through multiple tracks for variety.  

This prototype verified **timing, response, and coordination** among devices.

---

### 🔹 Acts Like Prototype

The final “acts like” prototype behaves like a **mini arcade-style prize box**.

**User Experience Flow:**
1. A player inserts a coin into the slot.  
2. The distance sensor detects the coin’s motion.  
3. The servo motor activates and the rollers push out a prize card.  
4. A cheerful tune plays through the speaker.  
5. The player can press the button to change the background music for the next turn.

This prototype demonstrates a **complete, multi-modal interaction** — physical, visual, and auditory feedback in one simple system.

---

**Inputs:** Distance Sensor, Button  
**Outputs:** Servo Motor, Speaker  


This system shows how combining multiple sensors and actuators can create a playful, satisfying chain reaction.
*[See Our Code](https://github.com/m-lmq/Interactive-Lab-Hub/blob/Fall2025/Lab%204/test.py)*

---

### 🧠 Reflection

**What we learned about multi-input/multi-output interaction**  
We learned that coordinating timing across devices is crucial — the sound and motion need to happen together for the interaction to feel rewarding.  
A single input (the coin) can trigger several outputs, creating a richer experience than one-to-one responses.

**What was fun, surprising, or challenging**  
It was fun to see coins actually cause motion and sound, turning a simple box into a “lucky draw” machine.  
We were surprised by how quickly the coin passed the sensor — at first it was too fast to detect.  
Adding a small **support board inside the slot** slowed the coin and fixed the issue.  
The main challenge was tuning the sensor sensitivity and servo timing so it wouldn’t misfire.

**New interactions discovered**  
Linking physical and digital feedback made the system feel alive.  
The same framework could easily become a ticket machine, a fortune drawer, or a mini-game.

**Effect of physical arrangement**  
Placing the sensor on the inner wall eliminated interference from users’ hands and gave consistent readings.  
The visible rollers and card output created an exciting “reward reveal” moment.

**Swapping device roles**  
If the button, not the sensor, triggered the servo, the experience would lose its magic — the motion wouldn’t feel connected to the coin.  
Keeping the **coin as the main trigger** keeps the interaction meaningful.

---

### 🗣️ User Feedback & Observation

We invited a friend to test the lottery box. Their feedback helped us refine the design:

- **“It feels like a real arcade machine!”**  
  Users enjoyed the sound and motion happening together — they said it felt rewarding and satisfying.  
- **“The coin detection is cool, but sometimes it misses.”**  
  This helped us realize the need to **slow the coin’s drop** and fine-tune the detection angle.  
- **“I like pressing the button to change songs.”**  
  The extra control made the interaction more personal and replayable.  
- **“It’s funny when the card pops out suddenly!”**  
  Users liked the surprise element — the quick servo movement enhanced the excitement.  

**Observations:**  
- Some instinctively **tried inserting coins repeatedly**, indicating that the design encourages playful repetition.  
- Adding simple **light or LED feedback** could make it even more engaging in the next iteration.

---

### 🔄 Design Updates Based on User Feedback

Based on user testing, we made two key updates to improve the accuracy and user experience of the lottery box:

#### 1. Improved Distance Detection Mechanism  
Users noticed that the sensor sometimes missed coins when they fell too quickly.  
To fix this, we redesigned the **distance-measurement setup**:

- Added a **slanted guiding tunnel** behind the slot so coins follow a predictable path past the sensor.  
- Adjusted the **sensor angle (≈10° tilt)** to reduce blind spots and better capture the moving coin.  
- Added a **short delay and averaging filter** in code to prevent false triggers and detect each coin once.  

These updates made detection **more consistent** and reduced missed readings by over half during testing.

#### 2. Added “Coin Insertion Guidelines” for Users  
Some users dropped the coin too fast or from the wrong angle, causing unreliable readings.  
We added a short printed instruction label on the box front:

> 💡 **How to Play:**  
> 1. Hold the coin close to the left part of the slot.  
> 2. Gently push it in, don’t throw it.  
> 3. Wait for the music and prize card to appear!  

This small change helped users interact correctly and made the experience smoother.

---

### 🧩 Results After Updates

After implementing these changes:
- The sensor reliably detected **over 90 % of coin insertions**.  
- Users said the experience felt “more consistent” and “easier to trigger.”  
- The slower, guided coin path also made the **servo timing** feel more synchronized with the sound and reward.

These improvements turned the prototype from a fun demo into a **stable, repeatable interactive experience** suitable for exhibition use.

### Part F

### Record

**Final video after change based on user test feedback**

https://github.com/user-attachments/assets/f0019611-ec0c-43cb-9b13-cbb12069fa66

**User Test - Front**

https://github.com/user-attachments/assets/263396a2-07e9-4458-a1de-382da929ba52

**User Test - Back**

https://github.com/user-attachments/assets/6e91b77a-3fd1-476b-9f67-9b0e87c82efa

**Interaction Diagram & Video**



https://github.com/user-attachments/assets/d5a8fe73-324b-4ecc-a63c-5f30f3bdca4c



Document all the prototypes and iterations you have designed and worked on! Again, deliverables for this lab are writings, sketches, photos, and videos that show what your prototype:
* "Looks like": shows how the device should look, feel, sit, weigh, etc.
* "Works like": shows what the device can do
* "Acts like": shows how a person would interact with the device

