# Distributed Interaction: Hot Potato

**Team**
- Viktor Radev - https://github.com/LaboriouslyExquisite/Interactive-Lab-Hub/
- Alex Yen - https://github.com/Alexyen04/Alex-Yen-Interactive-Lab-Hub/
- Ziqiao Gao - https://github.com/zg375/Interactive-Lab-Hub
- David Zhang - https://github.com/davidzhanggg/Interactive-Lab-Hub/tree/Fall2026/Lab%206

---

## Part A: MQTT Messaging

**5 ideas for messaging between devices**

1. **Hot Potato** - each Pi is a player holding a different controller; the potato is passed between Pis over MQTT before a timer runs out. *(This is what we built.)*
2. **BOMBANANA-style party game** - a simplified version of the bomb-passing party game, where each Pi gets a different mini-task to defuse its part of the bomb.
3. **Room presence board** - each Pi publishes whether someone is at their desk (proximity sensor), and a shared screen shows who is around.
4. **Distributed drum machine** - each Pi owns one instrument track; tapping a sensor publishes a beat, and one Pi plays the combined loop.
5. **Quiet-hours light** - a microphone Pi publishes the noise level, and Pis in other rooms change their screen color when it gets too loud.

---

## Part B: Collaborative Pixel Grid

<img width="804" height="476" alt="Pixel grid" src="https://github.com/user-attachments/assets/301d559e-2f6f-4059-965a-5598971882c3" />

<img width="1062" height="926" alt="Pi setup" src="https://github.com/user-attachments/assets/e1ee59f4-a47e-43da-9c04-512eebd7bdaf" />

---

## Part C: Hot Potato

### 1. Project Description

We made a networked Hot Potato game for four players. Each player has their own Raspberry Pi with a **different physical controller**: a capacitive touch sensor + button, a joystick, a rotary encoder, and an IMU + button. The players sit in a diamond, and a laptop server shows the whole table in a browser.

**How a round works**
- Everyone joins the lobby, and any player presses their button to start.
- Whoever holds the potato aims at one of the other three players (left, forward, or right) and presses their button to throw it.
- The player it is thrown at sees **CATCH!** on their miniPiTFT and presses their button to catch it.
- A countdown runs while the potato is passed around. When it hits zero, the potato explodes (**BOOM!**) on whoever is holding it, and everyone else sees **YOU SURVIVED**.

Each player's miniPiTFT shows their own view of the game: their name and seat, who is to their left / forward / right, who they are aiming at, and whether they need to throw or catch. The browser shows the shared view: all four players, who has the potato, and the timer.

**Why it is interesting:** the game does not care what the controller is. Every controller turns its sensor into the same small set of JSON messages defined in `hot_potato/PROTOCOL.md` (join, aim, throw, catch, start), so any sensor that can produce "a direction" and "a press" can be a player. Four very different inputs (tilting, turning, pushing, and touching) all play the same game, which also means every player has a slightly different feel and skill to master.

**Gameplay video**

<!-- VIDEO: to make it play inline on GitHub, open this README in the GitHub web editor and drag
     imgs/hot_potato_gameplay.mp4 onto this line. GitHub replaces it with a playable video link. -->
[▶ Watch the gameplay video](imgs/hot_potato_gameplay.mp4)

### 2. Architecture Diagram

<!-- DIAGRAM: architecture (imgs/architecture.png) -->
<img src="imgs/architecture.png" alt="Hot Potato architecture" width="700">

- **Input:** four Pis, each reading its own sensor locally and turning raw readings into game actions.
- **Computation:** the central game server (`server.py`) on a laptop. It is the single source of truth: it checks that throws and catches are legal, runs the timer, decides explosions, and keeps score.
- **Output:** the browser game UI (Flask + Socket.IO) and a personalized state message sent back to each Pi's miniPiTFT.

All messages go through the class MQTT broker at `farlab.infosci.cornell.edu:1883`.

### 3. Build Documentation

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
<img src="imgs/touch_sketch.png" alt="Touch controller sketch" width="500">

<!-- PHOTO: touch controller Pi (imgs/touch_pi.jpg) -->
<img src="imgs/touch_pi.jpg" alt="Touch controller Pi" width="450">

