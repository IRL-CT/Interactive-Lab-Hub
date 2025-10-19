#!/usr/bin/env python3
# Mini-PiTFT Tamagotchi — Joystick (4 actions) + Proximity "Pet" (no idle, no wake/sleep)
# Screen: ST7789 240x135 (Mini PiTFT), x_offset=53, y_offset=40, rotation=90

import os, time, threading
import board, busio, digitalio
from collections import deque
from enum import Enum
from PIL import Image, ImageDraw, ImageSequence, ImageFont
import adafruit_rgb_display.st7789 as st7789
import pygame

# ---- Joystick driver ----
try:
    import qwiic_joystick
    HAVE_JOY = True
except Exception:
    HAVE_JOY = False

# ---- APDS-9960 (proximity only) ----
try:
    from adafruit_apds9960.apds9960 import APDS9960
    HAVE_APDS = True
except Exception:
    HAVE_APDS = False

# ---------------------------
# Display setup (Mini PiTFT)
# ---------------------------
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None
BAUDRATE = 32_000_000
spi = board.SPI()

disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

WIDTH, HEIGHT, ROTATION = 240, 135, 90
canvas = Image.new("RGB", (WIDTH, HEIGHT))
draw = ImageDraw.Draw(canvas)

# Backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

# ---------------------------
# Sound setup
# ---------------------------
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    print("Audio system initialized")
except Exception as e:
    print(f"Audio init failed: {e}")
    pygame = None

def play_sound(sound_file):
    """Play a sound file if audio is available."""
    if pygame and os.path.exists(sound_file):
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
            print(f"Playing: {sound_file}")
        except Exception as e:
            print(f"Sound error: {e}")
    else:
        print(f"Sound file not found: {sound_file}")

def stop_sound():
    """Stop any currently playing sound."""
    if pygame:
        try:
            pygame.mixer.music.stop()
            print("Sound stopped")
        except Exception as e:
            print(f"Stop sound error: {e}")

def load_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()
font_sm = load_font(14)

# ---------------------------
# Image helpers
# ---------------------------
def cover_fit(img, tw, th):
    w, h = img.size
    if w * th < tw * h:
        nw, nh = tw, int(h * tw / w)
    else:
        nh, nw = th, int(w * th / h)
    img = img.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - tw)//2, (nh - th)//2
    return img.crop((left, top, left + tw, top + th))

def load_gif(path):
    frames, durations = [], []
    if not os.path.exists(path):
        return frames, durations
    gif = Image.open(path)
    for fr in ImageSequence.Iterator(gif):
        fr = fr.convert("RGB")
        fr = cover_fit(fr, WIDTH, HEIGHT)
        frames.append(fr)
        durations.append(max(20, int(fr.info.get("duration", gif.info.get("duration", 100)))))
    return frames, durations

# ---------------------------
# Actions & assets (NO IDLE)
# ---------------------------
class Action(Enum):
    FEED="feed"    # UP
    PLAY="play"    # DOWN
    CLEAN="clean"  # LEFT
    DRINK="drink"  # RIGHT
    PET="pet"      # proximity (hand moves closer)
    HAPPY="happy"  # UP + proximity touch

GIFS = {
    Action.FEED:  "gifs/run.gif",        # UP
    Action.PLAY:  "gifs/shakehead.gif",  # DOWN
    Action.CLEAN: "gifs/no.gif",         # LEFT
    Action.DRINK: "gifs/drink.gif",       # RIGHT
    Action.PET:   "gifs/pet.gif",         # Proximity (add your file; fallback if missing)
    Action.HAPPY: "gifs/happy.gif",        # UP + proximity touch
}

# Preload GIFs (fallback card if missing)
GIF_CACHE = {}
for act, p in GIFS.items():
    frames, durs = load_gif(p)
    if not frames:
        card = Image.new("RGB", (WIDTH, HEIGHT), (40, 40, 60))
        d = ImageDraw.Draw(card)
        d.text((10,10), f"{act.value.upper()} (missing {os.path.basename(p)})", fill=(255,255,255))
        frames, durs = [card], [120]
    GIF_CACHE[act] = (frames, durs)

# ---------------------------
# Hardware: I2C + devices
# ---------------------------
i2c = busio.I2C(board.SCL, board.SDA)

joystick = None
if HAVE_JOY:
    try:
        joystick = qwiic_joystick.QwiicJoystick()
        if joystick.connected:
            joystick.begin()
            print("Joystick ready")
        else:
            print("Joystick not detected")
            joystick = None
    except Exception as e:
        print("Joystick init failed:", e)
        joystick = None

