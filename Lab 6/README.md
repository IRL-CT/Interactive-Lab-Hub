# Distributed Interaction# Little Interactions Everywhere



**NAMES OF COLLABORATORS HERE****NAMES OF COLLABORATORS HERE**



## Prep## Prep



1. Pull the new changes from the class interactive-lab-hub1. Pull the new changes from the class interactive-lab-hub. (You should be familiar with this already!)

2. Readings before class:2. Install [MQTT Explorer](http://mqtt-explorer.com/) on your laptop. If you are using Mac, MQTT Explorer only works when installed from the [App Store](https://apps.apple.com/app/apple-store/id1455214828).

   * [MQTT](#mqtt-messaging)3. Readings before class:

   * [The Presence Table](https://dl.acm.org/doi/10.1145/1935701.1935800) and [video](https://vimeo.com/15932020)   * [MQTT](#MQTT)

   * [The Presence Table](https://dl.acm.org/doi/10.1145/1935701.1935800) and [video](https://vimeo.com/15932020)

## Overview



This lab introduces **distributed interaction** - building interactive systems where multiple devices communicate and coordinate over a network. You'll learn MQTT messaging and build a collaborative application with your team.## Overview



**Lab Sections:**The point of this lab is to introduce you to distributed interaction. We have included some Natural Language Processing (NLP) and Generation (NLG) but those are not really the emphasis. Feel free to dig into the examples and play around the code which you can integrate into your projects if wanted. However, we want to emphasize that the grading will focus on your ability to develop interesting uses for messaging across distributed devices. Here are the four sections of the lab activity:

- [Part A: Understanding MQTT](#part-a-understanding-mqtt)

- [Part B: Collaborative Pixel Grid Demo](#part-b-collaborative-pixel-grid-demo)A) [MQTT](#part-a)

- [Part C: Design Your Distributed System](#part-c-design-your-distributed-system)

B) [Send and Receive on your Pi](#part-b)

---

C) [Streaming a Sensor](#part-c)

## Part A: Understanding MQTT

D) [The One True ColorNet](#part-d)

### What is MQTT?

E) [Make It Your Own](#part-)

MQTT is a lightweight messaging protocol designed for IoT devices with limited bandwidth. It uses a publish/subscribe model with a central broker.

## Part 1.

#### Key Concepts

### Part A

* **Broker** - Central server that receives and distributes messages### MQTT

  - Our broker: `farlab.infosci.cornell.edu` (port 1883)

  MQTT is a lightweight messaging portal invented in 1999 for low bandwidth networks. It was later adopted as a defacto standard for a variety of [Internet of Things (IoT)](https://en.wikipedia.org/wiki/Internet_of_things) devices. 

* **Client** - Any device that publishes or subscribes to messages

#### The Bits

* **Topic** - Hierarchical message channels (like file paths)

  - Example: `IDD/bedroom/temperature`* **Broker** - The central server node that receives all messages and sends them out to the interested clients. Our broker is hosted on the far lab server (Thanks David!) at `farlab.infosci.cornell.edu/8883`. Imagine that the Broker is the messaging center!

  - You can use any subtopic under `IDD/`* **Client** - A device that subscribes or publishes information to/on the network.

  * **Topic** - The location data gets published to. These are *hierarchical with subtopics*. For example, If you were making a network of IoT smart bulbs this might look like `home/livingroom/sidelamp/light_status` and `home/livingroom/sidelamp/voltage`. With this setup, the info/updates of the sidelamp's `light_status` and `voltage` will be store in the subtopics. Because we use this broker for a variety of projects you have access to read, write and create subtopics of `IDD`. This means `IDD/ilan/is/a/goof` is a valid topic you can send data messages to.

* **Subscribe** - Listen for messages on a topic*  **Subscribe** - This is a way of telling the client to pay attention to messages the broker sends out on the topic. You can subscribe to a specific topic or subtopics. You can also unsubscribe. Following the previouse example of home IoT smart bulbs, subscribing to `home/livingroom/sidelamp/#` would give you message updates to both the light_status and the voltage.

  - Use `#` as wildcard: `IDD/bedroom/#` gets all bedroom messages* **Publish** - This is a way of sending messages to a topic. Again, with the previouse example, you can set up your IoT smart bulbs to publish info/updates to the topic or subtopic. Also, note that you can publish to topics you do not subscribe to. 

  

* **Publish** - Send a message to a topic

**Important note:** With the broker we set up for the class, you are limited to subtopics of `IDD`. That is, to publish or subcribe, the topics will start with `IDD/`. Also, setting up a broker is not much work, but for the purposes of this class, you should all use the broker we have set up for you!

### Testing MQTT on Your Pi



Install requirements in your virtual environment:#### Useful Tooling



```bashDebugging and visualizing what's happening on your MQTT broker can be helpful. We like [MQTT Explorer](http://mqtt-explorer.com/). You can connect by putting in the settings from the image below.

source .venv/bin/activate

cd "Lab 6"

pip install -r requirements.txt![input settings](imgs/mqtt_explorer.png?raw=true)

```



Test publishing a message:Once connected, you should be able to see all the messages under the IDD topic. , go to the **Publish** tab and try publish something! From the interface you can send and plot messages as well. Remember, you are limited to subtopics of `IDD`. That is, to publish or subcribe, the topics will start with `IDD/`.



```bash

mosquitto_pub -h farlab.infosci.cornell.edu -p 1883 \<img width="1026" alt="Screen Shot 2022-10-30 at 10 40 32 AM" src="https://user-images.githubusercontent.com/24699361/198885090-356f4af0-4706-4fb1-870f-41c15e030aba.png">

  -t "IDD/test/yourname" \

  -m "Hello from my Pi!" \

  -u idd -P "device@theFarm"

```### Part B

### Send and Receive on your Pi

Test subscribing to messages:

[sender.py](./sender.py) and and [reader.py](./reader.py) show you the basics of using the mqtt in python. Let's spend a few minutes running these and seeing how messages are transferred and shown up. Before working on your Pi, keep the connection of `farlab.infosci.cornell.edu/8883` with MQTT Explorer running on your laptop.

```bash

mosquitto_sub -h farlab.infosci.cornell.edu -p 1883 \**Running Examples on Pi**

  -t "IDD/#" \

  -u idd -P "device@theFarm"* Install the packages from `requirements.txt` under a virtual environment:

```

  ```

You should see messages from other students!  pi@raspberrypi:~/Interactive-Lab-Hub $ source .venv/bin/activate

  (circuitpython) pi@raspberrypi:~/Interactive-Lab-Hub $ cd Lab\ 6

**✏️ Brainstorm: How could you use messaging for interactive devices? Write down 5 ideas.**  (circuitpython) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 6 $ pip install -r requirements.txt

  ...

---  ```

* Run `sender.py`, fill in a topic name (should start with `IDD/`), then start sending messages. You should be able to see them on MQTT Explorer.

## Part B: Collaborative Pixel Grid Demo

  ```

We've built a real-time collaborative pixel art system. Each Pi becomes one pixel in a shared grid, controlled by its color sensor.  (circuitpython) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 6 $ python sender.py

  >> topic: IDD/AlexandraTesting

### System Architecture  now writing to topic IDD/AlexandraTesting

  type new-topic to swich topics

```  >> message: testtesttest

┌─────────────┐     MQTT      ┌──────────────┐  ...

│  Pi #1      │────────────────│              │  ```

│ (RGB Sensor)│                │   Server     │──► Web Browser* Run `reader.py`, and you should see any messages being published to `IDD/` subtopics. Type a message inside MQTT explorer and see if you can receive it with `reader.py`.

├─────────────┤                │   app.py     │    (Grid Display)

│  Pi #2      │────────────────│              │  ```

│ (RGB Sensor)│      WiFi      └──────────────┘  (circuitpython) pi@raspberrypi:~ Interactive-Lab-Hub/Lab 6 $ python reader.py

├─────────────┤  ...

│  Pi #3...   │  ```

└─────────────┘

```<img width="890" alt="Screen Shot 2022-10-30 at 10 47 52 AM" src="https://user-images.githubusercontent.com/24699361/198885135-a1d38d17-a78f-4bb2-91c7-17d014c3a0bd.png">



### Setup Instructions

**\*\*\*Consider how you might use this messaging system on interactive devices, and draw/write down 5 ideas here.\*\*\***

#### 1. Test Your RGB Sensor (APDS-9960)

### Part C

First, verify your sensor works:### Streaming a Sensor



```bashWe have included an updated example from [lab 4](https://github.com/FAR-Lab/Interactive-Lab-Hub/tree/Fall2021/Lab%204) that streams the [capacitor sensor](https://learn.adafruit.com/adafruit-mpr121-gator) inputs over MQTT. 

python test_apds9960.py

```Plug in the capacitive sensor board with the Qwiic connector. Use the alligator clips to connect a Twizzler (or any other things you used back in Lab 4) and run the example script:



You should see live RGB readings. Try holding colored objects near the sensor!<p float="left">

<img src="https://cdn-learn.adafruit.com/assets/assets/000/082/842/large1024/adafruit_products_4393_iso_ORIG_2019_10.jpg" height="150" />

#### 2. Start the Server (One person on laptop)<img src="https://cdn-shop.adafruit.com/970x728/4210-02.jpg" height="150">

<img src="https://cdn-learn.adafruit.com/guides/cropped_images/000/003/226/medium640/MPR121_top_angle.jpg?1609282424" height="150"/>

```bash<img src="https://media.discordapp.net/attachments/679721816318803975/823299613812719666/PXL_20210321_205742253.jpg" height="150">

python app.py</p>

```

 ```

The server will start on port 5000. Open two browser windows: (circuitpython) pi@raspberrypi:~ Interactive-Lab-Hub/Lab 6 $ python distributed_twizzlers_sender.py

- **Grid Display**: `http://farlab.infosci.cornell.edu:5000` ...

- **Color Controller**: `http://farlab.infosci.cornell.edu:5000/controller` ```



The controller lets you test without a Pi - each browser tab gets a unique pixel!**\*\*\*Include a picture of your setup here: what did you see on MQTT Explorer?\*\*\***



#### 3. Run Publisher on Your Pi**\*\*\*Pick another part in your kit and try to implement the data streaming with it.\*\*\***



Connect your APDS-9960 sensor via I2C, then:

### Part D

```bash### The One True ColorNet

python pixel_grid_publisher.py

```It is with great fortitude and resilience that we shall worship at the altar of the *OneColor*. Through unity of the collective RGB, we too can find unity in our heart, minds and souls. With the help of machines, we can overthrow the bourgeoisie, get on the same wavelength (this was also a color pun) and establish [Fully Automated Luxury Communism](https://en.wikipedia.org/wiki/Fully_Automated_Luxury_Communism).



Your Pi will:The first step on the path to *collective* enlightenment, plug the [APDS-9960 Proximity, Light, RGB, and Gesture Sensor](https://www.adafruit.com/product/3595) into the [MiniPiTFT Display](https://www.adafruit.com/product/4393). You are almost there!

1. Read RGB values from the sensor

2. Publish them to MQTT every 2 seconds<p float="left">

3. Appear as a colored pixel in the grid!  <img src="https://cdn-learn.adafruit.com/assets/assets/000/082/842/large1024/adafruit_products_4393_iso_ORIG_2019_10.jpg" height="150" />

  <img src="https://cdn-shop.adafruit.com/970x728/4210-02.jpg" height="150">

### How It Works  <img src="https://cdn-shop.adafruit.com/970x728/3595-03.jpg" height="150">

</p>

**Data Flow:**

```

Sensor → Pi → MQTT Broker → Server → WebSocket → BrowserThe second step to achieving our great enlightenment is to run `color.py`. We have talked about this sensor back in Lab 2 and Lab 4, this script is similar to what you have done before! Remember to activate the `circuitpython` virtual environment you have been using during this semester before running the script:

```

 ```

**Message Format:** (circuitpython) pi@raspberrypi:~ Interactive-Lab-Hub/Lab 6 $ systemctl stop mini-screen.service

```json (circuitpython) pi@raspberrypi:~ Interactive-Lab-Hub/Lab 6 $ python color.py

{ ...

  "mac": "b8:27:eb:xx:xx:xx", ```

  "r": 255,

  "g": 128, By running the script, wou will find the two squares on the display. Half is showing an approximation of the output from the color sensor. The other half is up to the collective. Press the top button to share your color with the class. Your color is now our color, our color is now your color. We are one.

  "b": 64

}(A message from the previous TA, Ilan: I was not super careful with handling the loop so you may need to press more than once if the timing isn't quite right. Also, I haven't load-tested it so things might just immediately break when everyone pushes the button at once.)

```

**\*\*\*Can you set up the script that can read the color anyone else publish and display it on your screen?\*\*\***

**Grid Layout:**

- Pixels appear in order of joining

- Grid automatically arranges in square layout (e.g., 9 pixels → 3×3 grid)### Part E

- Updates in real-time as sensor values change### Make it your own



### 📸 Document Your ExperienceFind at least one class (more are okay) partner, and design a distributed application together based on the exercise we asked you to do in this lab.



**Include in your README:****\*\*\*1. Explain your design\*\*\*** For example, if you made a remote controlled banana piano, explain why anyone would want such a thing.

1. Screenshot of the pixel grid with your team's pixels

2. Photo of your Pi setup with the RGB sensor**\*\*\*2. Diagram the architecture of the system.\*\*\*** Be clear to document where input, output and computation occur, and label all parts and connections. For example, where is the banana, who is the banana player, where does the sound get played, and who is listening to the banana music?

3. What colors were easiest/hardest for the sensor to detect?

**\*\*\*3. Build a working prototype of the system.\*\*\*** Do think about the user interface: if someone encountered these bananas somewhere in the wild, would they know how to interact with them? Should they know what to expect?

---

**\*\*\*4. Document the working prototype in use.\*\*\*** It may be helpful to record a Zoom session where you should the input in one location clearly causing response in another location.

## Part C: Design Your Distributed System

<!--**\*\*\*5. BONUS (Wendy didn't approve this so you should probably ignore it)\*\*\*** get the whole class to run your code and make your distributed system BIGGER.-->

Now it's time to create your own distributed interactive system!


### Requirements

**Team Size:** 3+ students (each with a Raspberry Pi)

**System Requirements:**
- Use MQTT for communication between Pis
- Each Pi contributes sensor input or interaction
- Create a meaningful or fun collaborative experience
- Design a clear user interface/interaction

### Project Ideas

Here are some starting points (feel free to invent your own!):

#### 1. **Frankenstories Generator**
- Each Pi has a different sensor (gesture, color, distance, buttons)
- Sensor events trigger story elements (not direct text input!)
- Example: Red color = "danger", gesture up = "climbed", distance < 10cm = "suddenly"
- Server combines inputs into collaborative stories

#### 2. **Sensor Fortune Teller**
- Each Pi sends a number (0-255) from any sensor
- Server combines the numbers to generate fortunes
- Different sensors = different fortune aspects (love, career, health)

#### 3. **Distributed Musical Instrument**
- Each Pi controls one aspect (pitch, rhythm, volume, effects)
- Physical gestures/sensors map to musical parameters
- Creates music only when everyone participates

#### 4. **Collaborative Game**
- Example: Distributed Simon Says
- Example: Team-based sensor challenges
- Example: Physical escape room puzzles

#### 5. **Ambient Communication**
- Visualize team activity/presence
- Example: Each person's desk lights show their status
- Example: Shared mood ring for the group

### Design Process

**Step 1: Concept & Roles**
```
What is your system called?
What does it do?
Why would people want to use it?
Who does what? (Assign sensors/roles to each team member)
```

**Step 2: Architecture Diagram**

Draw a clear diagram showing:
- Where are the sensors/inputs?
- Where does computation happen?
- Where are the outputs/displays?
- How does data flow between components?

Label all:
- Hardware components
- Network connections  
- Data transformations

**Step 3: Interaction Design**

Consider:
- How do users know what to do?
- What feedback do they get?
- What happens when someone joins/leaves?
- How do you handle errors or disconnections?

**Step 4: Build & Test**

Start simple:
1. Get basic MQTT communication working
2. Add one sensor at a time
3. Test with 2 Pis before adding the 3rd
4. Refine the interaction based on testing

### 📋 Deliverables

Document in your README:

**1. System Design**
- Name and description of your system
- Why is this interesting/useful/fun?
- Who are the users and what do they experience?

**2. Architecture Diagram**  
- Clear visual showing all components
- Label inputs, outputs, computation, communication

**3. Implementation Details**
- What sensors/hardware does each Pi use?
- What topics do you publish/subscribe to?
- How does the server process the data?

**4. Working Prototype Documentation**
- Photos of each Pi setup
- Video or photos showing the system in use
- Demonstrate that all Pis contribute meaningfully
- Show the complete interaction from start to finish

**5. Reflection**
- What worked well?
- What was challenging?
- What would you improve with more time?
- What did you learn about distributed interaction?

---

## Code Structure

**Core Files:**
- `app.py` - Flask server with WebSocket and MQTT support
- `mqtt_bridge.py` - Connects MQTT messages to WebSocket clients
- `pixel_grid_publisher.py` - Example: RGB sensor → MQTT
- `test_apds9960.py` - Test your color sensor

**Templates:**
- `templates/grid.html` - Fullscreen pixel grid display
- `templates/controller.html` - Web-based color picker for testing

**Old Examples:**
- `old_demos/` - Previous lab examples (for reference)

---

## Tips & Troubleshooting

**MQTT Not Connecting?**
- Check broker address: `farlab.infosci.cornell.edu`
- Use port 1883 (not 8883)
- Username: `idd`, Password: `device@theFarm`

**Sensor Not Working?**
- Run `i2cdetect -y 1` to check I2C devices
- APDS-9960 should appear at address `0x39`
- Enable I2C: `sudo raspi-config` → Interface Options → I2C

**Grid Not Updating?**
- Check server is running: `python app.py`
- Verify MQTT messages are being sent (check server console)
- Try opening controller in browser to test WebSocket

**Need Help?**
- Check the Slack channel
- Review the pixel grid example code
- Ask your teammates or neighbors!

---

## Helpful Resources

- [MQTT Essentials](https://www.hivemq.com/mqtt-essentials/)
- [Paho MQTT Python Docs](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)
