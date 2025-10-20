
# Ph-UI!!!

## Lab 4 Deliverables

#### Collaborators: Charlotte Lin (hl2575), Zoe Tseng (yzt2), Le-En Huang (lh764) 
#### Use of AI for this lab: Claude Sonnet4 for image creation and debugging instructions for the code.


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

### Design #1: Top Sensor Classic
**Sensors Used:** APDS Gesture Sensor

<img src="https://hackmd.io/_uploads/SJVRpdS6ge.png" width="400"/>

&nbsp;  
**Description:**
- Users interact through simple hand gestures above the device — for example, swiping up to Feed or down to Play
- The screen displays pet status (Hunger, Happiness) and visual reactions
- Three buttons (A, B, C) below the screen support menu navigation and confirmations

**Need to Prototype:**
- Test gesture accuracy and false triggers with a top-mounted APDS in varied lighting and hand positions.

### Design #2: Joystick Control
**Sensors Used:** APDS Gesture Sensor + Analog Joystick

<img src="https://hackmd.io/_uploads/S1bEZtrpee.png" width="400"/>

&nbsp;  
**Description:**
- The joystick enables directional inputs for Feed, Play, Clean, and Pet, making it feel more game-like and interactive
- The APDS sensor adds shortcut gestures for instant responses, enhancing speed and convenience

**Need to Prototype:**
- Build a mock joystick setup to test comfort, accuracy, and how it integrates with gesture inputs.

### Design #3: Twizzler Touch Edition (Capacitive Petting Pad)

**Sensors Used:** Capacitive Sensor Board (MPR121) + Copper Tape or Twizzlers  

<img src="https://hackmd.io/_uploads/H1itQCtTgx.png" width="400"/>

&nbsp;  
**Description:**
- Four touch pads—🍖 Feed, 🎮 Play, 💊 Medicine, ❤️ Pet—are arranged around the central display

**Need to Prototype:**
- Create a touch-panel mockup with copper pads and test pad spacing, labeling, and sensitivity.

### Design #4: Rotary Mood Dial + Distance Sensor

**Sensors Used:** Rotary Encoder + Distance Sensor  

<img src="https://hackmd.io/_uploads/rJI4NRYale.png" width="400"/>

&nbsp;  
**Description:**
- Combines **rotational input** for selecting pet actions with **distance sensing** to detect user presence
- The rotary knob scrolls through actions like *Feed*, *Play*, *Clean*, and *Heal*
- The distance sensor **wakes the pet** when the user approaches  

**Need to Prototype:**
- Assemble a tabletop model to test rotary precision and wake-on-approach reliability.

### Design #5: Hybrid Playground (APDS + Joystick + Rotary Encoder)

**Sensors Used:** APDS Gesture Sensor + Joystick + Rotary Encoder

<img src="https://hackmd.io/_uploads/B1Re6qTTlg.png" width="400"/>

&nbsp;  
**Description:**
- The APDS sensor at the top detects quick gestures
- The joystick provides tactile input for Feed, Play, and Clean actions — giving users fine control and an arcade-like feel
- The rotary dial adjusts secondary settings such as brightness, sound, or pet mood intensity

**Need to Prototype:**
- Build a hybrid cardboard rig to test simultaneous sensor inputs and multi-modal user behavior.

&nbsp;  

**\*\*\*Pick one of these display designs to integrate into your prototype.\*\*\***

**\*\*\*Explain the rationale for the design.\*\*\*** (e.g. Does it need to be a certain size or form or need to be able to be seen from a certain distance?)

**\*\*\*Document your rough prototype.\*\*\***

## Joystick Control design (Design #2)

We selected the **Joystick Control design**, which combines a top-mounted APDS gesture sensor with a front joystick. This hybrid setup allows both gesture shortcuts (for quick actions) and tactile control (for precision), allowing users to care for the digital pet in different ways — both physically and emotionally.

## 🧭 Input Function Chart

| Component | Function | Type of Interaction | Example Behavior | Purpose in Design |
|------------|-----------|--------------------|------------------|-------------------|
| 🕹️ **Joystick** | Controls **Feed**, **Play**, **Clean**, **Pet**, and **Drink Water** | Tactile / Directional | Move joystick up to Feed, down to Play, left/right for other actions | Provides **precise, game-like control** for core care actions |
| 🔘 **Button** | Confirm selection / special action (in development) | Tactile / Confirm | Press to confirm feeding amount or start a mini-game | Adds **clear physical confirmation**; reduces accidental actions |
| ✋ APDS Gesture Sensor | Proximity + simple gestures (affection/presence) | Contact-free / Ambient | Gesture up = wake up, gesture down = sleep, hand moving toward sensor = petting (affection) | Creates lifelike, emotional responses (petting, wake/sleep based on attention) |

