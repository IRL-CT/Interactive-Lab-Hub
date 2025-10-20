#!/usr/bin/env python3
# Mini-PiTFT Tamagotchi — Joystick (4 actions) + Proximity "Pet" with SCOREBOARD
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
font_med = load_font(20)
font_lg = load_font(28)

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
# Dog Stats (Life & Heart)
# ---------------------------
class DogStats:
    def __init__(self):
        self.life = 60   # 0-100 (starts at 3/5 stars = 60%)
        self.heart = 60  # 0-100 (starts at 3/5 hearts = 60%)
        self.lock = threading.Lock()
    
    def update(self, action):
        """Update stats based on action performed. Max +/- 2 per action."""
        with self.lock:
            if action == Action.FEED:
                self.life = min(100, self.life + 10)   # +0.5 star
                self.heart = min(100, self.heart + 10) # +0.5 heart
            elif action == Action.DRINK:
                self.life = min(100, self.life + 10)   # +0.5 star
            elif action == Action.PLAY:
                self.heart = min(100, self.heart + 20) # +1 heart
                self.life = max(0, self.life - 10)     # -0.5 star (playing tires the dog)
            elif action == Action.CLEAN:
                self.life = min(100, self.life + 20)   # +1 star
                self.heart = min(100, self.heart + 10) # +0.5 heart
            elif action == Action.PET:
                self.heart = min(100, self.heart + 20) # +1 heart
            elif action == Action.HAPPY:
                self.heart = min(100, self.heart + 40) # +2 hearts (best action!)
                self.life = min(100, self.life + 20)   # +1 star
    
    def decay(self):
        """Gradual stat decay over time (called periodically)."""
        with self.lock:
            self.life = max(0, self.life - 2)   # -0.1 star every 10s
            self.heart = max(0, self.heart - 2) # -0.1 heart every 10s
    
    def get_stats(self):
        """Thread-safe getter."""
        with self.lock:
            return self.life, self.heart

dog_stats = DogStats()

# ---------------------------
# Actions & assets
# ---------------------------
class Action(Enum):
    FEED="feed"    # UP
    PLAY="play"    # DOWN
    CLEAN="clean"  # LEFT
    DRINK="drink"  # RIGHT
    PET="pet"      # proximity (hand moves closer)
    HAPPY="happy"  # UP + proximity touch
    IDLE="idle"    # NEW: scoreboard state

GIFS = {
    Action.FEED:  "gifs/run.gif",        # UP
    Action.PLAY:  "gifs/shakehead.gif",  # DOWN
    Action.CLEAN: "gifs/no.gif",         # LEFT
    Action.DRINK: "gifs/drink.gif",      # RIGHT
    Action.PET:   "gifs/pet.gif",        # Proximity
    Action.HAPPY: "gifs/happy.gif",      # UP + proximity touch
}

# Preload GIFs (fallback card if missing)
GIF_CACHE = {}
for act, p in GIFS.items():
    frames, durs = load_gif(p)
    if not frames:
        card = Image.new("RGB", (WIDTH, HEIGHT), (40, 40, 60))
        d = ImageDraw.Draw(card)
        d.text((10,10), f"{act.value.upper()} (missing {os.path.basename(p)})", fill=(255,255,255), font=font_sm)
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
current_action = Action.IDLE  # start with scoreboard
frame_idx = 0
next_frame_at = time.time()
last_action_time = time.time()
IDLE_TIMEOUT = 3.0  # seconds of inactivity before showing scoreboard

# Animation state for floating hearts
heart_animation_active = False
heart_animation_start = 0.0
heart_animation_duration = 0.0

def push(a: Action):
    global last_action_time
    # avoid spamming the same action
    if not event_q or event_q[-1] != a:
        event_q.append(a)
        last_action_time = time.time()

# ---------------------------
# Scoreboard drawing
# ---------------------------
def draw_floating_heart(d, progress):
    """Draw a floating heart that slides in from right.
    progress: 0.0 (start) to 1.0 (end)
    """
    # Heart slides in from right side
    start_x = WIDTH + 30  # Off-screen right
    end_x = WIDTH - 50    # Final position on right side
    
    # Ease-in-out animation
    t = progress
    if t < 0.5:
        eased = 2 * t * t
    else:
        eased = 1 - pow(-2 * t + 2, 2) / 2
    
    x = int(start_x + (end_x - start_x) * eased)
    y = HEIGHT // 2 - 20  # Vertically centered
    
    # Draw big heart with outline for visibility
    heart_size = font_lg
    d.text((x-2, y), "♥", fill=(100, 0, 50), font=heart_size)  # Dark outline
    d.text((x, y), "♥", fill=(255, 50, 150), font=heart_size)  # Main heart
    
    # Draw "+1" text below heart
    d.text((x, y + 30), "+1", fill=(255, 200, 200), font=font_med)

