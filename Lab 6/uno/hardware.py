"""The Pi's screen, buttons and APDS-9960 sensor. Imported only when they are really used."""

import json
import os
import time

COLORS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'colors.json')
HOLD_TO_CALL = 0.3  # seconds. Long enough that a passing swipe doesn't count as a call.
HOLD_TO_PICK = 1.2
LONG_PRESS = 0.8

GESTURES = {1: 'play', 2: 'draw', 3: 'prev', 4: 'next'}


def load_references(path=COLORS_FILE):
    """What this Pi's calibration recorded for each color, or None if it hasn't been calibrated"""
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def color_mix(r, g, b):
    """Share of each channel, so a color reads the same when it's nearer or farther away"""
    total = r + g + b
    return (r / total, g / total, b / total) if total > 0 else None


def classify_color(r, g, b, clear, references=None, min_clear=20):
    """Nearest UNO color, or None if too dark to tell. Uses the calibrated colors if there are any."""
    if clear < min_clear:
        return None
    if references:
        mix = color_mix(r, g, b)
        if mix is None:
            return None
        return min(references, key=lambda color: sum((a - b) ** 2 for a, b in zip(mix, references[color])))
    # Same boosts as pixel_grid_publisher.py: this sensor underreports blue
    r, g, b = r * 1.2, g * 1.2, b * 1.7
    top = max(r, g, b)
    if top <= 0:
        return None
    r, g, b = r / top, g / top, b / top
    if r > 0.65 and g > 0.55 and b < 0.6:
        return 'Y'
    if r == 1:
        return 'R'
    return 'G' if g == 1 else 'B'


def is_confident(r, g, b, references, ratio=2.0):
    """False if the two closest colors are too similar to pick between without asking"""
    mix = color_mix(r, g, b)
    if not references or len(references) < 2 or mix is None:
        return True
    gaps = sorted(sum((a - b) ** 2 for a, b in zip(mix, ref)) ** 0.5 for ref in references.values())
    return gaps[1] >= gaps[0] * ratio


class Display:
    def __init__(self):
        import board
        import digitalio
        import adafruit_rgb_display.st7789 as st7789

        self.backlight = digitalio.DigitalInOut(board.D22)
        self.backlight.switch_to_output()
        self.backlight.value = True
        self.disp = st7789.ST7789(
            board.SPI(),
            cs=digitalio.DigitalInOut(board.D5),
            dc=digitalio.DigitalInOut(board.D25),
            rst=None,
            baudrate=64000000,
            width=135,
            height=240,
            x_offset=53,
            y_offset=40,
            rotation=90,
        )

    def show(self, image):
        self.disp.image(image)


class Controls:
    """Turns gestures, a covered sensor, colors and button presses into game events."""

    def __init__(self, proximity=60, rotation=0):
        import board
        import busio
        import digitalio
        from adafruit_apds9960.apds9960 import APDS9960

        self.button_a = digitalio.DigitalInOut(board.D23)
        self.button_b = digitalio.DigitalInOut(board.D24)
        self.button_a.switch_to_input(pull=digitalio.Pull.UP)
        self.button_b.switch_to_input(pull=digitalio.Pull.UP)
        self.a_down = None
        self.b_down = None

        self.sensor = APDS9960(busio.I2C(board.SCL, board.SDA))
        self.sensor.enable_proximity = True
        self.sensor.enable_color = True
        self.sensor.rotation = rotation
        self.proximity = proximity
        self.mode = None
        self.covered_since = None
        self.seen_color = None
        self.seen_since = 0.0
        self.warned = False
        self.references = load_references()

    def set_mode(self, mode):
        """Each engine holds up the others. Color takes 712 ms a reading, so it only runs for 'pick'."""
        if mode != self.mode:
            self.mode = mode
            self.sensor.enable_gesture = mode == 'turn'
            self.sensor.enable_color = mode == 'pick'
            self.covered_since = None
            self.seen_color = None

    def poll_buttons(self):
        """Returns 'a', 'b' or 'b_long' when a button is let go"""
        now = time.monotonic()
        events = []
        if not self.button_a.value and self.a_down is None:
            self.a_down = now
        elif self.button_a.value and self.a_down is not None:
            self.a_down = None
            events.append('a')
        if not self.button_b.value and self.b_down is None:
            self.b_down = now
        elif self.button_b.value and self.b_down is not None:
            events.append('b_long' if now - self.b_down >= LONG_PRESS else 'b')
            self.b_down = None
        return events

    def poll(self):
        """Returns a list of events: next, prev, play, draw, call, cycle, confirm, cancel, ('pick', color)"""
        presses = self.poll_buttons()
        events = []
        try:
            if self.mode == 'turn':
                code = self.sensor.gesture()
                if code in GESTURES:
                    events.append(GESTURES[code])
            elif self.mode == 'uno':
                events += self.poll_covered()
            elif self.mode == 'pick':
                events += self.poll_color()
        except OSError as e:
            # A loose Qwiic cable shouldn't end the game: the buttons still work
            if not self.warned:
                print(f'[WARN] sensor error, using buttons only: {e}')
                self.warned = True

        for press in presses:
            if self.mode == 'turn':
                events.append({'a': 'next', 'b': 'play', 'b_long': 'draw'}[press])
            elif self.mode == 'uno':
                events.append('call')
            elif self.mode == 'pick':
                events.append({'a': 'cycle', 'b': 'confirm', 'b_long': 'cancel'}[press])
        return events

    def poll_covered(self):
        now = time.monotonic()
        if self.sensor.proximity < self.proximity:
            self.covered_since = None
        elif self.covered_since is None:
            self.covered_since = now
        elif now - self.covered_since >= HOLD_TO_CALL:
            return ['call']
        return []

    def poll_color(self):
        """Hold a colored thing steady near the sensor to choose that color. A close call needs a button."""
        if self.sensor.proximity < self.proximity or not self.sensor.color_data_ready:
            if self.sensor.proximity < self.proximity:
                self.seen_color = None
            return []
        reading = self.sensor.color_data
        color = classify_color(*reading, references=self.references)
        now = time.monotonic()
        if color is None:
            return []
        if color != self.seen_color:
            self.seen_color = color
            self.seen_since = now
            return [('pick', color)]
        if now - self.seen_since >= HOLD_TO_PICK and is_confident(*reading[:3], self.references):
            self.seen_since = now
            return ['confirm']
        return []


