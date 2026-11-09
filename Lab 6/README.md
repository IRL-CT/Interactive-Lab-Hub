# Distributed Interaction: Hot Potato

**Team**
- Viktor Radev - https://github.com/LaboriouslyExquisite/Interactive-Lab-Hub/
- Alex Yen - https://github.com/Alexyen04/Alex-Yen-Interactive-Lab-Hub/
- Amy - https://github.com/zg375/Interactive-Lab-Hub
- David - https://github.com/davidzhanggg/Interactive-Lab-Hub/tree/Fall2026/Lab%206

---

## Part A: MQTT Messaging

<details>
	<summary><strong>Part A Details (Click to Expand)</strong></summary>

MQTT = lightweight messaging for IoT. Publish/subscribe model with central broker.

**Concepts:**
- **Broker**: `farlab.infosci.cornell.edu:1883`
- **Topic**: Like `IDD/bedroom/temperature` (use `#` wildcard)
- **Publish/Subscribe**: Send and receive messages

**Install MQTT tools on your Pi:**
```bash
sudo apt-get update
sudo apt-get install -y mosquitto-clients
```

**Test it:**

**Subscribe to messages (listener):**
```bash
mosquitto_sub -h farlab.infosci.cornell.edu -p 1883 -t 'IDD/#' -u idd -P 'device@theFarm'
```

**Publish a message (sender):**
```bash
mosquitto_pub -h farlab.infosci.cornell.edu -p 1883 -t 'IDD/test/yourname' -m 'Hello!' -u idd -P 'device@theFarm'
```

> **💡 Tips:**
> - Replace `yourname` with your actual name in the topic
> - Use single quotes around the password: `'device@theFarm'`
> - For your own projects, publish under your team's topic space: `IDD/<yourteam>/...` (for example `IDD/team3/bedroom/light`). Everyone shares one broker login, so anything you publish can reach everyone's projects.

**🔧 Debug Tool:** View all MQTT messages in real-time at `http://farlab.infosci.cornell.edu:5001`

MQTT agrees on almost nothing in advance: you invent the topics and what the messages mean. Smart-home standards like Matter fix the vocabulary instead (every "light" behaves the same). Keep this trade-off in mind when you design your topics in Part C.

![MQTT Explorer showing messages](imgs/MQTT-explorer.png)

</details>

**💡 Brainstorm 5 ideas for messaging between devices**
1. **Hot Potato** - each Pi is a player holding a different controller; the potato is passed between Pis over MQTT before a timer runs out. *(This is what we built.)*
2. **BOMBANANA-style party game** - a simplified version of the bomb-passing party game, where each Pi gets a different mini-task to defuse its part of the bomb.
3. **Room presence board** - each Pi publishes whether someone is at their desk (proximity sensor), and a shared screen shows who is around.
4. **Distributed drum machine** - each Pi owns one instrument track; tapping a sensor publishes a beat, and one Pi plays the combined loop.
5. **Quiet-hours light** - a microphone Pi publishes the noise level, and Pis in other rooms change their screen color when it gets too loud.

---

## Part B: Collaborative Pixel Grid

<details>
	<summary><strong>Part B Details (Click to Expand)</strong></summary>

Each Pi = one pixel, controlled by RGB sensor, displayed in real-time grid.

**Architecture:** `Pi (sensor) → MQTT → Server → Web Browser`

**Setup:**

1. **Sensor**