def draw_scoreboard():
    """Draw a compact scoreboard with resting dog image."""
    canvas.paste(Image.new("RGB", (WIDTH, HEIGHT), (30, 30, 50)))  # dark blue background
    
    # Load and display resting dog image (smaller to avoid cropping)
    rest_img_path = "gifs/still.png"
    if os.path.exists(rest_img_path):
        try:
            rest_img = Image.open(rest_img_path).convert("RGBA")
            # Set max dimensions for the dog image
            img_max_width = int(WIDTH * 0.6)  # 60% of screen width
            img_max_height = 70  # Keep it compact to avoid head cropping
            rest_img.thumbnail((img_max_width, img_max_height), Image.Resampling.LANCZOS)
            
            # Center the image horizontally
            x = (WIDTH - rest_img.width) // 2
            y = 5  # Small offset from top
            
            # Paste with transparency support
            canvas.paste(rest_img, (x, y), rest_img)
        except Exception as e:
            print(f"Error loading rest image: {e}")
    
    d = ImageDraw.Draw(canvas)
    life, heart = dog_stats.get_stats()
    
    # Convert 0-100 to 0-5 stars/hearts
    life_count = round(life / 20.0)  # 20% = 1 star
    heart_count = round(heart / 20.0)  # 20% = 1 heart
    
    # Compact stats at bottom of screen
    stats_y = 85  # Start stats section
    
    # Life stars (★)
    d.text((10, stats_y), "LIFE", fill=(100, 255, 100), font=font_sm)
    star_x = 55
    for i in range(5):
        if i < life_count:
            # Filled star
            d.text((star_x + i * 25, stats_y - 2), "★", fill=(255, 215, 0), font=font_med)
        else:
            # Empty star
            d.text((star_x + i * 25, stats_y - 2), "☆", fill=(100, 100, 100), font=font_med)
    
    # Heart icons (♥)
    heart_y = stats_y + 25
    d.text((10, heart_y), "HEART", fill=(255, 100, 150), font=font_sm)
    heart_x = 55
    for i in range(5):
        if i < heart_count:
            # Filled heart
            d.text((heart_x + i * 25, heart_y - 2), "♥", fill=(255, 50, 150), font=font_med)
        else:
            # Empty heart
            d.text((heart_x + i * 25, heart_y - 2), "♡", fill=(100, 100, 100), font=font_med)
    
    disp.image(canvas, ROTATION)

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

def stats_decay_worker():
    """Slowly decay stats over time."""
    while True:
        time.sleep(10)  # decay every 10 seconds
        dog_stats.decay()

# ---------------------------
# GIF playback
# ---------------------------
def set_action(a: Action):
    global current_action, frame_idx, next_frame_at
    global heart_animation_active, heart_animation_start, heart_animation_duration
    
    if a == current_action:
        return
    current_action = a
    frame_idx = 0
    next_frame_at = time.time()
    
    # Update stats when action is performed (not IDLE)
    if a != Action.IDLE:
        dog_stats.update(a)
        
        # Trigger heart animation for actions that increase heart
        if a in [Action.FEED, Action.PLAY, Action.CLEAN, Action.PET, Action.HAPPY]:
            heart_animation_active = True
            heart_animation_start = time.time()
            # Calculate GIF duration to sync animation
            frames, durs = GIF_CACHE[a]
            heart_animation_duration = sum(durs) / 1000.0  # Convert ms to seconds

def draw_frame(now: float):
    global frame_idx, next_frame_at, heart_animation_active
    
    if current_action == Action.IDLE:
        draw_scoreboard()
        return
    
    frames, durs = GIF_CACHE[current_action]
    if now >= next_frame_at:
        frame_idx = (frame_idx + 1) % len(frames)
        next_frame_at = now + (durs[frame_idx] / 1000.0)
    canvas.paste(frames[frame_idx])
    
    # Draw floating heart animation if active
    if heart_animation_active:
        elapsed = now - heart_animation_start
        progress = min(1.0, elapsed / heart_animation_duration)
        
        d = ImageDraw.Draw(canvas)
        draw_floating_heart(d, progress)
        
        # Deactivate when animation completes
        if progress >= 1.0:
            heart_animation_active = False
    
    disp.image(canvas, ROTATION)

# ---------------------------
# Main
# ---------------------------
def main():
    threading.Thread(target=joystick_worker, daemon=True).start()
    threading.Thread(target=apds_worker, daemon=True).start()
    threading.Thread(target=stats_decay_worker, daemon=True).start()

    set_action(current_action)
    disp.image(canvas, ROTATION)

    while True:
        now = time.time()

        # Check for idle timeout
        if (now - last_action_time) > IDLE_TIMEOUT and current_action != Action.IDLE:
            set_action(Action.IDLE)

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