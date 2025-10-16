#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Color-to-Sound Demo using APDS9960 + simpleaudio
- Continuously reads color sensor data
- Converts RGB values into harmonic tones
"""

import time
import board
from adafruit_apds9960.apds9960 import APDS9960
import numpy as np
import simpleaudio as sa
import math

def play_rgb_tone(r, g, b, duration=0.25):
    """Convert RGB to a tri-tone sound."""
    sr = 44100
    t = np.linspace(0, duration, int(sr * duration), False)

    # Map RGB → frequencies (Hz)
    f_r = 220 + (r / 255) * 440
    f_g = 440 + (g / 255) * 440
    f_b = 660 + (b / 255) * 440

    # Mix three sine waves
    tone = (np.sin(2 * np.pi * f_r * t) +
            np.sin(2 * np.pi * f_g * t) +
            np.sin(2 * np.pi * f_b * t)) / 3

    # Convert to 16-bit PCM and play
    audio = np.int16(tone * 32767)
    sa.play_buffer(audio, 1, 2, sr).wait_done()

def normalize_rgb(r, g, b, c):
    """Normalize RGB by clear channel to 0–255."""
    if c == 0:
        return (0, 0, 0)
    rn = int(255 * r / c)
    gn = int(255 * g / c)
    bn = int(255 * b / c)
    return (min(255, rn), min(255, gn), min(255, bn))

def main():
    print("Color-to-Sound demo started (Ctrl+C to exit)")

    i2c = board.I2C()
    apds = APDS9960(i2c)
    apds.enable_color = True

    while True:
        while not apds.color_data_ready:
            time.sleep(0.01)
        r, g, b, c = apds.color_data
        r, g, b = normalize_rgb(r, g, b, c)
        print(f"R={r:3d} G={g:3d} B={b:3d}")
        play_rgb_tone(r, g, b, duration=0.2)
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
