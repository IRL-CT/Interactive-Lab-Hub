"""
Pan Burger: the pan.

One Pi = one pan. It reads
  * the 6-DoF IMU (LSM6DS3TR-C), with the pan held flat:
        tilt right (> 45 deg, then back)  -> next mode
        tilt left                         -> previous mode
        modes: grill -> board -> assembly -> grill ...
        grill:    flip = toss it up,  toss = swing it forward (to your partner)
        board:    chop = a sharp chop down
        assembly: scan cards in burger order
  * the APDS-9960: a card held in front of it is an ingredient
and publishes what happened over MQTT. The laptop (server.py) is the referee.

    ~/venv/bin/python pan.py --player p1               # play
    ~/venv/bin/python pan.py --player p1 --debug       # print every motion it sees
    ~/venv/bin/python pan.py --calibrate               # measure all card colours
    ~/venv/bin/python pan.py --calibrate meat          # re-measure just some cards
    ~/venv/bin/python pan.py --player p1 --no-mqtt     # just print, don't send

Gesture thresholds come from recordings/motion_20261103_193039.csv (record_motion.py).
If the sensor is mounted differently, record again and adjust AXES / thresholds.
"""

import argparse
import json
import math
import os
import sys
import threading
import time
from collections import deque

G = 9.81

# Which axis is which, for the way the board is mounted in the pan.
#   held flat: gravity on +Z     tilting left/right: gravity moves onto Y
#   forward swing: X             flip rotates about Y
AXES = dict(up='az', side='ay', forward='ax', flip_rot='gy')
TILT_RIGHT_IS_NEGATIVE_Y = False  # if left and right come out swapped, flip this

MODES = ['grill', 'board', 'assembly']

# Gestures (from the recording, see README for the numbers)
TRIGGER_A = 15.0        # |a| above this starts looking at a gesture
WINDOW_BEFORE = 0.10    # seconds of samples kept from before the trigger
WINDOW_AFTER = 0.35     # seconds collected after the trigger
FLIP_MIN_A = 20.0       # flips peaked at 26-30
FLIP_MIN_ROT = 5.0      # |gy| 6.7-10.1 when flipping, <= 2.1 when wandering
TOSS_MIN_FORWARD = 9.5  # |ax| 11.7-18.2 when tossing, <= 7.4 when flipping
CHOP_MIN_A = 16.0       # chops hit 17-70; wandering stayed <= 16.4 except one bump
GESTURE_COOLDOWN = 0.35
AFTER_MODE_LOCK = 0.5   # ignore gestures right after a mode switch

# Tilt to switch modes
TILT_ON = 45.0          # degrees of roll that count as a tilt (flips/tosses stay < 35)
TILT_OFF = 20.0         # must come back this close to flat before the next tilt
TILT_HOLD = 0.05        # roll must stay past TILT_ON this long (5 samples)
TILT_MAX_DYNAMIC = 3.0  # only trust the roll angle when |a| is within 3 m/s^2 of g
TILT_REFRACTORY = 0.8   # after a switch, ignore tilts this long: swinging back past
                        # flat overshoots and used to count as a tilt the other way
TILT_REARM = 0.2        # and stay near flat this long before the next tilt counts

# Cards
PROX_ON_DEFAULT = 40
PROX_ON_MIN = 20        # never more sensitive than this, or a passing hand reads as a card
PROX_OFF_RATIO = 0.5
LAMP_SETTLE = 0.3       # screen to white (~30 ms) + throw away one reading + one fresh (0.1 s each)
CARDS = ['bun', 'cheese', 'lettuce', 'meat']      # no plate card: the server sets out the plate
CARD_NAMES = {'bun': '麵包', 'cheese': '起司', 'lettuce': '菜', 'meat': '肉'}

MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS_FILE = os.path.join(HERE, 'cards.json')


# ------------------------------------------------------------------ motion --

