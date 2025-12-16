"""
calibrate.py

Active Learning Calibration for Raspberry Pi Dual-Ear Compass.

HARDWARE:
  - Pi 5 (Receiver) moving around a static Beacon (Sender).
  - ST7789 Display showing the "Needle".

WORKFLOW:
  1. BOOTSTRAP: We collect 3 baseline points (Center, Left 90, Right 90).
  2. FREE ROAM: The compass starts running live using the initial model.
     - You move around the circle.
     - When the needle matches reality (points at beacon), you type 'y'.
     - If the needle is wrong, you type 'n'.
     - The model retrains instantly on 'y'.

Usage:
  sudo python3 calibrate.py
"""

import os
import time
import uuid
import joblib
import threading
import math
import sys
import select
from collections import deque
from sklearn.linear_model import LinearRegression

import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
from scapy.all import sniff, Dot11, RadioTap

# ---------- CONFIG ----------

RECEIV_MAC  = "2c:cf:67:73:fe:2c"  # BEACON MAC
LEFT_IFACE  = "wlan1"
RIGHT_IFACE = "wlan2"
CHECKPOINT_DIR = "checkpoints"

# Physics limits for fallback (before ML takes over)
DELTA_MAX_DB   = 20.0 
MAX_ANGLE_DEG  = 90.0

# ---------- STATE ----------

lock = threading.Lock()
rssi_left_buffer  = deque(maxlen=10) # Fast smoothing
rssi_right_buffer = deque(maxlen=10)

X_train = [] # Features: [rssi_l, rssi_r]
y_train = [] # Labels:   [angle]

ml_model = None
is_running = True
current_pred_angle = 0.0

# ---------- HARDWARE SETUP ----------

def ensure_root():
    if os.geteuid() != 0:
        raise SystemExit("!! MUST RUN AS ROOT (sudo) !!")

# Setup Display
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
spi = board.SPI()
disp = st7789.ST7789(spi, cs=cs_pin, dc=dc_pin, width=135, height=240, x_offset=53, y_offset=40)
width = disp.height
height = disp.width
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)
bl = digitalio.DigitalInOut(board.D22)
bl.switch_to_output()
bl.value = True
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except:
    font = ImageFont.load_default()

# ---------- UTILS ----------

def normalize_mac(mac):
    return (mac or "").lower()

def get_current_rssi():
    """Returns average RSSI from buffers."""
    with lock:
        if len(rssi_left_buffer) < 2 or len(rssi_right_buffer) < 2:
            return None, None
        avg_l = sum(rssi_left_buffer) / len(rssi_left_buffer)
        avg_r = sum(rssi_right_buffer) / len(rssi_right_buffer)
        return avg_l, avg_r

def train_model():
    """Retrains the global model on X_train/y_train."""
    global ml_model
    if len(X_train) < 3:
        return # Not enough data
    
    # Linear Regression is robust for simple RSSI difference
    clf = LinearRegression()
    clf.fit(X_train, y_train)
    ml_model = clf

# ---------- SNIFFER ----------

TARGET_MAC = normalize_mac(RECEIV_MAC)

def sniff_thread(iface, side):
    def packet_handler(pkt):
        if not pkt.haslayer(Dot11): return
        if normalize_mac(pkt.addr2) == TARGET_MAC:
            try:
                rssi = int(pkt[RadioTap].dBm_AntSignal)
                with lock:
                    if side == "left": rssi_left_buffer.append(rssi)
                    else: rssi_right_buffer.append(rssi)
            except: pass
    
    print(f"[Sniffer] Listening on {iface} ({side})...")
    sniff(iface=iface, prn=packet_handler, store=False)

# ---------- DISPLAY LOOP (The "Spinning Compass") ----------

def display_thread_func():
    """Runs the display at 30FPS."""
    global current_pred_angle
    
    while is_running:
        l, r = get_current_rssi()
        
        # 1. Predict Angle
        if l is not None and r is not None:
            if ml_model:
                # Use the Brain
                try:
                    pred = ml_model.predict([[l, r]])[0]
                    current_pred_angle = max(-110, min(110, pred))
                except:
                    current_pred_angle = 0.0
            else:
                # Use rough math (Fallback before bootstrap)
                delta = r - l
                ratio = max(-1, min(1, delta / DELTA_MAX_DB))
                current_pred_angle = ratio * MAX_ANGLE_DEG

        # 2. Draw
        draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
        cx, cy = width // 2, height // 2
        radius = 50
        
        # Compass circle
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=(100,100,100), width=2)
        
        # Needle
        angle_rad = math.radians(current_pred_angle)
        px = cx + radius * math.sin(angle_rad)
        py = cy - radius * math.cos(angle_rad)
        draw.line((cx, cy, px, py), fill=(0, 255, 0), width=4) # Green needle for calibration
        
        # Stats
        if ml_model:
            draw.text((5, 5), "AI MODE", font=font, fill=(0, 255, 0))
        else:
            draw.text((5, 5), "MATH MODE", font=font, fill=(255, 0, 255))

        draw.text((5, 25), f"Ang: {current_pred_angle:.0f}", font=font, fill=(255,255,255))
        if l: draw.text((5, height-20), f"L:{l:.0f} R:{r:.0f}", font=font, fill=(100,100,100))
        
        disp.image(image, 90)
        time.sleep(0.05)

