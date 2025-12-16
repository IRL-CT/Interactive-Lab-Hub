"""
compass.py

Device: Raspberry Pi 5 (ROOT)
Features:
  - Fuses RSSI + Gyroscope (LSM6DS3) for smooth tracking.
  - Supports ML Checkpoints (--ckpt UID).
  - Supports Proximity Spin Mode (loads from checkpoints/spin.json).
  - Broadcasts Angle/Spin state via UDP to the Receiver Pi.

Run:
   sudo python3 compass.py --ckpt <UID>
"""

import os
import time
import math
import argparse
import threading
import joblib
import json
import socket
from collections import deque
import subprocess
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
from scapy.all import sniff, Dot11, RadioTap

def preempt_boot_screen() -> None:
    try:
        subprocess.run(["sudo", "-n", "systemctl", "stop", "pitft-boot-screen.service"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"systemctl stop attempt error (ignored): {e}")
    try:
        subprocess.run(["pkill", "-TERM", "-f", "python.*screen_boot_script.py"], check=False)
        time.sleep(0.8)
        subprocess.run(["pkill", "-KILL", "-f", "python.*screen_boot_script.py"], check=False)
    except Exception as e:
        print(f"pkill fallback error (ignored): {e}")

preempt_boot_screen()

# ---------- ARGS ----------
parser = argparse.ArgumentParser()
parser.add_argument("--ckpt", type=str, help="Model UID to load")
args = parser.parse_args()

# ---------- CONFIG ----------
RECEIV_MAC  = "2c:cf:67:73:fe:2c"
LEFT_IFACE  = "wlan1"
RIGHT_IFACE = "wlan2"
CHECKPOINT_DIR = "checkpoints"
BROADCAST_PORT = 55555

# Fallback Physics
DELTA_MAX_DB   = 20.0 
MAX_ANGLE_DEG  = 90.0
ALPHA_RSSI     = 0.05 
FPS            = 30

# ---------- STATE ----------
lock = threading.Lock()
raw_rssi_left  = None
raw_rssi_right = None
last_packet_time = 0.0
current_bearing = 0.0

ml_model = None
spin_threshold = None 

# ---------- NETWORK SETUP ----------
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# ---------- HARDWARE ----------
def ensure_root():
    if os.geteuid() != 0: raise SystemExit("Run as root.")

def init_display():
    cs_pin = digitalio.DigitalInOut(board.D5)
    dc_pin = digitalio.DigitalInOut(board.D25)
    spi = board.SPI()
    disp = st7789.ST7789(spi, cs=cs_pin, dc=dc_pin, width=135, height=240, x_offset=53, y_offset=40)
    width = disp.height; height = disp.width
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    bl = digitalio.DigitalInOut(board.D22)
    bl.switch_to_output(); bl.value = True
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except: font = ImageFont.load_default()
    return disp, image, draw, width, height, font

def init_imu():
    try:
        i2c = board.I2C()
        return LSM6DS3(i2c)
    except: return None

def calibrate_gyro(sensor):
    print("[IMU] Calibrating Gyro (Keep Still)...")
    offset = 0.0
    for _ in range(50):
        offset += sensor.gyro[2]
        time.sleep(0.02)
    return offset / 50.0

# ---------- LOADING ----------
if args.ckpt:
    path = os.path.join(CHECKPOINT_DIR, f"model_{args.ckpt}.pkl")
    if os.path.exists(path):
        print(f"[ML] Loading model: {path}")
        ml_model = joblib.load(path)

spin_path = os.path.join(CHECKPOINT_DIR, "spin.json")
if os.path.exists(spin_path):
    try:
        with open(spin_path, "r") as f:
            data = json.load(f)
            spin_threshold = data.get("spin_threshold_dbm")
            print(f"[SPIN] Threshold loaded: {spin_threshold} dBm")
    except: pass

# ---------- SNIFFER ----------
TARGET_MAC = (RECEIV_MAC or "").lower()

def sniff_thread(iface, side):
    global raw_rssi_left, raw_rssi_right, last_packet_time
    def h(pkt):
        global raw_rssi_left, raw_rssi_right, last_packet_time
        if not pkt.haslayer(Dot11): return
        if (pkt.addr2 or "").lower() == TARGET_MAC:
            try:
                val = pkt[RadioTap].dBm_AntSignal
                with lock:
                    if side == "left":
                        raw_rssi_left = val if raw_rssi_left is None else (raw_rssi_left * 0.7 + val * 0.3)
                    else:
                        raw_rssi_right = val if raw_rssi_right is None else (raw_rssi_right * 0.7 + val * 0.3)
                    last_packet_time = time.time()
            except: pass
    sniff(iface=iface, prn=h, store=False)

# ---------- MAIN LOOP ----------
def main():
    global current_bearing
    ensure_root()
    disp, image, draw, width, height, font = init_display()
    
    t1 = threading.Thread(target=sniff_thread, args=(LEFT_IFACE, "left"), daemon=True)
    t2 = threading.Thread(target=sniff_thread, args=(RIGHT_IFACE, "right"), daemon=True)
    t1.start(); t2.start()
    
    sensor = init_imu()
    g_off = calibrate_gyro(sensor) if sensor else 0.0
    
    print("[Main] Compass Running...")
    
    last_t = time.time()
    
    while True:
        now = time.time()
        dt = now - last_t
        last_t = now
        
        # 0. Check Proximity (Spin Logic)
        is_spinning = False
        with lock:
            l = raw_rssi_left
            r = raw_rssi_right
            
        if l is not None and r is not None and spin_threshold is not None:
            if max(l, r) > spin_threshold:
                is_spinning = True

        # 1. Update Bearing
        if is_spinning:
            current_bearing += 800.0 * dt  # Spin speed
            current_bearing %= 360 
        else:
            # Gyro
            if sensor:
                gz = sensor.gyro[2] - g_off
                current_bearing += math.degrees(gz * dt) 
            
            # RSSI
            target_angle = 0.0
            valid_signal = False
            
            if l is not None and r is not None:
                valid_signal = True
                if ml_model:
                    try: target_angle = ml_model.predict([[l, r]])[0]
                    except: target_angle = 0
                else:
                    delta = r - l
                    if delta > DELTA_MAX_DB: delta = DELTA_MAX_DB
                    if delta < -DELTA_MAX_DB: delta = -DELTA_MAX_DB
                    target_angle = (delta / DELTA_MAX_DB) * MAX_ANGLE_DEG
            
            if valid_signal:
                current_bearing = (current_bearing * (1.0 - ALPHA_RSSI)) + (target_angle * ALPHA_RSSI)
                if (now - last_packet_time) > 2.0:
                    current_bearing *= 0.9
            else:
                current_bearing *= 0.9

        # 2. Broadcast to RECEIV (Mirror)
        try:
            payload = {
                "angle": current_bearing,
                "spin": is_spinning
            }
            msg = json.dumps(payload).encode('utf-8')
            udp_sock.sendto(msg, ('<broadcast>', BROADCAST_PORT))
        except Exception as e:
            pass

        # 3. Draw Local (ROOT Screen)
        draw.rectangle((0,0,width,height), fill=0)
        cx, cy = width//2, height//2
        rad = 50
        
        color = (0, 255, 0) if is_spinning else (255, 0, 0)
        
        draw.ellipse((cx-rad, cy-rad, cx+rad, cy+rad), outline=(100,100,100), width=2)
        if not is_spinning:
            draw.line((cx, cy-rad, cx, cy-rad+10), fill=(150,150,150), width=2)
        
        a_rad = math.radians(current_bearing)
        nx = cx + rad * math.sin(a_rad)
        ny = cy - rad * math.cos(a_rad)
        draw.line((cx,cy,nx,ny), fill=color, width=5 if is_spinning else 4)
        
        if is_spinning:
            draw.text((10, height-30), "ARRIVED!", font=font, fill=(0, 255, 0))
        else:
            mode = "ML" if ml_model else "MATH"
            draw.text((5,5), mode, font=font, fill=(100,100,100))
            if l: draw.text((5, height-20), f"{max(l,r):.0f}dB", font=font, fill=(255,255,255))
        
        disp.image(image, 90)
        time.sleep(1.0/FPS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