class MotionDetector:
    """Feed it IMU samples; it returns ('mode', ...) and ('gesture', ...) events.
    No hardware in here, so it can be replayed on recorded CSVs."""

    def __init__(self, debug=False, tilt=False):
        self.debug = debug
        self.use_tilt = tilt              # default: the PiTFT buttons switch modes
        self.mode = 'grill'
        self.started = False
        self.recent = deque()             # samples from the last WINDOW_BEFORE s
        self.capture = None               # samples of a gesture being collected
        self.capture_until = 0
        self.lock_until = 0
        self.tilt_armed = True
        self.tilt_dir = None
        self.tilt_since = 0
        self.tilt_last = -1e9
        self.flat_since = None

    def update(self, t, ax, ay, az, gx, gy, gz):
        s = dict(t=t, ax=ax, ay=ay, az=az, gx=gx, gy=gy, gz=gz)
        s['a'] = math.sqrt(ax * ax + ay * ay + az * az)
        s['g'] = math.sqrt(gx * gx + gy * gy + gz * gz)
        out = []
        if not self.started:              # announce the starting mode once
            self.started = True
            out.append(('mode', self.mode))

        self.recent.append(s)
        while self.recent and t - self.recent[0]['t'] > WINDOW_BEFORE:
            self.recent.popleft()

        # ---- gestures: trigger on a big |a|, then look at the whole window
        if self.capture is not None:
            self.capture.append(s)
            if t >= self.capture_until:
                gesture = self.classify(self.capture)
                self.capture = None
                if gesture:
                    out.append(('gesture', gesture))
                    self.lock_until = t + GESTURE_COOLDOWN
        elif s['a'] > TRIGGER_A and t >= self.lock_until:
            self.capture = list(self.recent)
            self.capture_until = t + WINDOW_AFTER

        # ---- tilt left / right -> previous / next mode (only with --tilt)
        if self.use_tilt and self.capture is None:
            step = self.tilt(s)
            if step:
                self.mode = MODES[(MODES.index(self.mode) + step) % len(MODES)]
                self.lock_until = max(self.lock_until, t + AFTER_MODE_LOCK)
                out.append(('mode', self.mode))
        return out

    def step_mode(self, step, t):
        """Move to the previous (-1) / next (+1) mode, e.g. from a button."""
        self.mode = MODES[(MODES.index(self.mode) + step) % len(MODES)]
        self.capture = None
        self.lock_until = max(self.lock_until, t + AFTER_MODE_LOCK)
        return self.mode

    def classify(self, w):
        peak = lambda k: max(abs(x[k]) for x in w)
        a_max = peak('a')
        fwd = peak(AXES['forward'])
        flip_rot = peak(AXES['flip_rot'])
        result = None
        if self.mode == 'grill':
            # A forward swing is not a flip, even though it also jolts the pan.
            if fwd <= TOSS_MIN_FORWARD and a_max > FLIP_MIN_A and flip_rot > FLIP_MIN_ROT:
                result = 'flip'
        elif self.mode == 'board':
            if a_max > CHOP_MIN_A:
                result = 'chop'
        elif self.mode == 'assembly':
            if fwd > TOSS_MIN_FORWARD:
                result = 'toss'
        if self.debug:
            print(f'  [motion] mode={self.mode} |a|max={a_max:5.1f} fwd={fwd:5.1f} '
                  f'flip_rot={flip_rot:4.1f} -> {result}')
        return result

    def roll(self, s):
        """Degrees of left/right tilt; positive = right."""
        r = math.degrees(math.atan2(s[AXES['side']], s[AXES['up']]))
        return -r if TILT_RIGHT_IS_NEGATIVE_Y else r

    def tilt(self, s):
        if abs(s['a'] - G) > TILT_MAX_DYNAMIC:
            return 0                       # accelerating: the angle is not gravity
        r = self.roll(s)
        t = s['t']
        if abs(r) < TILT_OFF:
            if self.flat_since is None:
                self.flat_since = t
            if t - self.flat_since >= TILT_REARM and t - self.tilt_last >= TILT_REFRACTORY:
                self.tilt_armed = True
            self.tilt_dir = None
            return 0
        self.flat_since = None
        if not self.tilt_armed or abs(r) < TILT_ON:
            self.tilt_dir = None
            return 0
        d = 1 if r > 0 else -1
        if d != self.tilt_dir:
            self.tilt_dir = d
            self.tilt_since = t
            return 0
        if t - self.tilt_since >= TILT_HOLD:
            self.tilt_armed = False
            self.tilt_dir = None
            self.tilt_last = t
            if self.debug:
                print(f'  [tilt] {"right" if d > 0 else "left"} ({r:+.0f} deg)')
            return d
        return 0


# ------------------------------------------------------------------- cards --

def chroma(r, g, b, c):
    total = max(1, r + g + b)
    return [r / total, g / total, b / total, math.log10(max(1, c))]


