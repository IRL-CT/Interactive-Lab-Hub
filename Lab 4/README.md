
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

<details>
	<Summary><strong>Lab 4 Deliverable (Click to Expand)</strong>
	</summary>

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

The deliverables for this lab are, writings, sketches, photos, and videos that show what your prototype:

"Looks like": shows how the device should look, feel, sit, weigh, etc.
"Works like": shows what the device can do.
"Acts like": shows how a person would interact with the device.
For submission, the readme.md page for this lab should be edited to include the work you have done:

Upload any materials that explain what you did, into your lab 4 repository, and link them in your lab 4 readme.md.
Link your Lab 4 readme.md in your main Interactive-Lab-Hub readme.md.
Labs are due on Mondays, make sure to submit your Lab 4 readme.md to Canvas.

</details>

<details>
	<summary><strong>Lab 4 Part 1. Preparation</strong></summary>
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

</details>

---

## Lab Overview
Collaborators: Jessica Hsiao (dh779), Irene Wu (yw2785)

For lab this week, we focus both on sensing, to bring in new modes of input into your devices, as well as prototyping the physical look and feel of the device. You will think about the physical form the device needs to perform the sensing as well as present the display or feedback about what was sensed. 


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

We chose **Light/Proximity/Gesture sensor (APDS-9960)** as our sensor.

**Application #1: Plant Health Monitor**

- Sensor information: light
- The device is capable of detecting plant color variations by RGB. When the color shifts from bright and vibrant tones to brown, the system alerts users that the plants are under stress or nearing death. Users can then respond by providing additional water or nutrients to restore plant health.

**Application #2: Natural Lighting Room**

- Sensor information: light
- Mounted near a window or ceiling fixture, the sensor continuously measures ambient light intensity. When sufficient natural light is detected, the system automatically dims or turns off artificial lighting to save energy.

**Application #3:  Exhibition Visitor Counter**

- Sensor information: gesture
- Placed on a side or above an exhibit entryway, the APDS-9960 detects directional hand or body movements. When a visitor passes by, the gesture data (e.g., left or right swipe) increments a counter, helping curators estimate visitor flow and engagement.

**Application #4: Eye Wellness Assistant**

- Sensor information: proximity
- Integrated near a computer monitor or laptop bezel, the proximity sensor tracks how close a user’s face is to the screen. If the user sits too close for prolonged periods, the system gently alerts them to maintain a healthier viewing distance.

**Application #5: Movie Controller**

- Sensor information: gesture
- Installed near a TV or projector, the sensor enables touch-free gesture controls. Users can swipe left to rewind, swipe right to skip, or perform an upward gesture to pause/play the movie.



**\*\*\*Draw 5 sketches of different ways you might use your sensor, and how the larger device needs to be shaped in order to make the sensor useful.\*\*\***

Application #1: Plant Health Monitor

<img src="./assets/C.%20Plant%20Health%20Monitor.png" height="400" />

Application #2: Natural Lighting Room

<img src="./assets/C.%20Natural%20lighting%20room%20detection.png" height="400" />

Application #3:  Exhibition Visitor Counter

<img src="./assets/C.%20Exhibition%20visitor%20counter.png" height="400" />

Application #4: Eye Wellness Assistant

<img src="./assets/C.%20Eye%20wellness%20assistant.png" height="400" />

Application #5: Movie Controller

<img src="./assets/C.%20Movie%20controller.png" height="400" />


**\*\*\*What are some things these sketches raise as questions? What do you need to physically prototype to understand how to anwer those questions?\*\*\***

**Application #1: Plant Health Monitor**
- Questions raised:
	1. Connection and communication: The sketch doesn’t specify how the sensor and the display communicate — whether they are connected by wire, use wireless transmission, or operate through an intermediary microcontroller such as a Raspberry Pi.
	2. Sensor placement: It’s unclear how the sensor should be positioned or angled relative to the plant’s leaves to ensure consistent and accurate color readings.
	3. Environmental lighting effects: Different ambient lighting conditions (sunny vs. cloudy, indoor vs. outdoor) could alter the perceived color of the plant, even when its actual health remains the same.

