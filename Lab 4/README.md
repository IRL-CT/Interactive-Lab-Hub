
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

## Lab 4 Deliverables

### Part 1 (Week 1)
<details>
	<summary><strong>Submit the following for Part 1:</strong></summary>
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

</details>
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
**Nophar Shalom, Angela Bi**


For lab this week, we focus both on sensing, to bring in new modes of input into your devices, as well as prototyping the physical look and feel of the device. You will think about the physical form the device needs to perform the sensing as well as present the display or feedback about what was sensed. 

<details>
	<summary><strong>Part 1 Lab Preparation</strong></summary>
	Get the latest content:
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
<details>
	<summary><strong>Part A: Capacitive Sensing, a.k.a. Human-Twizzler Interaction</strong></summary>
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

### *️⃣A. Mints Box Capacitive Sensing
<a href="https://drive.google.com/file/d/1o_3bsJ4SPG-J-lyWNZgraCDtJGMWwgW-/view?usp=sharing">
  <img src="mints_touch_sensor.png" alt="Watch the video" width="50%"/>
</a>

### *️⃣B. More sensors

<details>
	<summary><strong>Light/Proximity/Gesture sensor (APDS-9960)</strong></summary>
	
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

### Light Sensor
<a href="https://drive.google.com/file/d/17o3jzOjhaZLSZGRchTLip_6mdbL5KMBl/view?usp=sharing">
  <img src="light_demo.png" alt="Watch the video" width="50%"/>
</a>

### Proximity Sensor
<a href="https://drive.google.com/file/d/1wR2hlbg4L0NEHqKz22Iuk_joZSZ03NmU/view?usp=sharing">
  <img src="proximity_demo.png" alt="Watch the video" width="50%"/>
</a>

### Gesture Sensor
<a href="https://drive.google.com/file/d/1HdXgBWi7IqDgMRbetC-ETP8n4h-rlmix/view?usp=sharing">
  <img src="gesture_demo.png" alt="Watch the video" width="50%"/>
</a>

<details> 
	<summary><strong>Rotary Encoder </strong></summary>
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

<a href="https://drive.google.com/file/d/118q29NelT253OV3SDiViSWC53AV_Uej-/view?usp=sharing">
  <img src="rotary_demo.png" alt="Watch the video" width="50%"/>
</a>

### Joystick
<details>
	<summary>Joystick Instruction</summary>
	
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

<a href="https://drive.google.com/file/d/1omgW6KX0jmCe2UsV1cPgFuCHKB7BV50a/view?usp=sharing">
  <img src="joystick_demo.png" alt="Watch the video" width="50%"/>
</a>

### Distance Sensor
<details>
	<summary>Distance Sensor Instructions</summary>
	
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

<a href="https://drive.google.com/file/d/1wR2hlbg4L0NEHqKz22Iuk_joZSZ03NmU/view?usp=sharing">
  <img src="distance_demo.png" alt="Watch the video" width="50%"/>
</a>


### Part C
### Physical considerations for sensing


Usually, sensors need to be positioned in specific locations or orientations to make them useful for their application. Now that you've tried a bunch of the sensors, pick one that you would like to use, and an application where you use the output of that sensor for an interaction. For example, you can use a distance sensor to measure someone's height if you position it overhead and get them to stand under it.


**Five sketches of different ways you might use your sensor**

<img src="PXL_20251008_170113134.MP.jpg" width=50%>
<img src="PXL_20251008_170528809.MP.jpg" width=50%>
<img src="cattoyremote.jpeg" width=50%>

**What are some things these sketches raise as questions? What do you need to physically prototype to understand how to anwer those questions?**
1. Anti-Roommate Snack Protector
   - How do we conceal the wire and the rasppi so that the roommate wouldn't notice its a trap?
   - How would we make this a more complex prototype in terms of more than just the sensor and sound?
2. Freeze Dance!
   - Where should we place the sensor so that it detects the right amount of movement?
   - How can we make the party machine portable but still sturdy?