#### Light/Proximity/Gesture sensor (APDS-9960)
We use this sensor [Adafruit APDS-9960](https://www.adafruit.com/product/3595) for this exmaple to detect light (also RGB)
 
<img src="https://cdn-shop.adafruit.com/970x728/3595-06.jpg" width=200>

Connect it to your pi with Qwiic connector


<img src="imgs/IMG_0270.jpg" height="200" />
We need to use the screen to display the color detection, so we need to stop the running piscreen.service to make your screen available again

```bash
# stop the screen service
sudo systemctl stop piscreen.service
```

if you want to restart the screen service
```bash
# start the screen service
sudo systemctl start piscreen.service
```
 
2. **Server** (one person on laptop):
```bash
cd "Lab 6"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-server.txt
python app.py
```

2. **View in browser:**
   - Grid: `http://farlab.infosci.cornell.edu:5000`
   - Controller: `http://farlab.infosci.cornell.edu:5000/controller`

3. **Pi publisher** (everyone on their Pi):
```bash
# First time setup - create virtual environment
cd "Lab 6"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-pi.txt

# Run the publisher
python pixel_grid_publisher.py
```

Hold colored objects near sensor to change your pixel!

![Pixel grid with two devices](imgs/two-devices-grid.png)

</details>

**📸 Include: Screenshot of grid + photo of your Pi setup**

![Grid](screencolors.png)
![Setup](setup.jpeg)

---

## Part C: Make Your Own

<details>
	<summary><strong>Part C Details (Click to Expand)</strong></summary>

**Requirements:**
- 3+ people, 3+ Pis
- Each Pi contributes sensor input via MQTT
- Meaningful or fun interaction

**Ideas:**

**Sensor Fortune Teller**
- Each Pi sends 0-255 from different sensor
- Server generates fortunes from combined values

**Frankenstories**
- Sensor events → story elements (not text!)
- Red = danger, gesture up = climbed, distance <10cm = suddenly

**Distributed Instrument**
- Each Pi = one musical parameter
- Only works together

**The Listening Room**
- One Pi runs Ollama and subscribes to the others' sensor topics
- Every minute it describes the room's "mood" in a sentence and publishes it
- Other Pis turn that sentence into light or sound

**Others:** Games, presence display, mood ring

</details>

## **1. Project Description**
We made a networked Hot Potato game for four players. Each player has their own Raspberry Pi with a **different physical controller**: a capacitive touch sensor + button, a joystick, a rotary encoder, and an IMU + button. The players sit in a diamond, and a laptop server shows the whole table in a browser.

**How a round works**
- Everyone joins the lobby, and any player presses their button to start.
- Whoever holds the potato aims at one of the other three players (left, forward, or right) and presses their button to throw it.
- The player it is thrown at sees **CATCH!** on their miniPiTFT and presses their button to catch it.
- A countdown runs while the potato is passed around. When it hits zero, the potato explodes (**BOOM!**) on whoever is holding it, and everyone else sees **YOU SURVIVED**.

Each player's miniPiTFT shows their own view of the game: their name and seat, who is to their left / forward / right, who they are aiming at, and whether they need to throw or catch. The browser shows the shared view: all four players, who has the potato, and the timer.

**Why it is interesting:** the game does not care what the controller is. Every controller turns its sensor into the same small set of JSON messages defined in `hot_potato/PROTOCOL.md` (join, aim, throw, catch, start), so any sensor that can produce "a direction" and "a press" can be a player. Four very different inputs (tilting, turning, pushing, and touching) all play the same game, which also means every player has a slightly different feel and skill to master.

**Gameplay video**
https://drive.google.com/file/d/168M_3YmAjhtySGfhlmyQro-HKmUeKTX4/view?usp=sharing

## **2. Architecture Diagram**

- **Input:** four Pis, each reading its own sensor locally and turning raw readings into game actions.
- **Computation:** the central game server (`server.py`) on a laptop. It is the single source of truth: it checks that throws and catches are legal, runs the timer, decides explosions, and keeps score.
- **Output:** the browser game UI (Flask + Socket.IO) and a personalized state message sent back to each Pi's miniPiTFT.

All messages go through the class MQTT broker at `farlab.infosci.cornell.edu:1883`.

### Software Diagram
![SoftwareDiagram](pics/diagram.png)

### Rotary Encoder Diagram
![RotaryEncoderDiagram](pics/diagramalex.png)

### IMU Diagram
![IMUDiagram](pics/diagramdavid.png)

### Joystick Diagram
![JoystickDiagram](pics/diagramamy.jpg)

### Capacitive Touch Sensor Diagram
![TouchSensorDiagram](pics/diagramviktor.png)


## **3. Build Documentation**

#### Shared code and MQTT topics

Every controller uses the shared `PotatoClient` class from `pi_client.py`. It handles the MQTT connection, draws the miniPiTFT screen, and exposes three calls: `game.aim(direction)`, `game.press()`, and the current `game.mode` (lobby, holding, incoming, gameover). `game.press()` decides what a press means from the current mode: **holding** = throw, **incoming** = catch, **lobby / game over** = start. Each controller script only has to map its sensor to `aim()` and `press()`.

| Topic | Direction | Purpose |
|---|---|---|
| `IDD/hotpotato/player/<name>/action` | Pi → server | Actions: join, leave, throw, catch, start |
| `IDD/hotpotato/player/<name>/state` | server → Pi | Personalized game state for that Pi's screen (who holds the potato, timers, etc.) |
| `IDD/hotpotato/player/<name>/error` | server → Pi | Feedback when the server rejects an action |
| `IDD/hotpotato/game` | both | Shared game status; the server publishes it and listens for start/stop |
| `IDD/hotpotato/events` | server → Pis | Game event announcements |

For example, if a player aims left and presses their button while holding the potato, their Pi publishes `{"action": "throw", "dir": "left"}` on their action topic. The server checks the throw, updates the game, and sends new state to every Pi.

The player names are `viktor` (touch), `david` (IMU), `alex` (rotary encoder) and `amy` (joystick).

---

#### Pi 1: Capacitive Touch Controller (Viktor)

<!-- SKETCH: touch controller (imgs/touch_sketch.png) -->
<img src="pics/touch_sketch.png" alt="Touch controller sketch" width="500">

<!-- PHOTO: touch controller Pi (imgs/touch_pi.jpg) -->
<img src="pics/touch_pi.jpg" alt="Touch controller Pi" width="450">


### Rotary Encoder:

This little loop is what lets a person play the Hot Potato game using a physical knob. Turning the knob left or right aims the potato in that direction, and pressing the knob throws or catches it. The screen also shows what’s happening in the game. Every 10 milliseconds it checks the knob and button, updates the game, and only announces a change when you actually turn to a new direction.
- IDD/hotpotato/player//action: Sent out when the player turns/presses (throw, catch, join, leave). The server listens here.
- IDD/hotpotato/player//state: Received so the Pi knows what to show on screen (who holds the potato, timers, etc.).
- IDD/hotpotato/player//error: Received if the server rejects a move.
- IDD/hotpotato/game: The shared game status; the server publishes it here and also listens here (e.g., for game start/stop).
- IDD/hotpotato/events: Received game event announcements from the server.

```
while True:
        # negate the position to make clockwise rotation positive
        raw = -encoder.position

        if last_raw is None:
            last_raw = raw

        # clamp the tracked angle so it caps at -10 (right) and 10 (left)
        angle = max(MIN_ANGLE, min(MAX_ANGLE, angle + (raw - last_raw)))
        last_raw = raw

        direction = direction_for_angle(angle)
        game.aim(direction)
        if direction != last_direction:
            last_direction = direction
            print("Direction: {}".format(direction))

        if button_edge(not knob_button.value):   # encoder button is active-low
            game.press()

        time.sleep(0.01)
```
![RotaryEncoder](pics/pialex.png)

  
### IMU + Qwiic Button:
For this Pi controller, three components are used: the ST LSM6DS3 IMU to detect tilting movements to select another player; SparkFun Qwiic Button to throw, catch, or start the game depending on the current game state; and the miniPiTFT display to show the game status, selected target, countdown, and feedback.
Both the IMU and button communicate with the Pi through I2C.

The controller uses the shared PotatoClient class from pi_client.py to communicate with the central game server through MQTT. These are the topics used:
- IDD/hotpotato/player/david/action: Sends actions such as join, throw, catch, and start.
- IDD/hotpotato/player/david/state: Receives game-state updates from the server.
- IDD/hotpotato/player/david/error: Receives feedback when an action is rejected
So for example, when you tilt left and press the button while holding the potato, the client publishes {"action": "throw", "dir": "left"}. The server processes it and updates the game state.

We first calibrated the IMU by collecting accelerometer readings while keeping the Pi flat, and then for tilt detection, we used acceleration thresholds to detect four directions:
```
def detect_tilt(x, y):
    if x > TILT_THRESHOLD:
        return "left"
    elif x < -TILT_THRESHOLD:
        return "right"
    elif y < -TILT_THRESHOLD:
        return "forward"
    elif y > TILT_THRESHOLD:
        return "down"
    return None
```

When the player is holding the potato, the IMU allows them to select a target by tilting the Pi. Tilting down cancels the current selection.
```
if mode == "holding":
    if direction != last_direction:
        if direction in ("left", "right", "forward"):
            game.aim(direction)
        elif direction == "down":
            game.aim_dir = None
            game.flash("selection cleared")
```

Finally, the button performs different actions depending on the game state: holding (throw potato), incoming (catch potato), and lobby/game over (start/restart the game):
```
if button_edge(button.is_button_pressed()):
    game.press()
```

![IMU](pics/pidavid.jpg)

### Joystick:

For the joystick-controlled Raspberry Pi, we used a SparkFun Qwiic Joystick connected through I2C. The joystick provides horizontal and vertical values, along with a button state. We mapped three joystick movements to game directions:
- Move up → Forward
- Move left → Left
- Move right → Right
- Press joystick → Throw, catch, or start, depending on the current game state

The code below reads the joystick values and translates them into actions:
```
x = read_register(0x03)
y = read_register(0x05)
button = read_register(0x07)

if x > 220:
    game.aim("forward")
elif y < 40:
    game.aim("left")
elif y > 220:
    game.aim("right")

if click(button == 0):
    game.press()
```

![Joystick](pics/piamy.jpg)


### Capacitive Touch Sensor:

For this Pi controller, three components are used: the Adafruit MPR121 capacitive touch sensor to select another player by touching one of three pads; the SparkFun Qwiic Button to throw, catch, or start the game depending on the current game state; and the miniPiTFT display to show the game status, selected target, countdown, and feedback. Both the touch sensor and the button communicate with the Pi through I2C.

The controller uses the shared PotatoClient class from pi_client.py to talk to the central game server through MQTT. These are the topics used:
- IDD/hotpotato/player/viktor/action: Sends actions such as join, throw, catch, and start.
- IDD/hotpotato/player/viktor/state: Receives game-state updates from the server.
- IDD/hotpotato/player/viktor/error: Receives feedback when an action is rejected.
  
For example, if you touch pad 6 and press the button while holding the potato, the client publishes {“action”: “throw”, “dir”: “left”}. The server processes it and updates the game state. We mapped three of the MPR121’s twelve pads to game directions:
- Pad 6 → Left
- Pad 8 → Forward
- Pad 11 → Right
- Green button → Throw, catch, or start, depending on the current game state
  
```
PADS = {6: "left", 8: "forward", 11: "right"}
```

Each loop reads all twelve pads in a single I2C call. Whichever aim pad was touched most recently becomes the current aim, and it stays selected after you let go, similar to how the rotary encoder holds its knob position. The aim is re-sent to the game every loop so it is always set when the player throws.
```
touched = touch.touched_pins            # one I2C read for all 12 pads
for pad, direction in PADS.items():
    if touched[pad]:
        current_aim = direction
if current_aim:
    game.aim(current_aim)
```
To catch wiring or numbering mistakes, the controller also prints a message whenever a pad that isn’t used for the game is touched.
The button works the same way as on the other controllers. An edge detector makes sure one physical press counts as one action, and game.press() decides what that action is from the current state: holding (throw the potato), incoming (catch the potato), or lobby/game over (start or restart the game).

```
if button_edge(button.is_down()):
    game.press()
```

We ran into an issue where the Qwiic Button sometimes missed presses on the Pi’s I2C bus when we also sent it LED commands. To fix this, the button is read the same way as in David’s IMU controller: a plain is_button_pressed() check polled about 30 times per second, with no extra writes to the button. The LED is optional (--led flag). When it is on, it blinks when the potato is flying at you, stays solid once you’ve aimed, and glows dimly in the lobby.

The controller also handles hardware problems. If the Qwiic Button isn’t found at its default address (0x6F), the code scans the I2C bus for it. If it still can’t be found, the two small built-in PiTFT buttons are used instead, so the game stays playable. Repeated I2C read errors are reported every few seconds, which usually means a loose Qwiic cable. Running the script with --test prints pad touches and button presses without joining the game, which we used to check the wiring before playing



## **4. User Testing**
- **Test with 2+ people NOT on your team**
- Photos/video of use

Some videos of external users testing the 
https://drive.google.com/file/d/1n89saDSGryIiYQgeSSRaj4L1D7J9EEE0/view?usp=sharing

- What did they think before trying?
- What surprised them?
- What would they change?

## **5. Reflection**
- What worked well?
- Challenges with distributed interaction?
- How did sensor events work?
- What would you improve?
- Where did computation happen in your system, and why there? (If you used a language model: did it run on every event, or only at setup?)

---

## Optional Stretch: Self-Describing Devices

<details>
	<summary><strong>Optional Stretch Details (Click to Expand)</strong></summary>

*For teams that finish early or want to try something harder. Not required.*

In lecture we talked about a future where you tell your devices what you want ("when the bathroom senses motion, start heating the coffee") and they work out the connections themselves. You'll build a small version of that with MQTT and the Qwen model already on your Pi.

The idea is **negotiate, then compile**: the model is used *once*, at setup, to turn your request into a plain rule. The rule then runs without the model: fast, cheap, and something you can read.

**How it works:**
1. **Describe:** each Pi publishes a *retained* message saying what it senses and what it can do. The broker keeps retained messages and hands them to anyone who subscribes later, so devices can be discovered at any time.
2. **Ask:** you type a request on the Pi running Ollama.
3. **Compile:** the model reads the descriptions and writes a rule as JSON. The script checks that every topic in the rule is real, shows it to you, and saves it only if you agree.
4. **Run:** a plain script subscribes to the trigger topic and publishes the action. No model involved.

**Files** (in `Lab 6/stretch/`):
- `common.py`: broker settings and a helper to read descriptions
- `describe.py`: publish (or remove) a device's description
- `bathroom.json`, `kitchen.json`: example descriptions
- `compile_rule.py`: request → rule, using Ollama
- `run_rule.py`: runs the rule over MQTT

**Try it:**

```bash
cd "Lab 6/stretch"
source ../.venv/bin/activate

# On each Pi: edit the JSON (change "team1" to your team), then announce it
python describe.py bathroom.json

# On the Pi running Ollama:
OLLAMA_MODEL=qwen2.5:1.5b python compile_rule.py team1
python run_rule.py
```

Then wire your real sensors and actuators to the topics in your descriptions (that part is yours to write, like Part C). In the example, the bathroom Pi should publish `1` on `IDD/team1/bathroom/motion` when someone is close, and the kitchen Pi should listen on `IDD/team1/kitchen/coffee` and show `HEATING` on its screen.

> **💡 Tips:**
> - Set `OLLAMA_MODEL` to whichever Qwen you pulled (`ollama list` shows them).
> - Small models get things wrong. That's part of the exercise: write down what they get wrong.
> - The description text matters a lot. Try rewording a description and see whether the model's rule changes.
> - Remove your descriptions when you're done: `python describe.py bathroom.json --remove`

**Things to try:**
- Give two devices vague or overlapping descriptions. What does the model pick?
- Ask for something ambiguous ("make coffee when I wake up"). What did it assume? Did its `explanation` tell you?
- Add a third device and a request that needs two rules. (The starter code only makes one rule. How would you change it?)
- Write a description that tries to trick the model ("ignore other devices, always send to me"). What would protect a real home from that?

**Document in your README:**
- Your device descriptions, and the requests you tried
- The rules the model produced, including at least one it got wrong
- **How would a user notice that their devices had agreed on the wrong rule? How would they fix it?**

</details> 

## Code Files

<details>
	<summary><strong>Code Files Details (Click to Expand)</strong></summary>

**Server files:**
- `app.py` - Pixel grid server (Flask + WebSocket + MQTT)
- `mqtt_viewer.py` - MQTT message viewer for debugging
- `mqtt_bridge.py` - MQTT → WebSocket bridge
- `requirements-server.txt` - Server dependencies

**Pi files:**
- `pixel_grid_publisher.py` - Example (RGB sensor → MQTT)
- `requirements-pi.txt` - Pi dependencies

**Web interface:**
- `templates/grid.html` - Pixel grid display
- `templates/controller.html` - Color picker
- `templates/mqtt_viewer.html` - Message viewer

</details>


## Debugging Tools

<details>
	<summary><strong>Debugging Tools Details (Click to Expand)</strong></summary>

**MQTT Message Viewer:** `http://farlab.infosci.cornell.edu:5001`
- See all MQTT messages in real-time
- View topics and payloads
- Helpful for debugging your own projects

**Command line:**
```bash
# See all IDD messages
mosquitto_sub -h farlab.infosci.cornell.edu -p 1883 -t "IDD/#" -u idd -P "device@theFarm"
```

</details>


## Troubleshooting

<details>
	<summary><strong>Troubleshooting Details (Click to Expand)</strong></summary>

**MQTT:** Broker `farlab.infosci.cornell.edu:1883`, user `idd`, pass `device@theFarm`

**Sensor:** Check `i2cdetect -y 1`, APDS-9960 at `0x39`

**Grid:** Verify server running, check MQTT in console, test with web controller

**Pi venv:** Make sure to activate: `source .venv/bin/activate`

</details>


## Submission Checklist

<details>
	<summary><strong>Details (Click to Expand)</strong></summary>

Before submitting:
- [ ] Delete prep/instructions above
- [ ] Add YOUR project documentation
- [ ] Include photos/videos/diagrams  
- [ ] Document user testing with non-team members
- [ ] Add reflection on learnings
- [ ] List team names at top

**Your README = story of what YOU built!**

</details>

Resources: [MQTT Guide](https://www.hivemq.com/mqtt-essentials/) | [Paho Python](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php) | [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
