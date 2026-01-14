# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
from adafruit_apds9960.apds9960 import APDS9960

import qwiic_button
import sys

import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import webcolors

import busio
import adafruit_mpr121
# import speech_recognition as sr
import subprocess

# Proximity sensor
i2c = board.I2C()
apds = APDS9960(i2c)

apds.enable_proximity = True

# Default button (0x6F)
button1 = qwiic_button.QwiicButton() # green
# Button with A0 soldered (0x6E)
button2 = qwiic_button.QwiicButton(0x6E) # red

button1.begin()
button2.begin()
print("Buttons ready!")

# --- Speak using espeak ---
def speak(text):
    print(f"Pi says: {text}")
    subprocess.run(["espeak", "-s", "165", text])

# ---------------------------
# SPI + Display configuration
# ---------------------------
# Use a FREE GPIO for CS to avoid conflicts with the SPI driver owning CE0/CE1.
cs_pin = digitalio.DigitalInOut(board.D5)     # GPIO5  (PIN 29)  <-- wire display CS here
dc_pin = digitalio.DigitalInOut(board.D25)    # GPIO25 (PIN 22)
reset_pin = None

# Safer baudrate for stability; you can try 64_000_000 if your wiring is short/clean.
BAUDRATE = 64000000

# Create SPI object on SPI0 (spidev0.* must exist; enable SPI in raspi-config).
spi = board.SPI()

# For Adafruit mini PiTFT 1.14" (240x135) ST7789 use width=135, height=240, x/y offsets below.
# If you actually have a 240x240 panel, set width=240, height=240 and x_offset=y_offset=0.
# Keep the “native” portrait dims for this board
DISPLAY_WIDTH  = 135
DISPLAY_HEIGHT = 240

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    x_offset=53,
    y_offset=40,
)

# ---------------------------
# Backlight + Buttons
# ---------------------------
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# ---------------------------
# Global Variables
# ---------------------------
prev_mode = 1
mode = 0 # 0 for normal, 1 for warning
image = Image.new("RGB", (display.width, display.height))
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

print("Display size:", display.width, "x", display.height)
print("Display ready!")

# ---------------------------
# Main loop
# ---------------------------

print("Press Button 1 to start")

while not button1.is_button_pressed():
    pass

print("Start the application")
speak("start the application.")

while True:
    print("Proximity:", apds.proximity)

    if apds.proximity > 1:
        mode = 1
    else:
        mode = 0

    if mode != prev_mode:
        draw.rectangle((0, 0, image.width, image.height), fill=0)
        
        if mode == 0:
            draw.text((10, 40), "Good :)", font=font, fill="#00FF00")
            display.image(image)

        else:
            draw.text((10, 40), "Too close!", font=font, fill="#ff0000")
            display.image(image)

            print("Long press Button 2 to stop the warning.")
            while not button2.is_button_pressed():
                speak("You are too close to the screen.")
        
        prev_mode = mode
    
    time.sleep(0.2)