3. Candy Motion Dispense
   - How do we use motors to dispense the candy?
   - Where does the sensor have to be placed in order to detect the hand?
4. Gimme a Joke
   - How do we make a button and mini screen inviting/attractive to the user?
   - How do we make the tiny screen interactive?
5. Remote Cat Toy
   - How do we integrate all three input/outputs in a fluid manner?
   - How do we cat-proof the second end of the device?

**Pick one of these designs to prototype.**

We decided to pick Freeze Dance because we thought it was the most exciting and interactive device to prototype. It's a great challenge because we have to detect tiny movements while the music plays, then instantly stop the song and trigger a light or sound. This forces us to combine hardware, software, and a fun user experience. Since it's a party game, it's the most engaging choice for user testing and demos.

### Part D

<details>
	<summary><strong>Physical considerations for displaying information and housing parts</strong></summary>
	
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


**5 designs for how you would physically position your display and any buttons or knobs needed to interact with it.**
<img src="PXL_20251008_210615884.MP.jpg" width=50%>
<img src="NBMetadataCache.jpeg" width=50%>

**What are some things these sketches raise as questions? What do you need to physically prototype to understand how to answer those questions?**

These sketches raised the question of portability; how big or how small do we want our machine to be? Once we answer that question we can discover how to scale the project properly. These sketches also raise the question of how we orient the device; Do we prefer the vertical aspect of height or do we prioritize surface area for stability since it is going to be around lots of movement? Additionally, we need to be sure of our future plans of the device and what other additional features we may want to add, which impacts our decisions on the past two questions.

**Pick one of these display designs to integrate into your prototype.**
**Explain the rationale for the design.** (e.g. Does it need to be a certain size or form or need to be able to be seen from a certain distance?)

We decided to go with the Extra Portable small design so the user can have a party anywhere they go! We sacrificed the surface area for portability as well as the plan of covering the entire box in disco ball surface so it eliminates the need for a flat top to place a possible disco ball. For the size, we chose a device size that is about the span of an extended hand. Additionally, the design we chose is the one with the handle so that it can be picked up pretty easily for on-the-go moves.

**Build a cardboard prototype of your design.**


**Initial Planning**

<img src="PXL_20251008_212954779.MP.jpg" width=50%>

**Handle Prototyping**

<img src="PXL_20251008_213006788.MP.jpg" width=30%>

**Cardboard Prototype**