- To address these questions, we can first build a prototype that tests various sensor positions and angles to determine which setup yields the most stable readings. Next, running lighting variation tests — capturing RGB data under multiple environmental conditions — would help calibrate thresholds or develop compensation algorithms. Finally, prototyping the communication pathway between the sensor and display (wired vs. wireless) will clarify how to make the system responsive and portable for real-world use.

**Application #2: Natural Lighting Room**

- Questions raised:
	1. Light differentiation: The sketch doesn’t explain how the sensor distinguishes between natural and artificial light — will it rely solely on overall brightness, or also consider color temperature and spectral balance?
	2. Sensitivity and stability: It’s unclear how sensitive the system should be before adjusting lighting intensity. Minor fluctuations in sunlight (e.g., when clouds pass) could cause unstable dimming or flickering.
	3. Sensor orientation: The sensor’s placement and angle might significantly affect readings — pointing it directly at a window versus facing the interior ceiling could produce very different results.
	4. Communication and control: The sketch doesn’t specify how the sensor interacts with the lighting system — through direct wiring, a microcontroller, or a wireless connection.

- To address these questions, we can start by testing the sensor at different positions and orientations within a room to measure how light readings vary across the day. Next, a calibration experiment can help determine appropriate brightness thresholds and smoothing algorithms to avoid frequent or erratic lighting changes. Finally, building a prototype connection between the sensor and a light controller (e.g., Raspberry Pi + LED dimmer) will allow us to evaluate real-time response and communication reliability.

**Application #3:  Exhibition Visitor Counter**

- Questions raised:
	1. Detection accuracy: The sketch doesn’t specify how the sensor distinguishes between individual visitors — for example, how it avoids counting the same person twice or missing people walking closely together.
	2. Range and directionality: It’s unclear how far the APDS-9960 can reliably detect gestures or movement and whether it can sense entry versus exit directions.
	3. Environmental interference: Exhibition lighting, reflections, or nearby displays might interfere with gesture detection or falsely trigger the counter.
	4. Physical placement: The optimal height and orientation of the sensor relative to the doorway are uncertain — it may need to be tested at various positions to ensure consistent detection.

- By testing different sensor heights and distances near an actual doorway, we can measure detection accuracy for varying visitor speeds and group sizes. Additionally, running environmental tests under different lighting conditions will help determine if shielding or calibration is needed to reduce false triggers. Finally, prototyping a count display system will help evaluate real-time feedback and timing consistency during high-traffic scenarios.

**Application #4: Eye Wellness Assistant**

- Questions raised:
	1. Unclear sense of distance: The sketch doesn’t convey how far the user is from the screen, making it difficult to judge whether the sensor can accurately measure a comfortable viewing range.
	2. Screen tilt impact: The monitor’s tilt angle could affect proximity readings, since the sensor’s detection depends heavily on its facing direction.
	3. Sensor form and placement: The drawing doesn’t indicate the sensor’s actual size or visibility, leaving uncertainty about whether it would distract the user or blend seamlessly into the screen design.

- To answer the first question, we need to design a way to display the distance information to the user, for instance, putting a tiny monitor next to the screen to show the number. For the second and the third questions, they can be approached by conducting user studies with the physical prototype to experiment in a real-world settings. We can run user trials with different sensor placements and screen angles to evaluate accuracy, comfort, and intrusiveness in daily use.

**Application #5: Movie Controller**

- Questions raised:
	1. Gesture recognition accuracy: The sketch doesn’t clarify how reliably the sensor can differentiate between gestures such as left, right, or up swipes, especially when users vary in hand speed or distance.
	2. Detection range and angle: It’s unclear how far the user can sit from the screen while still being detected, or how wide the sensor’s field of view needs to be to capture gestures effectively.
	3. Interference and usability: Ambient lighting, reflections, or nearby movement (like someone walking past) could accidentally trigger commands. The sketch doesn’t show how the system might prevent or handle such false positives.

