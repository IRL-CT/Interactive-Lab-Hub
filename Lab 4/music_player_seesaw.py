#!/usr/bin/env python3
import os, sys, time, glob, subprocess
import qwiic_gpio
import pygame
import board
from adafruit_seesaw import seesaw, rotaryio

LED_PINS = [6, 7, 0, 5, 3, 4]
ADDR_CANDS = [0x36, 0x27]
MIN_VOL, MAX_VOL = 0, 100
STEP = 1
POLL_DELAY = 0.01

def find_fixed_wav():
    base = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
    cands = sorted(glob.glob(os.path.join(base, "music", "*_fixed.wav")))
    return cands[0] if cands else None

def set_system_volume(pct):
    pct = max(MIN_VOL, min(MAX_VOL, int(pct)))
    subprocess.run(["amixer", "sset", "Master", f"{pct}%"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))

def update_leds(io, volume):
    num = len(LED_PINS)
    level = int(round((volume / float(MAX_VOL)) * num))
    for i, p in enumerate(LED_PINS):
        io.digitalWrite(p, io.GPIO_LO if i < level else io.GPIO_HI)

def main():
    wav = find_fixed_wav()
    if not wav:
        print("No *_fixed.wav in ./music")
        sys.exit(1)

    ss = None
    for addr in ADDR_CANDS:
        try:
            ss_try = seesaw.Seesaw(board.I2C(), addr=addr)
            ss = ss_try
            break
        except Exception:
            pass
    if ss is None:
        print("Seesaw device not found. run i2cdetect -y 1")
        sys.exit(1)

    encoder = rotaryio.IncrementalEncoder(ss)
    last_pos = encoder.position

    io = qwiic_gpio.QwiicGPIO()
    if not io.isConnected():
        print("Qwiic GPIO not connected")
        sys.exit(1)
    io.begin()
    for p in LED_PINS:
        io.pinMode(p, io.GPIO_OUT)
        io.digitalWrite(p, io.GPIO_HI)

    pygame.mixer.init()
    pygame.mixer.music.load(wav)
    pygame.mixer.music.play(-1)

    volume = 50
    set_system_volume(volume)
    pygame.mixer.music.set_volume(volume / 100.0)
    update_leds(io, volume)

    try:
        while True:
            pos = encoder.position
            delta = pos - last_pos
            if delta:
                volume = clamp(volume + delta * STEP, MIN_VOL, MAX_VOL)
                set_system_volume(volume)
                pygame.mixer.music.set_volume(volume / 100.0)
                update_leds(io, volume)
                last_pos = pos
            time.sleep(POLL_DELAY)
    except KeyboardInterrupt:
        pass
    finally:
        for p in LED_PINS:
            io.digitalWrite(p, io.GPIO_HI)

if __name__ == "__main__":
    main()