## Prototype

<img src="https://hackmd.io/_uploads/Sy6AUtzAgl.jpg" width="400"/>



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

#### How To Run This

- make sure speaker is connected
- make sure APDS and joystick sensors are connected
- install requirements

```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 4/tamagochi $ sudo systemctl stop piscreen.service --nowow
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 4/tamagochi $ python tamagotchi_pitft.py
pygame 2.6.1 (SDL 2.28.4, Python 3.11.2)
Hello from the pygame community. https://www.pygame.org/contribute.html
Audio system initialized
Joystick ready
APDS init failed: No I2C device at address: 0x39
Calibrating joystick... (release the stick)
APDS worker skipped (no device)
Center=(513,517)  Scale~1023
...
```


#### Interaction Diagram

##### Data Flow
![Screenshot 2025-10-19 at 11.27.58 AM](https://hackmd.io/_uploads/Bk5tQYzCge.png)


##### input + output

![image](https://hackmd.io/_uploads/ry_itKMCel.png)

##### Multi-input + output

![image](https://hackmd.io/_uploads/ryQTOFMCxg.png)

##### Multi-input + Multi-output
![image](https://hackmd.io/_uploads/HJqudtMRee.png)


#### Interaction Design & Reflections

##### 1. Interaction Complexity & Systems
> Key Insight: 1 + 1 > 2

Multi-input systems aren't just "more inputs" — they create a multiplication effect where interactions become richer than the sum of their parts. When we combined feeding (joystick) with petting (gesture), it created a "moment" that cannot be accomplished by either one action.


Precise control (joystick navigation) + Spontaneous motion (gesture petting) ->  Emergent complexity

Example from our prototype:
Joystick Feed alone      = Dog eats (functional)
Gesture Pet alone        = Dog feels loved (emotional)
BOTH together            = Hand-feeding moment (intimate bonding)

##### 2. How Emotions Are Created
> Learned interactions, with proper rewarding mechanism, feel more natural and intuitive.

After talking to users, we learned there's a high correlation between motivation/attachment in gameplay when there are more than one outputs involved. Simultaneous outputs make the interactions feel more **real**. Especially when there are more than one senses engaged (visual + audio). That is why we decided to use an audio output.

##### 3. Managing Input Conflicts
> Figure out what takes precedence is more important than we thought - it defines the system and the expected interaction.

What happens when someone tries to pet and it tricked the light sensor into thinking it's night time? 

**Short answer: iterations of feature design.** 

We decided to redesign the gesture that will trigger a petting action, that will be compatible with the capability of the sen

---

### Part F

### Record

Document all the prototypes and iterations you have designed and worked on! Again, deliverables for this lab are writings, sketches, photos, and videos that show what your prototype:
* "Looks like": shows how the device should look, feel, sit, weigh, etc.
* "Works like": shows what the device can do
* "Acts like": shows how a person would interact with the device

#### screen prototypes - [looks like]

> We want the device to look like a Tamagotchi, a traditional digital pet toy device.
> Therefore, the screen design will feature a comic-like dog instead of a tech/realistic pet.
> We chose Corgi because that's usually a dog that captures people's attention and they're really cute!

- left: default screen the user will see without giving any interaction. There's also a scoreboard that nudges user to interact with the pet
- right: interaction/response from the pet, along with '+1 :heart:' event effect

<img src="https://hackmd.io/_uploads/B1JFQBmCgx.jpg" style="width: 50%; max-width: 600px;">

<img src="https://hackmd.io/_uploads/Hy9BXSQCxe.jpg" style="width: 50%; max-width: 600px;">



#### device demos - [works like]

1.  video : [single input & single output](https://youtube.com/shorts/1MbfEf6G84s?feature=share)

| Input  | Output (MiniPft Display)|
|--------|--------|
|Joystick - Left | Jump!   |
|Joystick - Right | Move head left to right  |
|Joystick - Up |Poop   |
|Joystick - Down | Shake head (disappointedly) |
|ADPS Proximity - Closer|  |

2.  video : [double input & double output](https://youtube.com/shorts/LqYYOzuW0A4?feature=share)
 
| Input1  | Input2  | Output1 (MiniPft Display)| Output2 (Sound)|
|--------|----------|--------|--------|
|Joystick - Left | ADPS sensor Proximity  | Celebrate! | Bark (Happily)

