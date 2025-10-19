#!/usr/bin/env python3
import os, sys, time, glob, subprocess
import qwiic_gpio
from gpiozero import Device, RotaryEncoder, Button
from gpiozero.pins.lgpio import LGPIOFactory

print("Initializing...")

try:
    import pygame
    HAVE_PYGAME = True
except Exception as e:
    print(f"Error: {e}")
    HAVE_PYGAME = False

try:
    Device.pin_factory = LGPIOFactory()
    print("GPIO initialized")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

CLK, DT, SW = 5, 6, 13
LED_PINS = [6, 7, 0, 5, 3, 4]
STEP = 5
MIN_VOL, MAX_VOL = 0, 100

def find_fixed_wav():
    base = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
    cands = sorted(glob.glob(os.path.join(base, "music", "*_fixed.wav")))
    return cands[0] if cands else None

def set_system_volume(pct):
    subprocess.run(["amixer", "sset", "Master", f"{pct}%"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def level_from_volume(pct, segments):
    return max(0, min(segments, int(round(pct * segments / 100.0))))

def update_led_bar(io, level):
    for i, pin in enumerate(LED_PINS):
        io.digitalWrite(pin, io.GPIO_LO if i < level else io.GPIO_HI)

class Player:
    def __init__(self, path):
        self.path = path
        pygame.mixer.init()
        pygame.mixer.music.load(self.path)
        pygame.mixer.music.play(-1)
    def set_volume(self, pct):
        pygame.mixer.music.set_volume(pct / 100.0)
    def pause_toggle(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()

def main():
    wav = find_fixed_wav()
    if not wav:
        print("No *_fixed.wav found in ./music")
        sys.exit(1)

    io = qwiic_gpio.QwiicGPIO()
    if not io.isConnected():
        print("Qwiic GPIO not found.")
        sys.exit(1)
    io.begin()
    for p in LED_PINS:
        io.pinMode(p, io.GPIO_OUT)
        io.digitalWrite(p, io.GPIO_HI)

    player = Player(wav)
    vol = 50
    set_system_volume(vol)
    player.set_volume(vol)
    update_led_bar(io, level_from_volume(vol, len(LED_PINS)))

    enc = RotaryEncoder(CLK, DT, wrap=False, max_steps=100)
    btn = Button(SW, hold_time=0.6)

    def on_rotate():
        nonlocal vol
        new_vol = max(MIN_VOL, min(MAX_VOL, vol + enc.steps * STEP))
        if new_vol != vol:
            vol = new_vol
            set_system_volume(vol)
            player.set_volume(vol)
            update_led_bar(io, level_from_volume(vol, len(LED_PINS)))
        enc.steps = 0

    def on_press():
        player.pause_toggle()

    btn.when_pressed = on_press

    print("Running... Press Ctrl+C to exit.")
    try:
        while True:
            on_rotate()
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in LED_PINS:
            io.digitalWrite(p, io.GPIO_HI)

if __name__ == "__main__":
    main()