- To address these questions, we can build a functional prototype that connects the gesture sensor to a simple media controller. This would allow testing of gesture detection accuracy across multiple users, distances, and lighting conditions. We also need to experiment with sensor placement and viewing angles — for example, mounting it on top of or below the TV — to find the most reliable setup. Lastly, collecting real interaction data can help define gesture thresholds and filtering strategies to minimize unintended activations.


**\*\*\*Pick one of these designs to prototype.\*\*\***

We picked the forth one to prototype: Eye Wellness Assistant


### Part D
### Physical considerations for displaying information and housing parts

<details>
	<summary>Examples (Click to expand)
	</summary>
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
</details>



Think about how you want to present the information about what your sensor is sensing! Design a paper display for your project that communicates the state of the Pi and a sensor. Ideally you should design it so that you can slide the Pi out to work on the circuit or programming, and then slide it back in and reattach a few wires to be back in operation.
 
**\*\*\*Sketch 5 designs for how you would physically position your display and any buttons or knobs needed to interact with it.\*\*\***

**Design #1**: The physical prototype includes an adjustable sensor holder extending from the computer, with a small board placed next to it for sensor integration. When the user is too close to the monitor, the board will display a red light and flash continuously to alert them. Otherwise, the board will remain black without providing any additional notifications.

<img src="./assets/D.%20Design%201.png" height="400" />

**Design #2**: The physical prototype includes an adjustable curved phone stand extending from the computer, with a small light placed beside it to indicate the proximity detection status. It uses a color light (green = good, yellow =  a bit close, red = too close) to present the status.

![img](./assets/D.%20Design%202.png)

**Design #3**: The physical prototype includes an adjustable curved phone stand extending from the computer, with a small board placed next to it for sensor integration. The actual distance between the screen and the user’s face will be displayed on the board.

<img src="./assets/D.%20Design%203.png" height="400" />

**Design #4**: Place the sensor on top of the computer with the sensor facing downward. When the user gets too close to the computer (meaning their head is below the sensor), the sensor detects the proximity and uses a beeping sound to alert the users.

<img src="./assets/D.%20Design%204.png" height="400" />

**Design #5**: Place the sensor on top of the computer with the sensor facing downward. When the user gets too close to the computer (meaning their head is below the sensor), a voice message will be played to remind the user of the distance, such as “you are too close to your screen, please keep away from it”

<img src="./assets/D.%20Design%205.png" height="400" />


**\*\*\*What are some things these sketches raise as questions? What do you need to physically prototype to understand how to anwer those questions?\*\*\***

#### Design #1

- Questions raised:
	1. How sensitive should the proximity threshold be to accurately detect when the user is “too close” without triggering false alerts?
	2. Will the flashing red light be noticeable yet comfortable for the user, or could it become distracting during long use?
	3. How much does the adjustable sensor angle affect detection accuracy across different screen tilt positions and user heights?
- What to prototype:
	1. Test various distance thresholds to determine the optimal trigger range for comfort and accuracy.
	2. Experiment with different light intensities, colors, and flashing rates to find a balance between visibility and user comfort.
	3. Build and evaluate the adjustable holder to measure how sensor angle and placement influence proximity detection reliability.


#### Design #2

- Questions raised:
	1. What are the optimal distance thresholds for each color indicator (green, yellow, red) to provide meaningful and intuitive feedback to users?
	2. Will users easily notice and interpret the color changes, or would additional feedback (e.g., brightness or flashing) improve clarity?
	3. How does the curved stand’s angle and height affect the accuracy of proximity detection for users of different sitting positions?
- What to prototype:
	1. Calibrate and test various distance ranges to define clear and consistent thresholds for each light color.
	2. Conduct short user tests to evaluate whether color feedback alone is sufficient for awareness and comfort.
	3. Build the curved stand prototype and measure detection performance at multiple sensor angles and user heights to ensure reliability.


#### Design #3

- Questions raised:
	1. How accurate and responsive will the displayed distance values be when the user moves slightly or changes posture?
	2. What is the most effective way to display the distance information so that it’s noticeable without being distracting?
	3. How does the sensor’s placement or tilt angle influence measurement consistency across different screen setups and user positions?