This controller uses three components: the Adafruit MPR121 capacitive touch sensor to select another player by touching one of three pads; the SparkFun Qwiic Button to throw, catch, or start the game depending on the current game state; and the miniPiTFT display to show the game status, selected target, countdown, and feedback. Both the touch sensor and the button connect to the Pi through I2C (Qwiic cables).

We mapped three of the MPR121's twelve pads to game directions:

- Pad 6 → Left
- Pad 8 → Forward
- Pad 11 → Right
- Qwiic button → Throw, catch, or start, depending on the current game state

```python
PADS = {6: "left", 8: "forward", 11: "right"}
```

Each loop reads all twelve pads in a single I2C call. Whichever aim pad was touched most recently becomes the current aim, and it stays selected after you let go, similar to how the rotary encoder holds its knob position. The aim is re-sent to the game every loop so it is always set when the player throws.

```python
touched = touch.touched_pins            # one I2C read for all 12 pads
for pad, direction in PADS.items():
    if touched[pad]:
        current_aim = direction
if current_aim:
    game.aim(current_aim)
```

To catch wiring or numbering mistakes, the controller also prints a message whenever a pad that is not used for the game is touched.

The button works the same way as on the other controllers. An edge detector makes sure one physical press counts as one action, and `game.press()` decides what that action is from the current state.

```python
if button_edge(button.is_down()):
    game.press()
```

We ran into an issue where the Qwiic Button sometimes missed presses on the Pi's I2C bus when we also sent it LED commands. To fix this, the button is read the same way as in David's IMU controller: a plain `is_button_pressed()` check polled about 30 times per second, with no extra writes to the button. The LED is optional (`--led` flag). When it is on, it blinks when the potato is flying at you, stays solid once you've aimed, and glows dimly in the lobby.

The controller also handles hardware problems. If the Qwiic Button is not found at its default address (0x6F), the code scans the I2C bus for it. If it still cannot be found, the two small built-in PiTFT buttons are used instead, so the game stays playable. Repeated I2C read errors are reported every few seconds, which usually means a loose Qwiic cable. Running the script with `--test` prints pad touches and button presses without joining the game, which we used to check the wiring before playing.

---

#### Pi 2: Joystick Controller (Amy)

<!-- SKETCH: joystick controller (imgs/joystick_sketch.png) -->
<img src="imgs/joystick_sketch.png" alt="Joystick sketch" width="500">

<!-- PHOTO: joystick Pi (imgs/joystick_pi.jpg) -->
<img src="imgs/joystick_pi.jpg" alt="Joystick Pi" width="450">

For the joystick-controlled Pi, we used a SparkFun Qwiic Joystick connected through I2C. The joystick provides horizontal and vertical values, along with a button state. We mapped three joystick movements to game directions:

- Move up → Forward
- Move left → Left
- Move right → Right
- Press joystick → Throw, catch, or start, depending on the current game state

The code below reads the joystick values and translates them into actions:

```python
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

---

#### Pi 3: Rotary Encoder Controller (Alex)

<!-- SKETCH: rotary encoder controller (imgs/encoder_sketch.png) -->
<img src="imgs/encoder_sketch.png" alt="Rotary encoder sketch" width="500">

<!-- PHOTO: rotary encoder Pi (imgs/encoder_pi.jpg) -->
<img src="imgs/encoder_pi.jpg" alt="Rotary encoder Pi" width="450">

This loop lets a person play the game using a physical knob. Turning the knob left or right aims the potato in that direction, and pressing the knob throws or catches it. The screen shows what is happening in the game. Every 10 milliseconds the loop checks the knob and button, updates the game, and only announces a change when you actually turn to a new direction.

```python
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

---

#### Pi 4: IMU Controller (David)

<!-- DIAGRAM: IMU controller (imgs/imu_diagram.png) -->
<img src="imgs/imu_diagram.png" alt="IMU diagram" width="500">

<!-- PHOTO: IMU Pi (imgs/imu_pi.jpg) -->
<img src="imgs/imu_pi.jpg" alt="IMU Pi" width="450">

This controller uses three components: the ST LSM6DS3 IMU to detect tilting movements to select another player; the SparkFun Qwiic Button to throw, catch, or start the game depending on the current game state; and the miniPiTFT display to show the game status, selected target, countdown, and feedback. Both the IMU and button communicate with the Pi through I2C.

We first calibrated the IMU by collecting accelerometer readings while keeping the Pi flat. For tilt detection, we used acceleration thresholds to detect four directions:

