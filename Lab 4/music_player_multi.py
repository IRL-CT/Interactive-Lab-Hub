#!/usr/bin/env python3
import os, sys, time
from glob import glob
import pygame
from gpiozero import RotaryEncoder
import qwiic_gpio

PINS = [6, 7, 0, 5, 3, 4]
STEP = 2
REFRESH = 0.02

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def pick_tracks():
    here = os.path.dirname(__file__)
    music_dir = os.path.join(here, "music")
    cands = sorted(glob(os.path.join(music_dir, "*_fixed.wav")))
    if not cands:
        cands = sorted(glob(os.path.join(music_dir, "*.wav"))) + \
                sorted(glob(os.path.join(music_dir, "*.mp3")))
    if not cands:
        raise RuntimeError("no audio files found in ./music")
    return cands

def init_audio(track):
    pygame.mixer.init(frequency=44100, channels=2, buffer=1024)
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.load(track)
    pygame.mixer.music.play(-1)

def init_encoder():
    return RotaryEncoder(17, 27, max_steps=1000, wrap=False)

def init_qwiic_gpio():
    gpio = qwiic_gpio.QwiicGPIO()
    if not gpio.isConnected():
        print("Qwiic GPIO not found", file=sys.stderr)
        sys.exit(1)
    gpio.begin()
    for p in PINS:
        gpio.pinMode(p, gpio.GPIO_OUT)
    return gpio

def show_volume_bar(gpio, volume):
    n = round(volume * len(PINS) / 100.0)
    on, off = gpio.GPIO_LO, gpio.GPIO_HI
    for i, pin in enumerate(PINS):
        gpio.digitalWrite(pin, on if i < n else off)

def main():
    tracks = pick_tracks()
    init_audio(tracks[0])
    enc = init_encoder()
    gpio = init_qwiic_gpio()

    volume = 30
    last = enc.steps
    pygame.mixer.music.set_volume(volume / 100.0)
    show_volume_bar(gpio, volume)
    print(f"playing: {os.path.basename(tracks[0])}")

    try:
        while True:
            s = enc.steps
            d = s - last
            if d:
                volume = clamp(volume + d * STEP, 0, 100)
                last = s
                pygame.mixer.music.set_volume(volume / 100.0)
                show_volume_bar(gpio, volume)
                print(f"volume {volume:3d}%")
            time.sleep(REFRESH)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