- What to prototype:
	1. Test the sensor’s real-time distance measurement accuracy and response speed under typical usage movements.
	2. Experiment with different display formats (numerical, graphical, or color-coded) to assess readability and user comfort.
	3. Build the adjustable stand prototype and measure how various angles and distances affect data stability and reliability.

#### Design #4:

- Questions raised:
	1. How accurately can the downward-facing sensor detect when the user’s head crosses the threshold distance without being affected by lighting or hair color?
	2. What should the distance threshold be to ensure the alert triggers at a comfortable and safe viewing distance?
	3. Will the beeping alert remain effective over time, or might it become annoying or easy to ignore during long computer use?
- What to prototype:
	1. Test detection reliability across users with different heights, hairstyles, and seating positions.
	2. Experiment with several threshold distances to determine an optimal range that balances comfort and alert sensitivity.
	3. Prototype different audio feedback patterns (e.g., single beep vs. continuous tone) to evaluate which is most noticeable yet least disruptive.


#### Design #5:
- Questions raised:
	1. How should the timing and frequency of the voice alert be set so it effectively reminds users without feeling intrusive?
	2. Will the downward-facing sensor maintain consistent accuracy across users with different heights and seating distances?
	3. Do users perceive the voice message as helpful feedback or as a distraction during focused work?
- What to prototype:
	1. Experiment with various voice alert intervals, tones, and volumes to find a balance between clarity and comfort.
	2. Test the sensor’s performance across diverse user positions and lighting environments to ensure reliable detection.
	3. Conduct short user evaluations comparing voice feedback with other alert methods (e.g., light or sound) to determine the most preferred design.



**\*\*\*Pick one of these display designs to integrate into your prototype.\*\*\***

We picked the forth one to integrate into our prototype.

**\*\*\*Explain the rationale for the design.\*\*\*** (e.g. Does it need to be a certain size or form or need to be able to be seen from a certain distance?)

#### Why the device is elevated
- The sensor needs to face downward to accurately detect the user’s head position. However, because the sensor strip is relatively short, we had to raise the Raspberry Pi to achieve the proper downward angle. Elevating the device also ensures that the user’s head does not accidentally block or strike the sensor during normal use.
- During testing, we found that the sensor can reliably detect objects within a range of about 15 cm. Beyond this distance, detection becomes unreliable. Therefore, raising the device ensures that the user’s head remains within this effective detection range for consistent performance.

#### Why the device has several holes
- The holes serve multiple functional purposes. One is for the Bluetooth module, which broadcasts audio alerts to notify the user when they are sitting too close to the screen. Another set of holes supports display visibility and ventilation. We integrated a small screen on the Raspberry Pi to show system details and user feedback. To make this display clear and user-friendly, we positioned it near the radio broadcaster and ensured there are openings for both visibility and heat dissipation.

#### Why handles were added to the device
- We added two handles on the right side of the device to make maintenance easier. These handles allow users or developers to conveniently open the casing for adjustments, sensor calibration, or component replacement without damaging the housing.


Build a cardboard prototype of your design.

**\*\*\*Document your rough prototype.\*\*\***

<img src="./assets/cardboard%20prototype.png" height="600" />

# LAB PART 2

Following exploration and reflection from Part 1, complete the "looks like," "works like" and "acts like" prototypes for your design, reiterated below.


---

### Part C: Chaining Devices and Exploring Interaction Effects

For Part 2, We designed and built a fun interactive prototype using multiple inputs and outputs. We use two inputs and two outputs to give users hints about the distance between user's head and their computers.

#### Detail Function:

- Proximity Detection
	- The sensor continuously measures the distance between the user’s head and the computer area.
	- When the user gets too close, the system switches from the “normal” state to the “warning” state.


- Visual Feedback (Screen)
	- In the normal state, the screen displays a motivational or positive message to encourage healthy posture.
	- In the warning state, the screen turns red and shows a clear alert message (“You are too close to the screen”) to draw attention.


- Audio Feedback (Speaker)
	- When the warning is triggered, the speaker plays a sound alert.
	- This adds an additional layer of feedback that is harder to ignore than visuals alone.