```python
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

When the player is holding the potato, they select a target by tilting the Pi. Tilting down cancels the current selection.

```python
if mode == "holding":
    if direction != last_direction:
        if direction in ("left", "right", "forward"):
            game.aim(direction)
        elif direction == "down":
            game.aim_dir = None
            game.flash("selection cleared")
```

Finally, the button performs different actions depending on the game state: holding (throw the potato), incoming (catch the potato), and lobby/game over (start or restart the game):

```python
if button_edge(button.is_button_pressed()):
    game.press()
```

---

### 4. User Testing

**Testers:** James and Adam (not on our team)

**Video of James and Adam playing**

<!-- VIDEO: to make it play inline on GitHub, open this README in the GitHub web editor and drag
     imgs/hot_potato_gameplay.mp4 onto this line. GitHub replaces it with a playable video link. -->
[▶ Watch the gameplay video](imgs/hot_potato_gameplay.mp4)

**What did they think before trying?**
At first they thought the game looked complicated. They weren't sure what catching, throwing, or selecting a target meant, and they asked us what class the project was for. After we demoed one round, we handed them the controllers and they picked it up quickly: they won 2 of the 3 rounds they played.

**What surprised them?**
They were surprised to see so many different controllers for one game. They were also bold enough to pick the two hardest ones, the IMU (tilting the whole Pi to aim) and the capacitive touch sensor, and still played well with them.

**What would they change?**
- **The game felt too simple.** Once you know the rules, every turn is the same: aim, press, pass. Testers wanted more ways to make decisions during a turn.
- **Two kinds of throws.** A fast throw and a slow throw, so players can fake each other out and make the catcher react to timing instead of just pressing when they see CATCH!.
- **Hide the timer.** If players cannot see how long they can hold the potato, they are pushed to throw earlier instead of waiting until the last second.
- **Power-ups like Mario Kart.** Random items that can change how a round goes.
- **The capacitive touch controller was finicky.** The loose wire ends on the touch pads would brush the table, which registered as a touch and changed the aim. Because the last touched pad becomes the aim, a stray touch would send the potato to the wrong player.

### 5. Reflection

**What worked well?**
Splitting the system into a shared client and a single server worked well. Because `pi_client.py` handled MQTT and the screen, each person only had to write the part that turned their sensor into `aim()` and `press()`. Writing the message format down in `PROTOCOL.md` early meant we could build four very different controllers in parallel and they all worked with the same server. Keeping the server as the only source of truth also meant the four screens and the browser never disagreed about who held the potato.

**Challenges with distributed interaction?**
- **Shared state:** with four Pis and a browser, every view has to show the same game. We solved this by never letting a Pi change the game itself. Pis only send requests, and the server answers with the new state for everyone.
- **Hardware on a shared I2C bus:** the Qwiic Button missed presses when we also sent it LED commands. We fixed it by only reading the button and making the LED optional.
- **Feedback across the network:** players need to know right away whether their action worked. The error topic and the "CATCH!" screen were added so players are not left guessing.

**How did sensor events work?**
Each Pi turns continuous sensor readings into a few discrete events before anything is sent over the network. The IMU uses tilt thresholds, the joystick uses value thresholds, the encoder tracks a clamped angle, and the touch sensor uses the last touched pad. Every button uses edge detection so one press is one action. Only actions (aim, throw, catch, start) go over MQTT, never raw sensor data, which keeps the network traffic small and the server simple.

**What would you improve?**
- Add the feedback from testing: fast and slow throws, a hidden timer, and power-ups (for example a shield, a speed-up that shortens the countdown, or a reverse that sends the potato back).
- Make the touch controller reliable: put the pads on copper tape on a board instead of loose wire ends, ignore touches when more than one pad is touched at once, and tune the MPR121's touch thresholds.
- Make the controllers handheld and enclosed, so each one feels like an object to pass around instead of a board on a desk.

**Where did computation happen, and why there?**
Sensor processing happens on each Pi, because each sensor is different and only that Pi knows how to read it. Game logic (legal throws, timers, explosions, scores) happens on the laptop server, because the game needs one authoritative state that all players agree on; if each Pi ran its own copy of the rules, they could disagree about who was holding the potato when it exploded. We did not use a language model; every event is handled by plain code, which keeps the game fast enough for quick catches.
