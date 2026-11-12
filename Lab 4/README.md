# Ph-UI!!!

Members: Jaclyn Pham (cqp4), Vasudha Devkota (vd269), Aryan Palave (ap2578)

<details>
<summary><strong>Lab structure and instructions (click to expand)</strong></summary>

## Lab Overview

For lab this week, we focus on both sensing and actuation, bringing new modes of input and output into your devices, while also prototyping the physical structure and overall look of the device. You will consider how the physical form supports sensing and actuation, and how these elements come together to shape the interaction and aesthetics of the device.

---

## Lab Structure

A) [Capacitive Sensing](#part-a)

B) [More Sensors](#part-b)

C) [Servo Actuation](#part-c)

D) [Physical Interaction Design: Feast Automata](#part-d)

E) [Build & Integrate](#part-e)

F) [Final Documentation](#part-f)

---

## Part 1 Lab Preparation

---

### Get the latest content:
As always, pull updates from the class Interactive-Lab-Hub to both your Pi and your own GitHub repo. As we discussed in the class, there are 3 ways you can do so:


Option 1: On the Pi, `cd` to your `Interactive-Lab-Hub`, pull the updates from upstream (class lab-hub) and push the updates back to your own GitHub repo. You will need the personal access token for this.
```
pi@ixe00:~$ cd Interactive-Lab-Hub
pi@ixe00:~/Interactive-Lab-Hub $ git pull upstream Fall2026
pi@ixe00:~/Interactive-Lab-Hub $ git add .
pi@ixe00:~/Interactive-Lab-Hub $ git commit -m "get lab4 content"
pi@ixe00:~/Interactive-Lab-Hub $ git push
```

Option 2: On your own GitHub repo, [create pull request](https://github.com/FAR-Lab/Developing-and-Designing-Interactive-Devices/blob/2021Fall/readings/Submitting%20Labs.md) to get updates from the class Interactive-Lab-Hub. After you have latest updates online, go on your Pi, `cd` to your `Interactive-Lab-Hub` and use `git pull` to get updates from your own GitHub repo.

Option 3: (preferred) use the Github.com interface to update the changes.

---

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

---

### Gathering materials for this lab:

* Cardboard (start collecting those shipping boxes!)
* Found objects and materials--like bananas and twigs.
* Cutting board
* Cutting tools
* Markers


(We do offer shared cutting board, cutting tools, and markers on the class cart during the lab, so do not worry if you don't have them!)

---

### Prototyping References 

* [What do prototypes prototype?](https://www.semanticscholar.org/paper/What-do-Prototypes-Prototype-Houde-Hill/30bc6125fab9d9b2d5854223aeea7900a218f149)
* [Paper prototyping](https://www.uxpin.com/studio/blog/paper-prototyping-the-practical-beginners-guide/) is used by UX designers to quickly develop interface ideas and run them by people before any programming occurs. 
* [Cardboard prototypes](https://www.youtube.com/watch?v=k_9Q-KDSb9o) help interactive product designers to work through additional issues, like how big something should be, how it could be carried, where it would sit. 
* [Tips to Cut, Fold, Mold and Papier-Mache Cardboard](https://makezine.com/2016/04/21/working-with-cardboard-tips-cut-fold-mold-papier-mache/) from Make Magazine.
* [Surprisingly complicated forms](https://www.pinterest.com/pin/50032245843343100/) can be built with paper, cardstock or cardboard.  The most advanced and challenging prototypes to prototype with paper are [cardboard mechanisms](https://www.pinterest.com/helgangchin/paper-mechanisms/) which move and change. 
* [Dyson Vacuum Cardboard Prototypes](http://media.dyson.com/downloads/JDF/JDF_Prim_poster05.pdf)
<p align="center"><img src="https://dysonthedesigner.weebly.com/uploads/2/6/3/9/26392736/427342_orig.jpg"  width="200" > </p>

### Feast Automata Inspirations

* [Simone Giertz - The Breakfast Machine](https://www.youtube.com/watch?v=E2evC2xTNWg) turns an everyday breakfast routine into a deliberately awkward robotic performance.
* [Pee-wee’s Big Adventure - Breakfast Machine](https://www.classhook.com/resources/1295-pee-wee-s-big-adventure-pee-wee-s-breakfast-machine?utm_source=chatgpt.com) An elaborate Rube Goldberg-style machine turns the ordinary routine of making breakfast into a playful mechanical performance.
* [Wallace & Gromit - The Autochef](https://www.google.com/search?sca_esv=66d2cd5ecf989ed9&sxsrf=APpeQnuwAWHrA3R0b1GeoQ4r-spKos3vUQ:1789367781228&udm=7&fbs=ABfTbFVyMZGZf1hfvX9uKjN_-G8cxpBkeIeqYwoCbfNVc4vKE7plZzta63Pe5DpJ3XFR9XzI_yj6fb6bfPt1x_5u3nRcG7tR9jg4Omd7-UnDuaw5i86wRQqe-045kPXObjb1eDS649ikhB0y_hSFYfNioDnA60A2i_oC1IzIZywb7ERnDQqnSx10JnfJEaAauzJXglx4123_vjf0_54bKrF6QjM9ne5i3g&q=Wallace+%26+Gromit+%E2%80%94+The+Autochef&sa=X&ved=2ahUKEwiI0OO3uu2WAxVHEFkFHQ3iAOEQtKgLegQIFRAB&biw=1197&bih=613&dpr=2.5#fpstate=ive&vld=cid:72c3eb07,vid:2igRcGxlshA,st:0)
* [Nik Ramage - Jelly Wobbler](http://www.youtube.com/watch?v=pj2t71q68sY#t=33) makes the simple act of wobbling jelly into a dedicated machine.
* [Zekun Chang - Blah Blah](https://zekunchang.com/portfolio/blah-blah/) is an alcohol machine that presents a playful commentary on drunken behavior.

### Mechanical Prototyping Resource

* [Gear Template Generator](https://woodgears.ca/gear_cutting/template.html) can help you prototype simple gear mechanisms for translating servo motion into physical movement.


---

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

---

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

---

### Part C
### Servo Actuation

Now that you have explored several forms of sensing, add physical output by learning to control a servo motor. Complete the Servo pHAT setup and basic servo test before beginning your interaction design.

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

### Part D
### Physical Interaction Design: Feast Automata

**Feast Automata:** build a device that **transforms ordinary dining rituals into playful physical interactions.** Begin with a familiar experience around eating, drinking, cooking, serving, or sharing food, and explore how sensing and actuation might augment, exaggerate, automate, or reinterpret your dining experience.

In this part, use the sensing techniques from Parts A–B and the servo actuation from Part C to develop a physical interaction.

#### Physical considerations for sensing

Sensors need to be positioned in specific locations or orientations to make them useful for an application. Choose a sensor that fits the dining interaction you want to explore. For example, a distance sensor could detect when a cup is placed on a coaster; where the sensor is positioned determines what it can reliably detect.

Think about how the larger object needs to be shaped so the sensor can work reliably, where the actuator needs to sit, what moves, and how a person encounters the interaction.

#### Physical Form and Housing

Think about how your sensor, actuator, and electronics are physically arranged within your prototype. Consider where components need to be placed, what parts move, how the device is supported or enclosed, and how the overall form and aesthetics shape the interaction.

Use cardboard, paper, found objects, or other low-fidelity materials to quickly prototype the physical structure before refining your final design.

#### Optional Display Feedback: Qwiic OLED

Your kit includes these [SparkFun Qwiic OLED screens](https://www.sparkfun.com/products/17153). These use less power than the MiniTFTs you have mounted on the GPIO pins of the Pi, but, more importantly, they can be more flexibly mounted elsewhere on your physical interface. The way you program this display is almost identical to the way you program a  Pi display. Take a look at `oled_test.py` and some more of the [Adafruit examples](https://github.com/adafruit/Adafruit_CircuitPython_SSD1306/tree/master/examples).

<p float="left">
<img src="https://cdn.sparkfun.com//assets/parts/1/6/1/3/5/17153-SparkFun_Qwiic_OLED_Display__0.91_in__128x32_-01.jpg" height="200" />

</p>


As you develop your Feast Automata concept, consider where the sensor and actuator need to be placed, what parts move, how electronics are housed, and how the overall form and aesthetics support the interaction.

**answers in the next section**

</details>

### Concept and artistic motivation

**Feast on Your Life** is an interactive dining table inspired by the closing invitation of Derek Walcott’s poem *Love After Love*: to sit with oneself and welcome one’s own life. The study sheet is titled *Sit. Feast on your life.* The familiar gestures of a meal — walking up to the table, reaching for a cup, touching a spoon — become the way a memory arrives.

Engraved outlines of plates and utensils sit in the surface as quiet landmarks. Coming close makes light bloom along those lines. Touching a conductive detail plays a sound from the diner’s own life: a loved one’s voice, a remembered place, or an everyday sound that carries personal meaning.

The motivation is to make memory feel present at the table. The Pi, the sensors, and the speaker live inside the table, and ordinary actions are what compose the experience. Light is a memory gradually coming into awareness. Sound lets the past briefly share the meal. A small servo-driven motion, such as a paper shade opening with the light, gives that response a physical gesture.

The work asks: **What might it mean to sit down and feast on the experiences, relationships, and memories that have made you who you are?** The dining table becomes an intimate archive, opened by the diner’s presence and by their touch.

Two signals carry the piece:

| Gesture | Sensor | Response |
| --- | --- | --- |
| Approaching the place setting | SparkFun VCNL4040 proximity | A slow glow along the engraved outline, and a small shade that opens with the light |
| Touching a spoon or an engraved conductive detail | MPR121 capacitive pad | A remembered sound from a speaker under the table |

![Five arrangement sketches for Sit. Feast on your life.](<Lab4 sketches.png>)

---

### What I have already built

The touch-to-sound half of the table already runs. In these tests, Twizzlers stand in for spoons and other conductive tableware. Anything conductive can be clipped to the MPR121. The light half runs as a pattern on its own. Connecting that pattern to the proximity sensor is the next step.

#### How the sound prototypes work

All three music scripts use the same chain.

1. The Adafruit MPR121 sits on the Qwiic I2C bus and reports whether each pad is touched.
2. The main loop reads the pads about every 10 ms. It watches the *edge*: a new touch cues a part, and a release cuts it. Holding the Twizzler does not retrigger the sound on every loop.
3. A `sounddevice` stream plays audio continuously at 44.1 kHz, in blocks of 512 samples. A sample counter advances whether or not anyone is touching. The position in the piece is that counter wrapped around the length of the loop.
4. Each part has its own gain. A touch fades the part in; a release fades it out. The fade keeps the entrance from clicking.

Because the clock never waits for a touch, a part that comes in late still lands on the beat. That is the behavior I want at a table, where a hand arrives in the middle of something already underway.

Each orchestral voice is synthesized in the audio callback: a stack of sine harmonics, an envelope, and one detail that gives the instrument its color. The violin has a little bow noise, the oboe has a short reed chirp, and the timpani pitch falls after the strike.

#### Orchestration

Seven pads, one section each:

| Pad | Part | Role |
| --- | --- | --- |
| 0 | violin | the tune |
| 1 | viola | inner voice |
| 2 | cello | the bass |
| 3 | flute | the tune, an octave up |
| 4 | horn | sustained harmony |
| 5 | timpani | the pulse |
| 6 | oboe | a countermelody |

**Grieg, *In the Hall of the Mountain King*.** [`mountain_king_orchestra.py`](mountain_king_orchestra.py) loops the march at 126 BPM in B minor. The grid is a sixteenth note, so the tune can stay short and pointed. Melody parts are staccato: the last quarter of each note is silence. Gain fades over about a tenth of a second.

[Grieg demo](https://youtu.be/P1fQQIjCXBU?si=kRvnSZQhSEFEwfpU)

**Beethoven, *Ode to Joy*.** [`twizzler_orchestra.py`](twizzler_orchestra.py) uses the same seven pads and the same clock, at 100 BPM in C major. The grid is an eighth note, and the flute doubles the violin an octave higher. This pass checked that the same conducting gesture still works on a lyrical line.

[Beethoven demo](https://www.instagram.com/p/DegK7smFazw/?img_index=2)

The cue itself is small. `want[i]` is the only message the audio thread needs:

```python
down = bool(mpr121[i].value)
if down and not held[i]:
    held[i] = True
    orchestra.want[i] = True   # fade this section in, on the current beat
elif not down and held[i]:
    held[i] = False
    orchestra.want[i] = False  # fade it out; the clock keeps going
```

#### DJ version

[`twizzler_dj.py`](twizzler_dj.py) is the same touch-to-layer idea on a house beat: 120 BPM, A minor, six pads.

| Pad | Part | What it plays |
| --- | --- | --- |
| 0 | kick | four on the floor |
| 1 | hats | offbeats, with an open hat at the end of the bar |
| 2 | clap | beats 2 and 4 |
| 3 | bass | one bar in A minor |
| 4 | chord | an A-minor stab on the offbeats |
| 5 | arp | A-minor pentatonic, in sixteenth notes |

The fade is shorter here, about 20 ms, so a pad feels like a mute on a mixer. Bringing parts in one at a time shows that several touches can share one clock and still read as a single piece.

[DJ demo](https://www.instagram.com/p/DeQE2kgjGT3/?img_index=1)

#### Light pattern

I tested LED patterns separately from the sound. The pattern runs on its own; distance does not change it yet.

[Light pattern demo](https://www.instagram.com/p/Dej_RV5I2Bo/)

The next step is the SparkFun VCNL4040, the same proximity sensor as [`qwiic_distance.py`](qwiic_distance.py) and [`windmill_coaster.py`](windmill_coaster.py). It reports a proximity value that rises as a hand or cup gets closer, out to about 20 cm. In the coaster example, crossing a threshold starts a servo. On this table, that value should drive brightness through a slow ramp and a low ceiling, so the engraving brightens as someone sits down. The same reading can move a servo a short distance, opening a paper shade as the light rises and closing it when the hand leaves.

#### What these tests imply for the table

The Twizzlers were clipped straight to the MPR121, so each touch was a bare conductive object. A spoon on the finished table is copper tape under a thin top, or a conductive inlay in the engraving. The cardboard section has to try a real top thickness. If the cover is too thick, the touch will not register.

The orchestra and the DJ also showed that one pad can be one layer, and that layers can be live together. For the meal, each conductive detail plays one remembered sound through the speaker under the table. The fade that keeps a violin from clicking is the same fade that lets a voice arrive gently. Approach controls the light. Touch controls the sound. They can start at different moments.

---

### Questions the sketches raise

The five drawings hold the sensor, the light, the touch point, and the speaker in different places. The open questions follow from those placements.

- Can the SparkFun VCNL4040 reliably detect a hand or dinnerware near the table, and where should it sit? It needs a clear view of the target, so an opaque tabletop will block it.
- How do plate material, color, angle, and placement affect the sensor readings?
- Will a WS2812B strip look like a soft glow when it is hidden in a channel under tracing paper or another diffuser, or will individual LED dots show through?
- Can a touch on the spoon, or on an engraved conductive detail, trigger the intended personal sound without accidental activations?
- How can the Pi, speaker, sensor, and LED wiring be enclosed safely, away from food and spills?
- What small movement could make the interaction feel like a ritual? A slow shade is the candidate. A snap from closed to open would feel like a mechanism announcing itself.

---

### What I need to prototype

I will build a small tabletop section from cardboard or foam board, with one plate, one spoon, and the sensor and light in their intended positions. I will cut an opening for the VCNL4040 so it can see the diner’s hand or a nearby cup. I will place a short WS2812B strip under tracing paper or a translucent cover and test whether the light diffuses evenly.

I will also test the existing touch-to-sound interaction at the spoon, then add a small servo that gently opens a paper flap or light-shade when someone approaches. I will try different sensor angles and distances, and record which dinnerware materials and positions produce useful readings.

Concretely, the section has to answer four checks:

1. **Sight line.** Readings from [`qwiic_distance.py`](qwiic_distance.py) with an empty setting, a hand, a cup, and a plate, at a few angles. The useful range is the gap between “someone is sitting nearby” and “a hand is over this place.”
2. **Diffusion.** A short LED run under tracing paper, at a low brightness, viewed from a seated position. Success is a continuous glow along the engraving.
3. **Touch through a top.** One MPR121 channel on copper tape at the spoon, under the same top thickness as the model. Success is one sound per deliberate touch, using the edge detect already in the orchestra scripts.
4. **Shade.** A 9 g servo on channel 0 of the Servo pHAT, powered from the pHAT’s USB-C supply, moving a paper flap a short arc as proximity rises and returning when the reading falls. The Pi keeps its own supply. Servos do not run from the Pi’s 5V rail.

The Pi, the Servo pHAT, the speaker, and the wiring sit in the cavity under the top. Food stays on the surface above them.

---

### Design I will prototype: The Living Inlay

I will prototype the **Living Inlay**, sketch 03. It is the arrangement that matches a dining table with engraved tableware and hidden technology.

From above, the diner sees engraved ware and a fine line of light. Under the surface sit the MPR121, the speaker, and the LEDs. The VCNL4040 rises through a small opening so it has a clear view, and that opening is meant to disappear into the engraving. Touching the spoon plays a sound from the diner’s life. As they come close, the engraving brightens, and a servo-operated paper shade opens slightly with the light.

I chose this design because the table surface stays visually calm, and the light and the movement feel as though they come from inside it. One small section can test the three physical questions that decide whether the piece works: sensor visibility, light diffusion, and where each component sits. The larger arrangements (a shared bowl, a lantern centerpiece, a runner for several place settings) depend on those answers.

The other four sketches stay useful as comparisons:

| Sketch | Where the sensor and light sit | What it is good for |
| --- | --- | --- |
| 01 The Remembering Place | Sensor at the rim of one setting, halo around the plate | A first check of “can it see past the plate?” |
| 02 The Common Table | Sensor at a shared bowl, light along paths to each seat | Several diners, and the risk of triggering from someone merely sitting nearby |
| 03 The Living Inlay | Electronics under the top, sensor through a small opening | The calm surface, and a real test of cover thickness and diffusion |
| 04 The Memory Lantern | Light above the table, in a paper shade | Whether a slow, dim fade feels intimate |
| 05 The Portable Memory Runner | Three modules on a removable runner, one pod for the Pi | Alignment, and whether neighboring sensors fire on the wrong setting |

Sketch 04’s fade is part of the inlay even though the lamp moves under the table: low brightness, slow rise, slow fall. Sketch 01 is the fallback if the inlay’s opening cannot see the hand. I can learn that from the same cardboard section by aiming the sensor at the rim instead of up through the top.

---

<details>
<summary><strong>Part 2 lab instructions (click to expand)</strong></summary>

## Part 2

Following exploration and reflection from Part 1, complete the "looks like," "works like" and "acts like" prototypes for your design, reiterated below.

---

### Part E

#### Build & Integrate: Sensing + Actuation

For Part 2, build the Feast Automata interaction you developed in Part D by connecting sensing/input to physical actuation.

**Your prototype should:**
- Use at least one sensing or input device.
- Use servo-based physical actuation.
- Connect sensing and actuation into a meaningful interaction around eating, drinking, cooking, serving, or sharing food.
- Additional inputs, displays, LEDs, buttons, or other outputs are optional extensions.

**Document your system with:**
- Code for your sensing + actuation prototype
- Photos and/or video of the working prototype in action
- A simple interaction diagram or sketch showing how sensing and actuation are connected
- Written reflection: What did you learn about connecting sensing, movement, and physical form? What was fun, surprising, or challenging?

**Questions to consider:**
- How does your chosen sensor or input shape the physical response?
- How does the physical arrangement of the sensor and actuator change the interaction?
- What thresholds, timing, or movement patterns make the interaction feel clear or playful?
- What changes when you adjust the sensor placement or servo motion?

Iterate on the sensing, movement, and physical form, and document what you discover.

See encoder_accel_servo_dashboard.py in the Lab 4 folder for an optional example of chaining together three devices.

**`Lab 4/encoder_accel_servo_dashboard.py`**

#### Example Application: Windmill Coaster

Now that you have explored both sensing and actuation, here is a simple example that combines the two.

The **Windmill Coaster** uses a Qwiic distance/proximity sensor to detect when a cup is placed on a coaster. When the cup is detected, a servo motor animates a small windmill by sweeping it back and forth, turning an ordinary action during drinking into a playful physical interaction.

<p align="center">
    <img src="windmill_coaster11.gif" alt="Windmill Coaster Demo" width="400"/>
</p>


This example demonstrates a simple interaction pipeline:

**cup placed → distance sensor detects cup → servo actuates windmill**

Connect the Qwiic distance sensor to the Pi and connect the servo to Channel 0 of the Servo pHAT. Make sure the Servo pHAT is powered through its USB-C connection.

Run the example script:

```bash
python windmill_coaster.py
```

The script continuously reads the proximity value from the distance sensor. When the value passes a threshold, the servo begins animating the windmill. When the cup is removed, the servo stops and returns to its resting position.

You may need to adjust `CUP_THRESHOLD` in [`windmill_coaster.py`](windmill_coaster.py) depending on the size of your cup and the physical placement of the sensor. You can run `qwiic_distance.py` first to compare readings with and without a cup.

Use this example as a starting point. Change the sensor, movement, physical form, or dining interaction to create your own Feast Automata variation.

#### Optional Extensions

The following examples are optional resources if you want to add more inputs or outputs to your prototype.

##### Using Multiple Qwiic Buttons: Changing I2C Address (Physically & Digitally)

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

##### PCF8574 GPIO Expander: Add More Pins Over I²C

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


---

---

### Part F

### Final Documentation

Document all the prototypes and iterations you have designed and worked on! Again, deliverables for this lab are writings, sketches, photos, and videos that show what your prototype:
* "Looks like": shows how the device should look, feel, sit, weigh, etc.
* "Works like": shows what the device can do
* "Acts like": shows how a person would interact with the device

</details>

### Part F

### Final Documentation

#### Tinfoil Concerto

**Tinfoil Concerto** is built from the earlier sound and sensing tests. It is a small dining table for one. Ode to Joy loops in C major at 100 BPM, and every layer meets in one speaker. The score and the instrument voices come from [`twizzler_orchestra.py`](twizzler_orchestra.py). The table that joins them is [`table_orchestra.py`](table_orchestra.py).

Earlier passes are documented above: the Grieg march, the Ode to Joy Twizzler orchestra, the house-beat DJ, and the light pattern. Those tests used Twizzlers as stand-ins for spoons. In the final piece the conductive tableware is tinfoil, and three sensors share one clock so a late gesture still lands on the beat.

**Note.** A servo under the table is meant to bloom a flower as the conductor comes into range of the distance sensor. The motion is written into [`table_orchestra.py`](table_orchestra.py): the flower sweeps while someone is close and rests when they leave. On the day of filming the servo did not run. The video below shows the sound without that bloom. We will submit a revised video once the flower is working.

[![Tinfoil Concerto final demo](https://img.youtube.com/vi/-xJ-nx6M46k/hqdefault.jpg)](https://youtu.be/-xJ-nx6M46k?si=GdRVrztpEzLHYCjd)

[Sensor-by-sensor walkthrough](https://www.instagram.com/p/DeqIdZ1jF_7/?img_index=1)

#### Looks like

The diner sees a place setting, not a circuit. Pieces of tinfoil tableware sit on the surface where a hand would naturally land: a spoon, a cup, a plate. The Raspberry Pi, the MPR121, and the speaker stay under the table. The SparkFun VCNL4040 watches the approach from the setting. The Adafruit APDS-9960 looks up from beneath one object, so the opening reads as part of the ware. A paper flower on a servo is the one moving part, meant to open as someone sits down. In the filmed version that flower stays still.

#### Works like

Three sensors write into one mix. The audio callback never reads a sensor. The main loop only sets targets, and each part fades in and out on the shared clock.

| Action | Sensor | What joins the piece |
| --- | --- | --- |
| Approaching the table | SparkFun VCNL4040, about 20 cm | The bass harmony builds: cello, then cello and viola, then cello, viola, and horn. It also grows louder. The flower servo is meant to sweep here. |
| Holding a piece of tableware | MPR121 capacitive touch | One higher line, at full level, for as long as the foil is held |
| Letting go | MPR121 | Only that line fades. Viola and horn can remain if the person is still close enough for the distance bed. |
| Circling one object | Adafruit APDS-9960 | A C major drone (C, E, G). The place of the hand around the rim brightens the fifth, the octave, or the third. A still hand is silent. The tone rings briefly after the circle stops. |

The tinfoil is clipped to six pads:

| Pad | Instrument |
| --- | --- |
| 1 | violin |
| 3 | flute |
| 5 | oboe |
| 6 | timpani |
| 8 | viola |
| 10 | horn |

Notes written below middle C are played one or two octaves higher, in the same key, so the small speaker can produce them. The timpani is a struck drum on those lifted pitches. At startup the script measures the empty table, so the distance harmony and the drone stay silent until someone actually arrives.

#### Acts like

Someone walks up to a quiet table. As they come closer, the distance sensor hears them and builds the harmony from the bottom: cello, then viola, then horn, louder as they sit. The flower is meant to bloom with that approach. On the filmed day it did not, so the arrival is carried by the harmony alone.

Their hands find the tableware. Holding a piece brings in a brighter voice, the violin, the flute, the oboe, or the timpani, and letting go fades only that voice. The low harmony can keep going underneath if they remain seated close.

One object asks for a slower hand. Resting on it does nothing. Circling it, the way a mallet wakes a singing bowl, rings a soft chord in the same key as Ode to Joy. Moving around the rim changes which harmonic is bright, and the tone lingers for a moment after the circle stops.