- User Control (Buttons)
	- One button allows the user to start or activate the monitoring system.
	- The second button lets the user silence the audio alert or stop the notification, giving the user agency.

- Interaction Flow
	- The sensor detects → screen and speaker react → user acknowledges with a button press → system resets.
	- This creates a loop of detection, feedback, and user response.


##### Input: 

1. Proximity Sensor: The sensor is placed next to the computer (typically around 40 cm away). When it detects an object below it—usually the user’s head—it triggers the application to remind the user to maintain a proper distance from the screen.

2. Two Led Button: Users can press one button to start the application, while the second button is used to stop notifications. For example, if the application plays a sound to warn the user that they are too close to the screen, pressing the second button will silence the alert.

##### Output: 
1. Screen: When the application is in a normal state (no warning is needed), the screen displays a motivational message to encourage the user to maintain good posture and continue working. When a warning is triggered, the screen switches to a red background and displays the message “You are too close to the screen” to alert the user.
2. Speaker: When a warning is triggered, which indicates that the user is too close to the computer, the speaker plays an alert sound.


**Hardware Block Diagram**

```scss
  ┌─────────────────────┐
  │   Proximity Sensor  │
  └─────────┬───────────┘
            │  (distance data)
            ▼
  ┌─────────────────────┐
  │     Raspberry Pi    │
  └───────┬───────┬─────┘
          │       │         │
       (visual) (audio) (user input)
          ▼       ▼         ▼
      ┌──────┐  ┌───────┐  ┌───────┐
      │Screen│  │Speaker│  │Buttons│
      └──────┘  └───────┘  └───────┘


```

**Interaction Flow Diagram**

```pgsql
           ┌────────────────────────┐
           │ Sensor checks distance │
           └─────────────┬──────────┘
                         │
        ┌────────────────┴─────────────────┐
        │                                  │
        ▼                                  ▼
  (User at safe distance)          (User too close)
        │                                  │
        ▼                                  ▼
Screen shows motivation          Screen turns red + alert text
        │                                  │
        ▼                                  ▼
     No sound                       Speaker plays warning
                                           │
                                           ▼
                          User presses button to silence alert
                                           │
                                           ▼
                           System returns to normal state

```

**System Flowchart**

```pgsql
              ┌──────────────────────┐
              │   System Started     │
              │ (User presses start) │
              └───────────┬──────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │ Sensor reads distance│
              └───────────┬──────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
   ┌───────────────────┐       ┌─────────────────────┐
   │ User far enough   │ NO    │  User too close     │ YES
   │ (safe distance)   │────── │  (below threshold)  │
   └─────────┬─────────┘       └─────────┬───────────┘
             │                           │
             ▼                           ▼
  ┌────────────────────┐      ┌────────────────────────┐
  │ Show motivational  │      │  Turn screen red       │
  │ text on screen     │      │  Display warning text  │
  └─────────┬──────────┘      └─────────┬──────────────┘
            │                           │
            ▼                           ▼
  ┌────────────────────┐      ┌────────────────────────┐
  │   No sound played  │      │  Speaker plays sound   │
  └─────────┬──────────┘      └─────────┬──────────────┘
            │                           │
            │              ┌────────────┴────────────┐
            │              │  User presses stop btn  │
            │              └────────────┬────────────┘
            │                           ▼
            │                ┌──────────────────────┐
            └───────────────▶│   Sound is silenced  │
                             │ System goes back to  │
                             │     normal state     │
                             └───────────┬──────────┘
                                         │
                                         ▼
                                 (Loop continues)

```

#### System Architecture

| Layer                   | Components                                                                            | Role                                                            |
| ----------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **Sensors (Input)**     | APDS9960 proximity sensor, Qwiic Button #1 & #2, GPIO buttons                         | Detect user proximity and button interaction                    |
| **Compute & Logic**     | Raspberry Pi running Python main loop                                                 | Coordinates all logic and state machine (NORMAL / WARNING mode) |
| **Communication Buses** | I2C (APDS9960 + QWIIC buttons), SPI (TFT display), GPIO (backlight + onboard buttons) | Hardware communication backbone                                 |
| **Output**              | ST7789 TFT screen, backlight, text-to-speech (espeak)                                 | Displays user feedback and audible warning                      |