<img src="PXL_20251008_214438351.MP.jpg" width=50%>

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
<details>
	<summary><strong>Multidevice Code</strong></summary>
	
		import qwiic_proximity
		import time
		import sys
		import statistics
		import vlc
		import yt_dlp
		import os
		YOUTUBE_URL = "https://youtu.be/EPo5wWmKEaI?si=P4iQHYS6ml0Li500"
		TEMP_FILE = "/tmp/video.mp4"
		SAMPLE_WINDOW = 10
		MOVEMENT_THRESHOLD = 5
		CHECK_INTERVAL = 0.4
		
		
		def download_video(url):
		    """Download YouTube video to a local MP4 file using yt_dlp."""
		    print("Downloading video to /tmp/video.mp4 ... (this may take ~30s)")
		    ydl_opts = {
		        'quiet': False,
		        'format': 'best[ext=mp4]/best',
		        'outtmpl': TEMP_FILE,
		        'noplaylist': True,
		    }
		    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		        ydl.download([url])
		    return TEMP_FILE
		
		
		def runExample():
		    print("\nSparkFun VCNL4040 Proximity Sensor + VLC (Local Playback Mode)\n")
		    oProx = qwiic_proximity.QwiicProximity()
		
		    if not oProx.connected:
		        print("The Qwiic Proximity device isn't connected. Please check your connection.", file=sys.stderr)
		        return
		
		    oProx.begin()
		
		    # Step 1: Ensure we have the video locally
		    if not os.path.exists(TEMP_FILE):
		        video_path = download_video(YOUTUBE_URL)
		    else:
		        video_path = TEMP_FILE
		        print("Using cached video:", video_path)
		
		    # Step 2: Play it with VLC
		    print("Starting VLC player...")
		    player = vlc.MediaPlayer(video_path)
		    player.play()
		    time.sleep(5)
		
		    readings = []
		    is_playing = True
		
		    while True:
		        proxValue = oProx.get_proximity()
		        print(f"Proximity Value: {proxValue}")
		
		        readings.append(proxValue)
		        if len(readings) > SAMPLE_WINDOW:
		            readings.pop(0)
		
		        if len(readings) >= SAMPLE_WINDOW:
		            variation = statistics.stdev(readings)
		            print(f"Variation: {variation:.2f}")
		
		            if variation > MOVEMENT_THRESHOLD:
		                if not is_playing:
		                    print("Movement detected: PLAY")
		                    player.play()
		                    is_playing = True
		            else:
		                if is_playing:
		                    print("Stable distance: PAUSE")
		                    player.pause()
		                    is_playing = False
		
		        time.sleep(CHECK_INTERVAL)
		
		
		if __name__ == '__main__':
		    try:
		        runExample()
		    except (KeyboardInterrupt, SystemExit):
		        print("\nExiting program. Cleaning up temporary file.")
		        try:
		            if os.path.exists(TEMP_FILE):
		                os.remove(TEMP_FILE)
		                print("Deleted:", TEMP_FILE)
		        except Exception as e:
		            print("Could not delete temp file:", e)
		        sys.exit(0)
</details>

## Iterative Process
During our design process, we decided to add lights to the device. However, with our cardboard prototype, there wasn't an aesthetic way to portray it well. Thus, we decided to laser cut acrylic for a see-through look, where the colorfulness of the lights and the inside machinery of the device can be seen from the outside without even opening the box. We also included a crochet handle for easy transportation of the device.

The first iteration of the lights:

<img src="lightprototype.jpg" width=50%>

The process of laser cutting:

<img src="lasercutting.jpg" width=50%>

Comparison of our two iterations:

<img src="iterationcomparison.jpg" width=50%>

Take it togo with the handle!

<img src="handle.jpg" width=50%>


- A simple interaction diagram or sketch showing how inputs and outputs are connected and interact

<img src="interactionmap.jpg" width=50%>

- Written reflection: What did you learn about multi-input/multi-output interaction? What was fun, surprising, or challenging?

**Questions to consider:**
- What new types of interaction become possible when you combine two or more sensors or actuators?
	- When combining two or more sensors or actuators new types of interactions arise such as the user having more control of their overall experience as well as an enhanced sense of the device's status and being. For example, with a rotary volume control, the user can control how loud they want their Freeze Dance party to be, rather than it being set on one level. The added lights provide an improved ambiance to the device, allowing the user to also know when it is powered/on.
- How does the physical arrangement of devices (e.g., where the encoder or sensor is placed) change the user experience?
  	- Every sensor has to be physically arranged to provide the user with the easiest, most intuitive experience. We placed our motion sensor in a broad area that is able to capture the most motion without the user having to angle themselves in any particular way. The speaker was also placed on the same side so that the audio projection will be in the direction of the user. The handle and volume were placed at the top so that it can be lifted/modified in an area that doesn't interfere with the main actions of the device.
- What happens if you use one device to control or modulate another (e.g., encoder sets a threshold, sensor triggers an action)?
- How does the system feel if you swap which device is "primary" and which is "secondary"?

<details>
	<summary>Try chaining different combinations and document what you discover!</summary>
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

### Part F

### Record

Document all the prototypes and iterations you have designed and worked on! Again, deliverables for this lab are writings, sketches, photos, and videos that show what your prototype:
* "Looks like": shows how the device should look, feel, sit, weigh, etc.
* "Works like": shows what the device can do
* "Acts like": shows how a person would interact with the device

