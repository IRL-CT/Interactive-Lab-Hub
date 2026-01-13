#!/usr/bin/env python3
import time, sys, subprocess
import qwiic_gpio
from gpiozero import RotaryEncoder

PINS = [6, 7, 0, 5, 3, 4]
STEP = 2

def clamp(v, lo, hi): 
    return lo if v < lo else hi if v > hi else v

def set_system_volume(percent):
    for ctl in ("Master","PCM","Headphone","Speaker"):
        try:
            subprocess.run(["amixer","-q","sset",ctl,f"{int(percent)}%"], check=True)
            return
        except Exception:
            pass

def main():
    enc = RotaryEncoder(17, 27, max_steps=1000, wrap=False)
    gpio = qwiic_gpio.QwiicGPIO()
    if not gpio.isConnected():
        print("Qwiic GPIO not found.", file=sys.stderr); sys.exit(1)
    gpio.begin()
    for p in PINS:
        gpio.pinMode(p, gpio.GPIO_OUT)

    ON, OFF = gpio.GPIO_LO, gpio.GPIO_HI
    volume, last = 30, enc.steps
    set_system_volume(volume)

    while True:
        s = enc.steps
        d = s - last
        if d:
            volume = clamp(volume + d * STEP, 0, 100)
            last = s
            n = round(volume * len(PINS) / 100.0)
            for i, pin in enumerate(PINS):
                gpio.digitalWrite(pin, ON if i < n else OFF)
            print(f"Volume {volume}% | LEDs {n}/{len(PINS)}")
            set_system_volume(volume)
        time.sleep(0.02)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