#### Demo (Photos and/or video of the working prototype in action)

Coding: look at [demo.py](https://github.com/JessicaDJ0807/Interactive-Lab-Hub/blob/Fall2025/Lab%204/demo.py)

* "Looks like": shows how the device should look, feel, sit, weigh, etc.

![img](./assets/looks_like.png)

* "Works like": shows what the device can do

![img](./assets/works_like.png)

* "Acts like": shows how a person would interact with the device

https://github.com/user-attachments/assets/16318d59-851d-438b-872a-084e3ad348d3


#### Users Feedback
* At first the sound surprised the user, but it was helpful because they sometimes don’t notice visual warnings when they're focused on the screen.
* They like that they can press a button to stop the sound. It feels like they still have control, instead of being stuck with an alarm.
* When the sensor was placed in front of them, it triggered too often and felt a bit annoying. But once you moved it to the side, it felt much smoother and more natural.

---

### Part D. Written Reflection

- Learning about multi-input/multi-output interaction

	- We learned that combining multiple sensors and actuators enables much richer and more meaningful interaction than using a single component. A proximity sensor alone can only detect that the user is too close, but it cannot communicate anything back. Once we added the screen, speaker, and buttons, the system could respond in multiple ways, including displaying a visual warning, playing a sound, or showing encouragement when the user maintained a healthy distance. This made the feedback intuitive and noticeable, transforming the system from a hidden measurement tool into an interactive assistant.

- New types of interaction from combining components

	- A proximity sensor alone only measures distance, but when paired with a screen and speaker, it becomes a behavioral feedback tool.

	- Adding buttons introduces two-way interaction. The user can acknowledge or silence alerts, not just passively receive them.

- Impact of physical arrangement

	- We discovered that the placement, distance, and angle of the sensor significantly shaped the user experience. When the sensor was positioned directly in front of the user, it triggered constant alerts and felt intrusive, even though it was technically accurate. After moving it to the side and angling it downward, the detection became smoother and more reliable, and the feedback felt more natural and helpful rather than annoying. This showed us that hardware setup affects how the interaction feels, not just how well it measures.

- Using one device to modulate another

	- The sensor triggers the warning, but the button controls how the warning continues.

	- This creates a feedback loop: sensor → system response → user action → system change.

- Primary vs. secondary device roles

	- When the sensor is “primary,” the system feels automatic and proactive.

	- When the button is “primary,” the system feels more user-controlled and cooperative.

	- Switching roles changes the tone of the interaction from “monitoring” to “assisting.”

- Fun, surprising, and challenging aspects

	- Fun: It was fun because we got to see something very simple, like a sensor, a screen, or a button, turn into a meaningful interaction once they were combined. Each component by itself felt basic, but when we connected them together, the system suddenly felt responsive. It was satisfying to watch a small physical change (like moving closer to the screen) trigger a chain of reactions that ended in useful feedback for the user. Building that kind of visible cause-and-effect interaction made the project feel rewarding rather than just technical.

	- Surprising: It was surprising because at first we assumed the sensor’s code and detection range would matter most, but we later realized that the physical placement had an even bigger impact on usability than the technical settings. Just moving the sensor a few centimeters or changing the angle completely changed how the system “felt” to the user, either calm and supportive, or overly aggressive and annoying. We didn’t expect something so simple and low-level (hardware positioning) to influence the overall user experience more than the logic running in the software.

	- Challenging: We found that one of the biggest challenges was choosing a physical location for the sensor that provided useful feedback without becoming annoying. When the sensor was placed too close or directly in front of the user, it triggered constant warnings, even small head movements caused alerts, which felt frustrating. But when we moved it slightly to the side and adjusted the angle, the feedback became much more natural and less intrusive. This showed us that where the hardware is physically positioned matters just as much as how the software detects distance.