def sensor_test():
    """Check each thing the game uses, one at a time, since gestures stall the other readings"""
    controls = Controls()
    sensor = controls.sensor

    print('\n1. SWIPE across the sensor: left, right, up, down, a few times each (20 s)')
    sensor.enable_color = False
    sensor.enable_gesture = True
    end = time.monotonic() + 20
    while time.monotonic() < end:
        code = sensor.gesture()
        if code:
            print(f'   gesture: {GESTURES[code]} (code {code})')
        for button in controls.poll_buttons():
            print(f'   button: {button}')
    sensor.enable_gesture = False

    print('\n2. COVER the sensor with your hand, then take it away, a few times (10 s)')
    end = time.monotonic() + 10
    while time.monotonic() < end:
        print(f'   proximity {sensor.proximity:3d}')
        time.sleep(0.25)

    print('\n3. Hold up each colored object you have, about 5 s each (30 s)')
    sensor.enable_color = True
    end = time.monotonic() + 30
    while time.monotonic() < end:
        r, g, b, c = sensor.color_data
        color = classify_color(r, g, b, c, references=controls.references)
        unsure = '' if is_confident(r, g, b, controls.references) else ' (unsure)'
        print(f'   proximity {sensor.proximity:3d}  rgbc {r:5d} {g:5d} {b:5d} {c:5d}  -> {color}{unsure}')
        time.sleep(0.5)


def calibrate(path=COLORS_FILE, check_seconds=30, samples=20):
    """Record what each color looks like on this Pi, in this room, then try them out"""
    controls = Controls()
    sensor = controls.sensor
    names = {'R': 'RED', 'Y': 'YELLOW', 'G': 'GREEN', 'B': 'BLUE'}
    references = {}
    for color, name in names.items():
        while True:
            answer = input(f'Hold your {name} object where you will hold it in the game, then press Enter (s = no {name} object): ')
            if answer.strip().lower() == 's':
                print(f'   Skipped. {name} can still be chosen with the buttons.')
                break
            readings = []
            nearest = 0
            for _ in range(samples):
                time.sleep(0.1)
                readings.append(sensor.color_data)
                nearest = max(nearest, sensor.proximity)
            if nearest < controls.proximity:
                # This would record the room's light instead of the object
                print(f'   Too far (proximity {nearest}, needs {controls.proximity}). Hold it closer and try again.')
                continue
            r, g, b = (sum(reading[i] for reading in readings) / samples for i in range(3))
            mix = color_mix(r, g, b)
            if mix is None:
                print('   The sensor saw nothing. Check the cable and run this again.')
                return
            references[color] = mix
            print(f'   {name}: red {mix[0]:.2f} green {mix[1]:.2f} blue {mix[2]:.2f}, proximity {nearest}')
            break

    if len(references) < 2:
        print('Need at least two colors to tell apart. Nothing saved.')
        return

    with open(path, 'w') as f:
        json.dump(references, f)
    print(f'Saved to {path}')

    colors = list(references)
    for i, first in enumerate(colors):
        for second in colors[i + 1:]:
            gap = sum((a - b) ** 2 for a, b in zip(references[first], references[second])) ** 0.5
            if gap < 0.05:
                print(f'   Warning: {names[first]} and {names[second]} look almost the same to the sensor. '
                      'Try a more saturated object.')

    print(f'Now try them: hold up each object ({check_seconds} s)')
    end = time.monotonic() + check_seconds
    while time.monotonic() < end:
        r, g, b, c = sensor.color_data
        unsure = '' if is_confident(r, g, b, references) else ' (unsure)'
        print(f'   proximity {sensor.proximity:3d}  -> {classify_color(r, g, b, c, references=references)}{unsure}')
        time.sleep(0.5)
