# Skittle Sorter (Lab 4: Feast Automata)

Hold a Skittle up to the webcam. The Pi reads its color, the OLED shows it with a
3-second countdown, and the three servos set the flaps during the countdown. When the
screen flashes **DROP NOW!**, drop the Skittle into the column and it lands in the
right bin.

## Interaction diagram

```
 person holds Skittle      USB webcam + OpenCV         Qwiic OLED              Servo pHAT (3 servos)
 in front of camera   -->  color = R / O / Y / G  -->  "ORANGE  3..2..1"  -->  flaps move to ORANGE path
                           (steady for ~1/3 s)          |                       (during the countdown)
                                                        v
                                                   "DROP NOW!" (screen flashes white)
                                                        |
 person drops Skittle into the column  <----------------'
          |
          v
   TOP flap -> LEFT/RIGHT flap -> bin      tally +1, OLED: "ORANGE #4  next Skittle!"
          |
 camera sees an empty box again  -->  ready for the next Skittle
```

Purple, or anything that isn't R/O/Y/G, shows **Not R/O/Y/G** and the flaps don't move.

## Hardware

| Part | Connection |
|---|---|
| Raspberry Pi (with your Lab 4 setup) | — |
| USB webcam | any USB port (`/dev/video0`) |
| SparkFun Servo pHAT | on the GPIO header, **powered with its own USB-C cable** |
| Servo "top" flap | Servo pHAT channel **0** |
| Servo "left" flap (red/orange) | channel **1** |
| Servo "right" flap (yellow/green) | channel **2** |
| SparkFun Qwiic OLED 128x32 | Qwiic cable into the Servo pHAT's Qwiic port |
| *(optional)* 2nd OLED for the tally | needs a SparkFun Qwiic Mux; both OLEDs are fixed at 0x3C |

Check the I2C bus with `i2cdetect -y 1`. You should see **3c** (OLED) and **40** (Servo pHAT),
plus **70** for the Qwiic Mux if you use one. The Servo pHAT also answers on 0x70 until it is
restarted. `sorter.py` restarts it before talking to the mux, so that overlap is harmless.

## Setup on the Pi

Put the `skittle_sorter` folder inside `Interactive-Lab-Hub/Lab 4/`, then:

```bash
cd ~/Interactive-Lab-Hub/Lab\ 4
source .venv/bin/activate
pip install -r requirements2025.txt          # if you haven't already
pip install opencv-python                     # webcam + color detection
pip install adafruit-circuitpython-tca9548a   # only if you use a Qwiic Mux for 2 OLEDs
cd skittle_sorter
```

## Bring-up order

1. **Servos:** `python sorter.py --test-servos`
   Press Enter to step through RED / ORANGE / YELLOW / GREEN. Adjust `HOME` and `ROUTES`
   in `config.py` until each position sends a Skittle to the right bin. Attach the servo
   horns at the HOME position (60) so you have room either side.
2. **Aim the camera:** `python sorter.py --preview` (needs the Pi desktop or VNC, not plain SSH).
   Hold a Skittle inside the box. The window shows the hue, the label, and a copy of the OLED.
3. **Calibrate:** `python sorter.py --calibrate`
   Use the lighting you'll demo in. It asks for each color in turn and saves `calibration.json`.
4. **Run:** `python sorter.py`. This works headless over SSH. Press Ctrl+C to stop; it prints the final tally.

No hardware handy? `python sorter.py --sim --preview` runs on a laptop webcam with a
virtual OLED drawn under the camera image.

## Tuning (all in `config.py`)

| Problem | Change |
|---|---|
| Red and orange get mixed up | Use brighter white light (desk lamp, LED), then re-run `--calibrate`. A white card behind the Skittle helps a lot. |
| Fingers or skin show up as "orange" | Raise `MIN_SAT` (e.g. 140) or hold the Skittle on a white spoon or tray |
| Doesn't notice the Skittle | Move it closer, increase `ROI_SIZE`, or lower `MIN_COVERAGE` / `MIN_SAT` |
| Locks the color too slowly or too jumpily | `STABLE_FRAMES` (10 ≈ 1/3 s) |
| Change the countdown | `COUNTDOWN_S` (3 s now) |
| Skittle still falling when the flaps go home | Raise `DROP_WINDOW_S` |
| Different mechanism (e.g. 3 trap doors in a row) | Only edit `ROUTES`, which sets each servo's angle for each color |
| OLED is upside down | `OLED_FLIP = True` |

## Files

- `sorter.py` – camera → color → OLED → servos state machine, plus calibrate, servo test, and sim modes
- `config.py` – pins, channels, angles, thresholds, timing
- `calibration.json` – created by `--calibrate`
