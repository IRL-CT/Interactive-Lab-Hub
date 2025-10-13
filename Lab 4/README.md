

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