# ---------- MAIN INTERACTION ----------

def main():
    global is_running, ml_model, X_train, y_train
    ensure_root()
    if not os.path.exists(CHECKPOINT_DIR): os.makedirs(CHECKPOINT_DIR)

    # 1. Start Ears
    t1 = threading.Thread(target=sniff_thread, args=(LEFT_IFACE, "left"), daemon=True)
    t2 = threading.Thread(target=sniff_thread, args=(RIGHT_IFACE, "right"), daemon=True)
    t1.start(); t2.start()

    # 2. Wait for Signal
    print("Waiting for signal...")
    while True:
        l, r = get_current_rssi()
        if l is not None: break
        time.sleep(0.5)
    print("Signal found. Starting Display.")

    # 3. Start Display Thread
    t_disp = threading.Thread(target=display_thread_func, daemon=True)
    t_disp.start()

    # 4. Bootstrap Phase (3 Points)
    print("\n=== PHASE 1: BOOTSTRAP ===")
    print("I need 3 baseline points before I can start guessing.")
    
    bootstrap_steps = [
        (0,   "Position Pi so Beacon is DEAD AHEAD (0 deg)"),
        (-90, "Position Pi so Beacon is 90 LEFT"),
        (90,  "Position Pi so Beacon is 90 RIGHT")
    ]

    for angle, prompt in bootstrap_steps:
        print(f"\n>> {prompt}")
        input(">> Press [ENTER] when ready...")
        
        l, r = get_current_rssi()
        if l is None:
            print("!! Signal lost. Skipping point.")
            continue
        
        print(f"   Saved: L={l:.1f}, R={r:.1f} -> Angle={angle}")
        X_train.append([l, r])
        y_train.append(angle)
    
    print("\nTraining initial model...")
    train_model()
    
    # 5. Active Learning Loop
    print("\n=== PHASE 2: FREE ROAM (Active Learning) ===")
    print("Instructions:")
    print(" 1. Walk around the beacon circle.")
    print(" 2. Watch the needle on the Pi screen.")
    print(" 3. When the needle is pointing CORRECTLY at the beacon -> Press 'y' then Enter")
    print(" 4. If the needle is WRONG -> Press 'n' then Enter")
    print(" 5. Press 's' to Save Checkpoint.")
    print(" 6. Press 'q' to Quit.")
    
    while True:
        # We need to capture input without blocking the display (display is in thread, so input() is fine)
        cmd = input("\n[y=Good / n=Bad / s=Save / q=Quit] > ").strip().lower()
        
        curr_l, curr_r = get_current_rssi()
        curr_angle = current_pred_angle # From the global updated by display thread
        
        if cmd == 'y':
            if curr_l is None: 
                print("No signal, cannot save.")
                continue
                
            # Reinforcement Learning:
            # We assume if the user said "Yes", the CURRENT PREDICTION is close to truth.
            # So we feed the prediction back into the model as ground truth to reinforce it.
            print(f"   Reinforcing: L={curr_l:.0f} R={curr_r:.0f} => {curr_angle:.0f} deg")
            X_train.append([curr_l, curr_r])
            y_train.append(curr_angle)
            train_model()
            print(f"   Model Retrained! (Points: {len(X_train)})")

        elif cmd == 'n':
            print("   Discarded. (Bad Guess)")
            # We do nothing, just don't learn from this moment.

        elif cmd == 's':
            uid = str(uuid.uuid4())[:8]
            fname = os.path.join(CHECKPOINT_DIR, f"model_{uid}.pkl")
            joblib.dump(ml_model, fname)
            print(f"\n[SAVED] Checkpoint: {uid}")
            print(f"To run: sudo python3 pi_fused_compass.py --ckpt {uid}")

        elif cmd == 'q':
            print("Exiting...")
            is_running = False
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        is_running = False
        print("\nStopped.")
