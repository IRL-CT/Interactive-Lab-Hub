
# Ph-UI!!!

#### Collaborators: Charlotte Lin (hl2575), Zoe Tseng (yzt2), Le-En Huang (lh764) 
#### Use of AI for this lab: Claude Sonnet4 for image creation and debugging instructions for the code.

## Lab 4 Deliverables

### Part 1 (Week 1)
**Submit the following for Part 1:**  
*️⃣ **A. Capacitive Sensing**
	- Photos/videos of your Twizzler (or other object) capacitive sensor setup


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

## Lab Overview

A) [Capacitive Sensing](#part-a)

B) [OLED screen](#part-b) 

C) [Paper Display](#part-c)

D) [Materiality](#part-d)

E) [Servo Control](#part-e)

F) [Record the interaction](#part-f)


## The Report (Part 1: A-D, Part 2: E-F)

### Part A @Zoe Tseng
### Capacitive Sensing, a.k.a. Human-Twizzler Interaction 

    
Video (pad 6): https://drive.google.com/file/d/1b7L1SqBQUygmfVYxJiss4DIEMV0uHwtq/view?usp=drive_link
Video (pad 10):
https://drive.google.com/file/d/14V4hyPFF8VFP9ItwjdHoa1cymrKm751O/view?usp=sharing

Code and terminal output showing touch detection
```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 4 $ python cap_test.py 
Twizzler 6 touched!
Twizzler 6 touched!
Twizzler 6 touched!
Twizzler 6 touched!
Twizzler 6 touched!
Twizzler 6 touched!
Twizzler 6 touched!
Twizzler 6 touched!
Twizzler 6 touched!
Twizzler 10 touched!
Twizzler 10 touched!
Twizzler 10 touched!
Twizzler 10 touched!
Twizzler 10 touched!
Twizzler 10 touched!
Twizzler 10 touched!
Twizzler 10 touched!
Twizzler 10 touched!
^CTraceback (most recent call last):
  File "/home/pi/Interactive-Lab-Hub/Lab 4/cap_test.py", line 16, in <module>
    time.sleep(0.25)  # Small delay to keep from spamming output messages.
    ^^^^^^^^^^^^^^^^
KeyboardInterrupt
``` 

### Part B
### More sensors

#### Light/Proximity/Gesture sensor (APDS-9960) @Charlotte Lin


Proximity
- photo

![proximity](https://hackmd.io/_uploads/HkxBqpFTxl.jpg)

- [video](https://drive.google.com/file/d/11OtQ9XfazL-6nwbsXwbiqk9xxBplYR6K/view?usp=drive_link)
- console output
```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 4 $ python proximity_test.py
0
0
0
0
3
44
167
224
255
255
253
253
255
11
6
12
189
251
254
255
255
255
255
255
16
0
0
0
```

Gesture
- photo
![gesture](https://hackmd.io/_uploads/B1FO5aF6ex.jpg)
- [video](https://drive.google.com/file/d/15aZFAI2Y_kP1M2qaymhDv42UCoqGmetB/view?usp=drive_link)
- console output
```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 4 $ python gesture_test.py 
down
right
left
down
up
down
```

Color
- photo
![color](https://hackmd.io/_uploads/BJ4c9TFpgg.jpg)
- [video](https://drive.google.com/file/d/1hiBqWVPw_DqA_ngKg1g7AsKgz8PEHs_k/view?usp=drive_link)
- console output
```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 4 $ python color_test.py
red:  2333
green:  1257
blue:  1045
clear:  4327
color temp 1770.7160880735482
light lux 461.7333600000002
red:  10
green:  8
blue:  6
clear:  29
color temp 3499.4007951306817
light lux 4.9889
red:  2
green:  2
blue:  1
clear:  7
color temp 3242.1840039686945
light lux 1.7755100000000001
red:  1
green:  2
blue:  1
clear:  5
color temp 4548.991462072831
light lux 2.10017
red:  3
green:  3
blue:  2
clear:  8
color temp 3942.565377810376
light lux 2.2973100000000004
red:  2527
green:  1356
blue:  1127
clear:  4682
color temp 1757.137645877991
light lux 494.9913300000002
red:  2802
green:  1502
blue:  1247
clear:  5184
color temp 1753.5357746806585
light lux 548.3226500000003
```

#### Rotary Encoder @Eva Huang 

- video
    - [demo](https://youtube.com/shorts/MpNVKIntTzs?feature=share)
    - [console output](https://youtu.be/KHeE8NTnrzw)

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 4 $ python encoder_test.py
Found product 4991
Position: 0
Position: 1
Position: 2
Position: 3
Position: 4
Position: 5
Position: 6
Position: 7
Position: 8
```

#### Joystick @Eva Huang

- video
    - [demo](https://youtube.com/shorts/pW5QYDFqWGM)
    - [console output](https://youtu.be/lZxyvGsi0Zo)

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 4 $ python joystick_test.py

SparkFun qwiic Joystick   Example 1

Initialized. Firmware Version: v 2.6
X: 514, Y: 517, Button: 1
...
X: 514, Y: 517, Button: 1
X: 1023, Y: 704, Button: 1
X: 0, Y: 517, Button: 1
X: 1023, Y: 517, Button: 1
X: 514, Y: 1023, Button: 1
X: 514, Y: 517, Button: 1
X: 514, Y: 1, Button: 1
X: 0, Y: 517, Button: 1
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 0
X: 514, Y: 517, Button: 0
X: 514, Y: 517, Button: 0
X: 514, Y: 517, Button: 0
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 1
X: 1022, Y: 1, Button: 1
X: 0, Y: 1022, Button: 1
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 0
X: 514, Y: 517, Button: 0
X: 514, Y: 517, Button: 0
X: 514, Y: 517, Button: 0
X: 514, Y: 517, Button: 0
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 1
X: 576, Y: 644, Button: 1
X: 1022, Y: 869, Button: 1
X: 1023, Y: 0, Button: 1
X: 0, Y: 418, Button: 1
X: 514, Y: 517, Button: 1
X: 514, Y: 517, Button: 1
^C
Ending Example 1
```

#### Distance Sensor @Charlotte Lin


- video
    - [demo](https://youtube.com/shorts/v1Gfl3jC7AU?feature=share)
- console output

```
(.venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 4 $ python qwiic_distance.py

SparkFun Proximity Sensor VCN4040 Example 1

Proximity Value: 4
Proximity Value: 4
Proximity Value: 4
Proximity Value: 4
Proximity Value: 8
Proximity Value: 21
Proximity Value: 18
Proximity Value: 48
Proximity Value: 272
Proximity Value: 354
Proximity Value: 471
Proximity Value: 52
Proximity Value: 8
Proximity Value: 7
Proximity Value: 6
Proximity Value: 5
Proximity Value: 6
Proximity Value: 22
Proximity Value: 124
Proximity Value: 397
Proximity Value: 405
Proximity Value: 142
Proximity Value: 10
Proximity Value: 5
Proximity Value: 5
Proximity Value: 6
Proximity Value: 4
Proximity Value: 4
Proximity Value: 4
Proximity Value: 3
^C
Ending Example 1
```

### Part C
### Physical considerations for sensing


**\*\*\*Draw 5 sketches of different ways you might use your sensor, and how the larger device needs to be shaped in order to make the sensor useful.\*\*\***


**\*\*\*What are some things these sketches raise as questions? What do you need to physically prototype to understand how to anwer those questions?\*\*\***

**\*\*\*Pick one of these designs to prototype.\*\*\***

#### 1. Bedside Sleep Companion
> Nightstand device for bedroom

<img src="https://hackmd.io/_uploads/HyyKwdragx.png" height="500"/>

```
Proximity: Detects when you reach over → displays time
Gesture up: Snooze alarm
Gesture down: Dismiss alarm
Light sensor: Auto-adjusts display brightness (dim at night, bright in morning)
Color sensor: Could detect sunrise colors and wake you gently
```

- Questions Raised:
    - Accidental triggers: Does rolling over in bed, pets, or a partner reaching over cause false alarms?
    - Gesture direction matters?: In darkness, do users naturally swipe up vs down? Or do they just wave randomly?
    - Sunrise color detection reliability: Can the sensor distinguish between actual sunrise, car headlights, phone screens, or artificial lights?
    - Optimal mounting position: Nightstand height? Angled down toward the bed or straight up?

- Need to Prototype:
    - Test with actual sleepy people
    - Mount device at different nightstand positions and observe natural reach patterns
    - Test color sensor with various light sources at dawn to see if sunrise is distinguishable

#### 2. Invisible DJ Booth

> Music playback controller!

<img src="https://hackmd.io/_uploads/HJ7rUOSTee.png" height="500"/>
How it works:
```
Swipe left/right: Skip tracks (prev/next song)
Swipe up/down: Volume control
Proximity + hold hand close: Scrub through current song (closer = faster scrub)
Color detection: Place colored cards near sensor to switch playlists (red=energetic, blue=chill, etc.)
Gesture combos: Double swipe for shuffle, circular motion for repeat
```

- Questions Raised:
    - Do users naturally gesture horizontally over a flat surface, or do they lift their hands up?
    - Color card distance: How close must colored cards be to the sensor? Does ambient lighting affect color detection?


Need to Prototype:

- Flat deck surface with sensor in center, test optimal hand hovering height (5cm? 10cm? 15cm?)
- Test color detection with different lighting conditions (bright room, dim room, colored room lights)
- Test if users can scrub through a song without visual feedback initially

#### 3. Interactive Tamagotchi

> Handheld-sized digit-pet
 
<img src="https://hackmd.io/_uploads/ByHJruHpxx.png" height="500"/>

```
Gesture Interactions:🍖 Swipe UP = Feed pet

Increases hunger bar
Pet does happy animation
Too much = sick!
🎮 Swipe DOWN = Play with pet

Pet jumps/bounces animation
Increases happiness
Decreases hunger slightly (exercise!)
❤️ Swipe RIGHT = Pet/affection

Pet purrs/wags tail
Increases happiness
Builds bond level
💊 Swipe LEFT = Give medicine/clean

Cures sickness
Cleans up "mess"
Returns to healthy state
👋 Proximity detection = Check status/wake up
```

- Questions Raised:
    - False positives: How often does normal movement (walking, putting it in a pocket) trigger unintended actions?
    - Hand positioning: Do users naturally gesture over the sensor, or do they gesture in front of the screen?

- Need to Prototype:
    - An egg-shaped enclosure with the ADPS sensor mounted at different positions (top, front, angled)
    - Test different gesture heights (2cm, 5cm, 10cm above sensor)
    - Observe natural user behavior: where do people instinctively gesture?

#### 4. Bathroom Hand-Wash Timer

> Educational handwash timer, perfect for k-12!

 
<img src="https://hackmd.io/_uploads/H1AlO_Haxl.png" height="500"/>

```
Proximity: Detects when hands are under sensor → starts 20-second countdown
Display: Shows countdown timer with progress bar
Gesture up: Restart timer if you need more time
Ambient light: Works in dark bathrooms (auto-brightness)
Feedback: Beeps/flashes when 20 seconds complete (proper hand-washing time)
```

- Questions Raised:
    - Water interference: Does running water, steam, or soap splashes affect the sensor?
    - Mounting height: What's optimal - mounted high looking down, or at counter level?
    - Edge case behaviors: What if you move hands in/out of range while washing? Does timer pause or restart?

- Need to Prototype:
    - Mount sensor above actual sink, test with running water and steam
    - Test detection cone width - can it cover the entire sink area?
    - Test with different hand movements (vigorous scrubbing, gentle washing)


#### 5. "Medicine Reminder Box"
> Physical reminder for taking pills/vitamins, perfect for elders!

<img src="https://hackmd.io/_uploads/H1ID9Orpxl.png" height="500"/>

```
Display: Shows "TIME TO TAKE MEDS" at scheduled times
Proximity: Wave hand to confirm you took medicine → logs timestamp
Gesture up: Snooze reminder for 10 minutes
Gesture down: Mark as "skipped" (records missed dose)
Ambient light: Tracks if you're home when reminder goes off (lights on = home)
Color sensor: Could detect pill bottle colors to track which medication
```

- Questions Raised:
    - How does it distinguish between "wave to confirm" vs "reaching for pills" vs "just passing by"?
    - Color detection practical range: Must pill bottles be placed at exact distance? Does bottle shape/label affect detection?
    - What if someone waves at the device accidentally while moving around the room?

- Need to Prototype:
    - Test with actual elderly users and observe natural gesture patterns and difficulties
    - Test color detection with real pill bottles at various distances and angles
    - Test ambient light sensor correlation with "home presence" over several days


---

### Part D
### Physical considerations for displaying information and housing parts


**\*\*\*Sketch 5 designs for how you would physically position your display and any buttons or knobs needed to interact with it.\*\*\***

**\*\*\*What are some things these sketches raise as questions? What do you need to physically prototype to understand how to anwer those questions?\*\*\***

- user interaction / usability : do the buttons appeared to be intuitive ? does the user understand what each element or action does ?
- informaiton content : is the order or hierarchy of information clear? Do users interpret icons, labels, and data the way we expect?
- Feasibility / Technical Constraint : will performance (e.g., loading time, hardware constraints) affect usability?

**\*\*\*Pick one of these display designs to integrate into your prototype.\*\*\***

**\*\*\*Explain the rationale for the design.\*\*\*** (e.g. Does it need to be a certain size or form or need to be able to be seen from a certain distance?)

Build a cardboard prototype of your design.


**\*\*\*Document your rough prototype.\*\*\***

<img src="https://hackmd.io/_uploads/SJVRpdS6ge.png" width="400"/>


<img src="https://hackmd.io/_uploads/S1bEZtrpee.png" width="400"/>


### 🎨 Design #3: Twizzler Touch Edition (Capacitive Petting Pad)

**Sensors Used:** Capacitive Sensor Board (MPR121) + Copper Tape or Twizzlers  

<img src="https://hackmd.io/_uploads/H1itQCtTgx.png" width="400"/>

### **Description**
Four touch pads—🍖 Feed, 🎮 Play, 💊 Medicine, ❤️ Pet—are arranged around the central display.  

### 🕹️ Design #4: Rotary Mood Dial + Distance Sensor

**Sensors Used:** Rotary Encoder + Distance Sensor  

<img src="https://hackmd.io/_uploads/rJI4NRYale.png" width="400"/>

### **Description**
- Combines **rotational input** for selecting pet actions with **distance sensing** to detect user presence. 
- The rotary knob scrolls through actions like *Feed*, *Play*, *Clean*, and *Heal*.  
- The distance sensor **wakes the pet** when the user approaches.


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

