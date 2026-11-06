# Hot Potato: make your Pi a player

This guide is for each teammate writing the script for **their** Pi and input.
You only write the part that reads your sensor. Talking to the server and drawing the screen is already done in `pi_client.py`.

| Who | Input | Seat | Script |
|---|---|---|---|
| Viktor | capacitive touch (pads 6 / 8 / 11) + green button | 1 | `pi_touch.py` (done, use it as an example) |
| ? | joystick | 2 | `pi_joystick.py` |
| ? | rotary encoder | 3 | `pi_encoder.py` |
| ? | IMU + button | 4 | `pi_imu.py` |

---

## 1. How the screen stays up to date (data goes both ways)

The server doesn't only receive. It also **sends every Pi its own state**, and it does it by itself. Your Pi never has to ask.

```
   your Pi                         class MQTT broker                     laptop: server.py
 ───────────                       ─────────────────                     ─────────────────
 sensor → game.press() ──publish──▶ IDD/hotpotato/player/<you>/action ──▶ applies the rules
                                                                          (who holds it, timers)
 screen ◀── game.state ◀─(pushed)── IDD/hotpotato/player/<you>/state ◀── publishes your state
```

- **When does the server send?** Immediately whenever anything about you changes (you got the potato, it's flying at you, you exploded…), **plus every 0.5 s during a round** with fresh timers.
- **How does the Pi receive it?** Because you're *subscribed* to your state topic, the broker delivers each message the instant it's published. `pi_client.py` stores it in `game.state`.
- **How does the screen update?** `pi_client.py` redraws the PiTFT about **12 times a second** from the latest `game.state`, and counts the timers down smoothly between messages.
- **Retained:** the last state is kept by the broker, so a Pi that restarts gets its current state right away.

So there's no "read every second" loop to write. Reading only once a second would also be too slow, since you only have **1.5 s to catch**.

A message looks like this (full field list in `PROTOCOL.md`):

```json
{"name": "viktor", "seat": 1, "mode": "holding", "holder": "viktor",
 "targets": {"left": "ana", "forward": "ben", "right": "cy"},
 "time_left": 6.5, "heat": 0.35, "round_left": 21.4, "booms": 1, "max_booms": 3, ...}
```

`mode` is the one that matters most: `lobby`, `waiting`, `incoming`, `holding`, `boom`, `safe`, `gameover`.

---

## 2. Set up your Pi (once)

1. Put the `hot_potato` folder in your `Lab 6` folder on the Pi (copy it from Viktor, or `git pull` once it's pushed).
2. Install the libraries (Lab 6 venv active):
   ```bash
   cd ~/Documents/GitHub/Interactive-Lab-Hub/"Lab 6"
   source .venv/bin/activate
   pip install -r requirements-pi.txt
   pip install sparkfun-qwiic-button sparkfun-qwiic-joystick adafruit-circuitpython-seesaw adafruit-circuitpython-lsm6ds
   ```
   (Only the line for your own sensor really matters.)
3. Free the screen before every run:
   ```bash
   sudo systemctl stop piscreen.service
   ```

---

## 3. The whole API

```python
from pi_client import PotatoClient, Edge

game = PotatoClient("yourname", seat=2, input_name="joystick", aim_hint="push the stick to aim")
game.start()                 # connects, joins, starts drawing the screen

game.aim("left")             # choose a direction ("left" | "forward" | "right"), shown on screen
game.press()                 # the action button:
                             #   holding the potato -> throw where you aimed
                             #   potato flying at you -> catch
                             #   lobby / game over   -> start the game
game.throw("right")          # throw immediately (skips aiming)
game.catch()                 # catch immediately
game.mode                    # "waiting", "incoming", "holding", ...
game.state                   # the full latest message from the server
game.flash("hello!")         # short message at the bottom of the screen
game.stop()                  # leave the game and blank the screen

pressed = Edge()             # turns "button is held down" into ONE event
if pressed(button_is_down):  # True only at the moment it goes down
    game.press()
```

Rules of thumb:
- Use `Edge()` for every button and every "aim" gesture, or you'll send 100 messages a second.
- You can always call `game.press()`. The server decides what it means. If you press catch when nothing is coming you get **butterfingers** (catch locked for 1 s), so don't spam it.
- Directions are **relative to you**: `left` is the person on your left at the table.

---

## 4. Templates per input

Copy one into `hot_potato/pi_<input>.py`, change `NAME` / `SEAT`, run it with `python hot_potato/pi_<input>.py`.
**Check the directions on your own hardware.** Run the Lab 4 test script for your sensor, look at the numbers, and flip signs or thresholds if needed.

### Joystick (SparkFun Qwiic Joystick): push to aim, click the stick to throw/catch

```python
import time
import qwiic_joystick
from pi_client import PotatoClient, Edge

NAME, SEAT = "yourname", 2
js = qwiic_joystick.QwiicJoystick()
js.begin()

game = PotatoClient(NAME, seat=SEAT, input_name="joystick", aim_hint="push the stick to aim")
game.start()
click = Edge()
LOW, HIGH = 200, 824            # values go 0..1023, centre is about 512

try:
    while True:
        x, y = js.horizontal, js.vertical
        if x < LOW:
            game.aim("left")    # swap left/right if it feels backwards
        elif x > HIGH:
            game.aim("right")
        elif y < LOW:           # might be y > HIGH on your stick: check joystick_test.py
            game.aim("forward")
        if click(js.button == 0):   # 0 = pressed on the Qwiic Joystick (check: it prints 1 at rest)
            game.press()
        time.sleep(0.01)
except KeyboardInterrupt:
    game.stop()
```

### Rotary encoder (Adafruit I2C QT encoder, seesaw): turn to aim, push to throw/catch

```python
import time
import board
from adafruit_seesaw import seesaw, rotaryio, digitalio as ss_digitalio
from pi_client import PotatoClient, Edge, DIRECTIONS

NAME, SEAT = "yourname", 3
ss = seesaw.Seesaw(board.I2C(), addr=0x36)
ss.pin_mode(24, ss.INPUT_PULLUP)
knob = rotaryio.IncrementalEncoder(ss)
knob_button = ss_digitalio.DigitalIO(ss, 24)

game = PotatoClient(NAME, seat=SEAT, input_name="encoder", aim_hint="turn the knob to aim")
game.start()
push = Edge()
last = None

try:
    while True:
        pos = -knob.position
        if pos != last:                         # every click of the knob = next direction
            last = pos
            game.aim(DIRECTIONS[pos % 3])       # left -> forward -> right -> left ...
        if push(not knob_button.value):         # value is False while pressed
            game.press()
        time.sleep(0.01)
except KeyboardInterrupt:
    game.stop()
```

### IMU + button (LSM6DS3 + Qwiic button): tilt to aim, button to throw/catch

```python
import time
import board
import qwiic_button
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
from pi_client import PotatoClient, Edge

NAME, SEAT = "yourname", 4
imu = LSM6DS3(board.I2C())
btn = qwiic_button.QwiicButton()
btn.begin()

game = PotatoClient(NAME, seat=SEAT, input_name="imu", aim_hint="tilt to aim")
game.start()
press = Edge()
TILT = 4.0     # m/s^2. Flat is about (0, 0, 9.8). Print imu.acceleration while tilting to pick axes/signs

try:
    while True:
        ax, ay, az = imu.acceleration
        if ay > TILT:
            game.aim("left")
        elif ay < -TILT:
            game.aim("right")
        elif ax > TILT:
            game.aim("forward")
        if press(btn.is_button_pressed()):
            game.press()
        time.sleep(0.01)
except KeyboardInterrupt:
    game.stop()
```

Want throws without a confirm button? Call `game.throw("left")` directly instead of `game.aim(...)`, e.g. a hard flick of the IMU.

---

## 5. What the screen shows (built in)

| `mode` | Screen |
|---|---|
| `lobby` | your name, seat, who sits left / forward / right. Press = start. |
| `waiting` | READY + who has the potato |
| `incoming` | flashing blue **CATCH!** + where it's coming from, then green **GOT IT!** |
| `holding` | potato on yellow → red background, seconds left, and who you're aiming at |
| `boom` | flashing **BOOM!** + reason (held too long / dropped it / time's up) |
| `safe` | phew! + who exploded |
| `gameover` | YOU'RE TOAST or YOU SURVIVED. Press = play again. |

The round timer is the bar along the top, and your lives are the dots in the corner.
To change the look, edit `render_frame()` in `pi_client.py` (test it on a laptop: it's plain Pillow).

---

## 6. Test your script alone

1. On the laptop: `python server.py`, open `http://localhost:5000/<yourname>`, and click **🤖 Bots** to fill the other seats.
2. On the Pi: `python hot_potato/pi_<input>.py`. You appear at the bottom of the laptop view.
3. Press your button in the lobby to start. Bots throw to you (catch them!), and you aim and throw back.
4. The server terminal prints every message from you with `OK` or `REJECTED: <reason>`.

| Problem | Fix |
|---|---|
| Screen stays on the old picture | `sudo systemctl stop piscreen.service`, then rerun |
| `No I2C device at address …` | sensor not plugged in / wrong address: `sudo i2cdetect -y 1` |
| Nothing happens on the laptop | not on Cornell Wi-Fi, typo in your name, or the server isn't running |
| Throws go to the wrong person | flip your left/right in the code, or check you're in the right seat |
| Catching feels impossible | tell Viktor: `FLIGHT_TIME` in `server.py` can go up from 1.5 s |

**Not using Python / `pi_client.py`?** Any MQTT client works: publish JSON to `IDD/hotpotato/player/<name>/action` and subscribe to `.../state`. Exact formats are in `PROTOCOL.md`.