def card_distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a[:3], b[:3]))) * 4 + abs(a[3] - b[3]) * 0.5


class CardReader:
    """A card is: proximity goes up -> the screen turns white to light the card
    (so the colour does not depend on the mode colour on the screen or on the
    room) -> after LAMP_SETTLE the colour is read and matched to the nearest
    calibrated card -> the next card needs the proximity to drop first."""

    def __init__(self, apds, calib, display=None):
        self.apds = apds
        self.calib = calib or {}
        self.display = display
        self.prox_on = max(PROX_ON_MIN, self.calib.get('prox_on', PROX_ON_DEFAULT))
        self.prox_off = self.prox_on * PROX_OFF_RATIO
        self.reading_since = None
        self.armed = True

    def lamp(self, on):
        if self.display is not None:
            self.display.set_lamp(on)

    def poll(self, t):
        prox = self.apds.proximity
        if prox < self.prox_off:
            if self.reading_since is not None:
                self.lamp(False)          # card pulled away before we could read it
            self.reading_since = None
            self.armed = True
            return None
        if self.reading_since is None:
            if prox < self.prox_on or not self.armed:
                return None
            self.reading_since = t
            self.lamp(True)
            return None
        if t - self.reading_since < LAMP_SETTLE:   # screen white + a full fresh reading
            return None
        r, g, b, c = self.apds.color_data
        self.lamp(False)
        self.reading_since = None
        self.armed = False
        return self.match(chroma(r, g, b, c)), (r, g, b, c), prox

    def nearest(self, feat):
        refs = {k: v for k, v in self.calib.get('cards', {}).items() if k in CARDS}
        if 'none' in self.calib:
            refs['none'] = self.calib['none']
        if not refs:
            return None, 1e9
        return min(((name, card_distance(feat, ref)) for name, ref in refs.items()), key=lambda x: x[1])

    def match(self, feat):
        name, d = self.nearest(feat)
        if name == 'none' or d > self.calib.get('max_distance', 0.6):
            return None
        return name


