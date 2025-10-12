#!/usr/bin/env python3
# joystick_voice_runner.py

import time
import subprocess
from smbus2 import SMBus

I2C_ADDR       = 0x20
BUS_NUM        = 1
VOICE_SCRIPT   = "my-scripts/voice_interaction.py"
COOLDOWN_SEC   = 1.2
CALIBRATE_SEC  = 1.0
READ_HZ        = 14
THRESH         = 4000
DEAD_BAND      = 1200
USE_Y_AS_HORIZ = True

def read_xyz(bus: SMBus):
    blk = bus.read_i2c_block_data(I2C_ADDR, 0x00, 5)
    x = blk[0] | (blk[1] << 8)
    y = blk[2] | (blk[3] << 8)
    b = blk[4]
    return x, y, b

def clamp_centered(val, center, dead_band):
    off = val - center
    if abs(off) <= dead_band:
        return 0
    return off

def dir_from_offsets(h_off, v_off, thresh):
    horiz = 'MID'
    vert  = 'MID'
    if   h_off >  thresh: horiz = 'RIGHT'
    elif h_off < -thresh: horiz = 'LEFT'
    if   v_off >  thresh: vert  = 'DOWN'
    elif v_off < -thresh: vert  = 'UP'
    return horiz, vert

def is_pressed(btn_raw):
    return btn_raw < 10

def run_voice_interaction():
    try:
        subprocess.run(["python3", VOICE_SCRIPT], check=False)
    except Exception as e:
        print(f"[WARN] Voice script error: {e}")

def main():
    bus = SMBus(BUS_NUM)
    print("Centering... keep joystick released ~1s")
    cx_samples, cy_samples = [], []
    t0 = time.time()
    while time.time() - t0 < CALIBRATE_SEC:
        x, y, _ = read_xyz(bus)
        cx_samples.append(x)
        cy_samples.append(y)
        time.sleep(0.02)
    cx = sum(cx_samples) // max(1, len(cx_samples))
    cy = sum(cy_samples) // max(1, len(cy_samples))
    print(f"[CAL] Center X={cx}, Y={cy}")

    last_btn_raw = None
    last_trigger_time = 0.0
    interval = 1.0 / READ_HZ

    print("Ready. Move joystick or press button. Ctrl+C to quit.")
    try:
        while True:
            x, y, b = read_xyz(bus)
            h_raw = (y if USE_Y_AS_HORIZ else x)
            v_raw = (x if USE_Y_AS_HORIZ else y)
            h_off = clamp_centered(h_raw, (cy if USE_Y_AS_HORIZ else cx), DEAD_BAND)
            v_off = clamp_centered(v_raw, (cx if USE_Y_AS_HORIZ else cy), DEAD_BAND)

            horiz, vert = dir_from_offsets(h_off, v_off, THRESH)
            if horiz != 'MID' or vert != 'MID':
                print(f"[DIR] {horiz} {vert} | raw X={x} Y={y}")

            pressed = is_pressed(b)
            was_pressed = (last_btn_raw is not None and is_pressed(last_btn_raw))
            if pressed and not was_pressed:
                now = time.time()
                if now - last_trigger_time >= COOLDOWN_SEC:
                    print("[BTN] PRESSED -> Voice interaction")
                    last_trigger_time = now
                    run_voice_interaction()
                else:
                    print("[BTN] Ignored (cooldown)")
            last_btn_raw = b
            time.sleep(interval)

    except KeyboardInterrupt:
        pass
    finally:
        bus.close()
        print("Bye!")

if __name__ == "__main__":
    main()