apds = None
if HAVE_APDS:
    try:
        apds = APDS9960(i2c)
        apds.enable_proximity = True       # proximity only
        apds.enable_gesture   = False      # gestures OFF
        print("APDS-9960 proximity ready")
    except Exception as e:
        print("APDS init failed:", e)
        apds = None

# ---------------------------
# Auto-calibration (joystick)
# ---------------------------
CENTER_X = 128
CENTER_Y = 128
SCALE = 255
THRESH = 0.30  # ≥30% from center triggers a direction

def calibrate_joystick(duration=0.8):
    global CENTER_X, CENTER_Y, SCALE
    if not joystick: return
    print("Calibrating joystick... (release the stick)")
    t0 = time.time()
    xs, ys = [], []
    while time.time() - t0 < duration:
        xs.append(joystick.get_horizontal())
        ys.append(joystick.get_vertical())
        time.sleep(0.01)
    CENTER_X = int(sum(xs)/max(1,len(xs)))
    CENTER_Y = int(sum(ys)/max(1,len(ys)))
    max_obs = max(max(xs), max(ys))
    SCALE = 1023 if max_obs > 300 else 255
    print(f"Center=({CENTER_X},{CENTER_Y})  Scale~{SCALE}")

def norm_delta(val, center):
    span = (SCALE / 2.0)
    return max(-1.0, min(1.0, (val - center) / span))

# ---------------------------
# State & queue
# ---------------------------
event_q = deque(maxlen=16)
current_action = Action.PLAY  # default loop at startup
frame_idx = 0
next_frame_at = time.time()

def push(a: Action):
    # avoid spamming the same action
    if not event_q or event_q[-1] != a:
        event_q.append(a)

# ---------------------------
# Workers
# ---------------------------
def joystick_worker():
    if not joystick:
        print("Joystick worker skipped (no device)")
        return
    calibrate_joystick()
    while True:
        try:
            x = joystick.get_horizontal()
            y = joystick.get_vertical()
            dx = norm_delta(x, CENTER_X)
            dy = norm_delta(y, CENTER_Y)
            abs_dx, abs_dy = abs(dx), abs(dy)

            if abs_dy >= abs_dx and abs_dy >= THRESH:
                if dy < 0:
                    # Check if proximity sensor detects touch when joystick goes UP
                    if apds and apds.proximity > 20:  # proximity threshold for touch
                        push(Action.HAPPY)  # UP + proximity touch = HAPPY
                    else:
                        push(Action.FEED)   # UP only = FEED
                else:
                    push(Action.PLAY)   # DOWN
            elif abs_dx > abs_dy and abs_dx >= THRESH:
                if dx < 0:
                    push(Action.CLEAN)  # LEFT
                else:
                    push(Action.DRINK)  # RIGHT
            time.sleep(0.06)
        except Exception as e:
            print("Joystick err:", e)
            time.sleep(0.2)

def apds_worker():
    """Proximity 'petting' = rising edge."""
    if not apds:
        print("APDS worker skipped (no device)")
        return
    last_prox = 0
    last_pet_at = 0.0
    PET_DELTA = 8         # how much 'closer' counts as a pet
    PET_COOLDOWN = 0.6    # seconds between PET events (debounce)
    while True:
        try:
            prox = apds.proximity  # 0..255
            now = time.time()
            if (prox - last_prox) >= PET_DELTA and (now - last_pet_at) > PET_COOLDOWN:
                push(Action.PET)
                last_pet_at = now
            last_prox = prox
            time.sleep(0.05)
        except Exception as e:
            print("APDS err:", e)
            time.sleep(0.3)

# ---------------------------
# GIF playback (loop current action forever)
# ---------------------------
def set_action(a: Action):
    global current_action, frame_idx, next_frame_at
    if a == current_action:
        return
    current_action = a
    frame_idx = 0
    next_frame_at = time.time()

def draw_frame(now: float):
    global frame_idx, next_frame_at
    frames, durs = GIF_CACHE[current_action]
    if now >= next_frame_at:
        frame_idx = (frame_idx + 1) % len(frames)
        next_frame_at = now + (durs[frame_idx] / 1000.0)
    canvas.paste(frames[frame_idx])
    disp.image(canvas, ROTATION)

# ---------------------------
# Main
# ---------------------------
def main():
    threading.Thread(target=joystick_worker, daemon=True).start()
    threading.Thread(target=apds_worker, daemon=True).start()

    set_action(current_action)  # loop default action
    disp.image(canvas, ROTATION)

    while True:
        now = time.time()

        if event_q:
            act = event_q.popleft()
            set_action(act)
            
            # Handle sound for different actions
            if act == Action.HAPPY:
                play_sound("dog_bark.mp3")
            else:
                # Stop sound when switching to other actions
                stop_sound()

        draw_frame(now)
        time.sleep(0.01)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