def measure(apds, seconds=2.0):
    feats, proxes = [], []
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if apds.color_data_ready:
            r, g, b, c = apds.color_data
            feats.append(chroma(r, g, b, c))
            proxes.append(apds.proximity)
        time.sleep(0.02)
    mean = [sum(f[i] for f in feats) / len(feats) for i in range(4)]
    return mean, sorted(proxes)[len(proxes) // 2]


def watch_cards(apds, calib, display):
    """Print the colour reading live (screen lit white, like when a card is read)."""
    reader = CardReader(apds, calib) if calib else None
    display.set_lamp(True)
    print('即時顏色（螢幕全白當補光）：把卡片在感測器前面前後移動，看讀數。Ctrl+C 結束。\n')
    print('距離  紅    綠    藍    亮度   → 最像')
    os.makedirs(os.path.join(HERE, 'recordings'), exist_ok=True)
    log_path = os.path.join(HERE, 'recordings', time.strftime('cards_%Y%m%d_%H%M%S.csv'))
    log = open(log_path, 'w')
    log.write('t,prox,r,g,b,c\n')
    print(f'（讀數同時存到 {log_path}）')
    t0 = time.monotonic()
    while True:
        if apds.color_data_ready:
            r, g, b, c = apds.color_data
            prox = apds.proximity
            log.write(f'{time.monotonic() - t0:.2f},{prox},{r},{g},{b},{c}\n')
            log.flush()
            f = chroma(r, g, b, c)
            guess = ''
            if reader:
                name, d = reader.nearest(f)
                guess = f'{CARD_NAMES.get(name, "沒卡片")} ({d:.2f})'
            bar = lambda v: '█' * int(v * 20)
            print(f'{prox:4d}  {f[0]:.2f}  {f[1]:.2f}  {f[2]:.2f}  {c:5d}  → {guess:12s} '
                  f'R{bar(f[0]):<12s}G{bar(f[1]):<14s}B{bar(f[2])}')
        time.sleep(0.02)


def calibrate(apds, display, only=None):
    display.set_lamp(True)            # cards are always read with the screen lit white
    if not display.ok:
        print('⚠️  螢幕沒有啟動，補光不會亮（先停掉 piscreen.service 和其他 pan.py）。')
    print('食材卡校準：每張卡拿在感測器正前方 2–4 公分，跟玩的時候一樣，按 Enter 量 2 秒。')
    print('（螢幕會全白當補光燈；卡片不要貼住感測器。）\n')
    cards, old = {}, {}
    if os.path.exists(CARDS_FILE):
        with open(CARDS_FILE) as f:
            old = json.load(f)
    if only and old.get('lamp'):
        # Re-measuring some cards: keep the others (only if they were measured with the lamp too).
        cards = {k: v for k, v in old.get('cards', {}).items() if k in CARDS}
    elif only:
        print('（舊的校準是在沒有補光時量的，這次 4 張卡都要重量。）\n')
        only = None

    input('  先量「沒有卡片」：感測器前面什麼都不要放，按 Enter… ')
    none, none_prox = measure(apds)
    print(f'    r {none[0]:.2f}  g {none[1]:.2f}  b {none[2]:.2f}  亮度 {10 ** none[3]:.0f}   距離值 {none_prox}\n')

    proxes = []
    for name in (only or CARDS):
        while True:
            input(f'  {CARD_NAMES[name]}卡（{name}）拿好按 Enter… ')
            mean, prox = measure(apds)
            print(f'    r {mean[0]:.2f}  g {mean[1]:.2f}  b {mean[2]:.2f}  亮度 {10 ** mean[3]:.0f}   距離值 {prox}')
            if prox < max(PROX_ON_MIN * 1.5, none_prox + 20):
                print('    ⚠️  距離值太低，感測器幾乎沒看到卡片。拿近一點（2–4 公分）再量一次。')
                continue
            if card_distance(mean, none) < 0.3:
                print('    ⚠️  讀到的顏色跟「沒有卡片」一樣。卡片要正對感測器，再量一次。')
                continue
            break
        cards[name] = mean
        proxes.append(prox)

    print('\n卡片之間的差距（越大越好，小於 0.3 容易認錯）：')
    names = list(cards)
    worst = 1e9
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            d = card_distance(cards[names[i]], cards[names[j]])
            worst = min(worst, d)
            print(f'  {CARD_NAMES[names[i]]} ↔ {CARD_NAMES[names[j]]}: {d:.2f}{"  ⚠️" if d < 0.3 else ""}')

    # A card counts as "there" at half the weakest proximity seen while calibrating.
    prox_on = max(PROX_ON_MIN, int(min(proxes) * 0.5))
    if only and old.get('prox_on'):
        prox_on = max(PROX_ON_MIN, min(prox_on, old['prox_on']))
    data = {'cards': cards, 'none': none, 'prox_on': prox_on, 'lamp': True,
            'max_distance': max(0.4, min(0.8, worst))}
    with open(CARDS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    display.set_lamp(False)
    print(f'\n存到 {CARDS_FILE}（卡片靠近的門檻：距離值 {prox_on}）')


# ----------------------------------------------------------------- display --

MODE_COLORS = {'grill': (228, 87, 46), 'board': (63, 163, 77), 'assembly': (46, 134, 222), None: (60, 60, 60)}
MODE_WORDS = {'grill': 'PAN', 'board': 'KNIFE', 'assembly': 'PLATE', None: '...'}
FLASH_COLORS = {'ok': (255, 255, 255), 'ding': (255, 220, 0), 'serve': (255, 220, 0),
                'catch': (255, 220, 0), 'error': (200, 0, 0), 'burn': (200, 0, 0)}


class Display:
    """Mini PiTFT: the whole screen is the colour of the mode, so it can be
    seen from across the table. Events flash it briefly. Runs in its own
    thread so drawing never slows down the IMU loop."""

    def __init__(self, player, enabled=True):
        self.player = player.upper()
        self.mode = None
        self.flash = None
        self.flash_until = 0
        self.lamp = False           # full white, used as the light for reading cards
        self.dirty = threading.Event()
        self.ok = False
        if not enabled:
            return
        try:
            import board
            import digitalio
            from PIL import Image, ImageDraw, ImageFont
            import adafruit_rgb_display.st7789 as st7789
            backlight = digitalio.DigitalInOut(board.D22)
            backlight.switch_to_output()
            backlight.value = True
            self.disp = st7789.ST7789(
                board.SPI(), cs=digitalio.DigitalInOut(board.D5), dc=digitalio.DigitalInOut(board.D25),
                rst=None, baudrate=64000000, width=135, height=240, x_offset=53, y_offset=40, rotation=90)
            self.Image, self.ImageDraw = Image, ImageDraw
            font = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            self.big = ImageFont.truetype(font, 56)
            self.small = ImageFont.truetype(font, 22)
            threading.Thread(target=self.loop, daemon=True).start()
            self.ok = True
        except Exception as e:
            print(f'（沒有螢幕，略過：{e}）')
            self.ok = False

    def set_mode(self, mode):
        self.mode = mode
        self.dirty.set()

    def set_lamp(self, on):
        self.lamp = on
        self.dirty.set()

    def flash_event(self, kind):
        if kind in FLASH_COLORS:
            self.flash = FLASH_COLORS[kind]
            self.flash_until = time.monotonic() + 0.3
            self.dirty.set()

    def loop(self):
        while True:
            self.dirty.wait(timeout=0.3)
            self.dirty.clear()
            if self.lamp:
                self.disp.image(self.Image.new('RGB', (240, 135), (255, 255, 255)))
                continue
            flashing = time.monotonic() < self.flash_until
            color = self.flash if flashing else MODE_COLORS.get(self.mode)
            img = self.Image.new('RGB', (240, 135), color)
            d = self.ImageDraw.Draw(img)
            d.text((10, 6), self.player, font=self.small, fill=(255, 255, 255))
            word = MODE_WORDS.get(self.mode, '')
            w = d.textlength(word, font=self.big)
            d.text(((240 - w) / 2, 45), word, font=self.big, fill=(255, 255, 255))
            self.disp.image(img)
            if flashing:
                time.sleep(max(0, self.flash_until - time.monotonic()))
                self.dirty.set()


# ----------------------------------------------------------------- buttons --

LONG_PRESS = 1.0        # hold B this long = throw away what is on the current station


class Buttons:
    """The two buttons on the Mini PiTFT (active low).
    A short press = previous mode, B short press = next mode, B held = trash."""

    def __init__(self):
        self.ok = False
        try:
            import board
            import digitalio
            self.pins = {}
            for name, pin in (('A', board.D23), ('B', board.D24)):
                io = digitalio.DigitalInOut(pin)
                io.switch_to_input(pull=digitalio.Pull.UP)
                self.pins[name] = io
            self.down_since = {'A': None, 'B': None}
            self.long_fired = {'A': False, 'B': False}
            self.ok = True
        except Exception as e:
            print(f'（讀不到螢幕按鈕：{e}）')

    def poll(self, t):
        """Returns 'A', 'B' (short press, on release), 'B_long' (held), or None."""
        if not self.ok:
            return None
        for name, io in self.pins.items():
            pressed = not io.value
            since = self.down_since[name]
            if pressed and since is None:
                self.down_since[name] = t
                self.long_fired[name] = False
            elif pressed and not self.long_fired[name] and t - since >= LONG_PRESS:
                self.long_fired[name] = True
                return name + '_long'
            elif not pressed and since is not None:
                self.down_since[name] = None
                if not self.long_fired[name] and t - since > 0.03:   # debounce
                    return name
        return None


# -------------------------------------------------------------------- mqtt --

class Link:
    def __init__(self, team, player, enabled, on_feedback):
        self.base = f'IDD/{team}/burger/{player}'
        self.client = None
        if not enabled:
            return
        import paho.mqtt.client as mqtt
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except AttributeError:
            self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                client.subscribe(f'{self.base}/feedback')
                print(f'MQTT 已連線：{self.base}/…')
            else:
                print(f'MQTT 連線失敗：{rc}')

        def on_message(client, userdata, msg):
            try:
                on_feedback(json.loads(msg.payload.decode('utf-8')))
            except ValueError:
                pass

        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=30)
        self.client.loop_start()

    def send(self, kind, value):
        payload = json.dumps({kind if kind != 'gesture' else 'type': value})
        if self.client is not None:
            self.client.publish(f'{self.base}/{kind}', payload)


# -------------------------------------------------------------------- main --

def setup_sensors():
    import board
    from adafruit_apds9960.apds9960 import APDS9960
    from adafruit_lsm6ds import AccelRange, GyroRange, Rate
    from adafruit_lsm6ds.lsm6ds3trc import LSM6DS3TRC
    i2c = board.I2C()
    imu = LSM6DS3TRC(i2c)
    imu.accelerometer_range = AccelRange.RANGE_16G
    imu.gyro_range = GyroRange.RANGE_2000_DPS
    imu.accelerometer_data_rate = Rate.RATE_208_HZ
    imu.gyro_data_rate = Rate.RATE_208_HZ
    apds = APDS9960(i2c)
    apds.enable_proximity = True
    apds.enable_color = True
    # The default colour integration is 256 cycles = 0.7 s per reading, far too
    # slow for a card held up for a moment: use 36 cycles (0.1 s) and 64x gain.
    apds.color_integration_time = 36
    apds.color_gain = 3
    return imu, apds


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--player', choices=['p1', 'p2'], default='p1')
    ap.add_argument('--team', default='panburger')
    ap.add_argument('--no-mqtt', action='store_true')
    ap.add_argument('--debug', action='store_true')
    ap.add_argument('--calibrate', nargs='*', metavar='CARD',
                    help='measure card colours (all, or only the cards named: ' + ' '.join(CARDS) + ')')
    ap.add_argument('--watch-cards', action='store_true', help='print colour readings live')
    ap.add_argument('--no-display', action='store_true', help="don't use the Mini PiTFT")
    ap.add_argument('--tilt', action='store_true', help='switch modes by tilting instead of the buttons')
    args = ap.parse_args()

    imu, apds = setup_sensors()
    display = Display(args.player, enabled=not args.no_display)
    if args.calibrate is not None:
        bad = [c for c in args.calibrate if c not in CARDS]
        if bad:
            sys.exit(f'不認得的卡片：{bad}，可以用：{CARDS}')
        return calibrate(apds, display, args.calibrate)

    calib = None
    if os.path.exists(CARDS_FILE):
        with open(CARDS_FILE) as f:
            calib = json.load(f)
    if args.watch_cards:
        return watch_cards(apds, calib, display)
    if not calib:
        print('⚠️  還沒校準食材卡（pan.py --calibrate），先不讀卡片。')

    motion = MotionDetector(debug=args.debug, tilt=args.tilt)
    buttons = Buttons()
    if calib and not calib.get('lamp'):
        print('⚠️  食材卡是在沒有螢幕補光時校準的，請重新執行 pan.py --calibrate。')
    cards = CardReader(apds, calib, display) if calib else None

    def on_feedback(fb):
        display.flash_event(fb.get('sound'))
        if fb.get('sound') == 'start' and motion.mode:
            link.send('mode', motion.mode)    # the server resets everyone to grill
        if fb.get('msg') and args.debug:
            print(f'  [server] {fb.get("sound")}: {fb.get("msg")}')

    link = Link(args.team, args.player, not args.no_mqtt, on_feedback)

    def send(kind, value):
        link.send(kind, value)
        label = {'mode': '模式', 'gesture': '動作', 'card': '卡片', 'button': '按鈕'}[kind]
        print(f'{time.strftime("%H:%M:%S")}  {label}：{value}')

    if args.tilt:
        print(f'{args.player} 開始！往右翻＝下一個模式、往左翻＝上一個模式。Ctrl+C 結束。')
    else:
        print(f'{args.player} 開始！A 鍵＝上一個模式、B 鍵＝下一個模式、長按 B＝丟掉。Ctrl+C 結束。')
    period = 0.01
    next_t = time.monotonic()
    last_mode_sent = 0
    n = 0
    while True:
        t = time.monotonic()
        ax, ay, az = imu.acceleration
        gx, gy, gz = imu.gyro
        for kind, value in motion.update(t, ax, ay, az, gx, gy, gz):
            if kind == 'mode':
                display.set_mode(value)
                last_mode_sent = t
            send(kind, value)

        press = buttons.poll(t)
        if press in ('A', 'B'):
            mode = motion.step_mode(-1 if press == 'A' else +1, t)
            display.set_mode(mode)
            last_mode_sent = t
            send('mode', mode)
        elif press == 'B_long':
            send('button', 'B')               # the server treats button B as "throw away"
            display.flash_event('error')

        # Re-announce the mode now and then, in case the server restarted.
        if motion.mode and t - last_mode_sent > 5:
            link.send('mode', motion.mode)
            last_mode_sent = t

        n += 1
        if cards and n % 3 == 0:              # ~33 Hz is plenty for cards
            hit = cards.poll(t)
            if hit:
                name, rgbc, prox = hit
                if name:
                    send('card', name)
                elif args.debug:
                    print(f'  [card] 認不出來 rgbc={rgbc} prox={prox}')

        next_t += period
        delay = next_t - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        else:
            next_t = time.monotonic()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n掰掰')
