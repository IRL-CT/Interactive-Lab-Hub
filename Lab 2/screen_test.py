# rpi5_minipitft_st7789.py
# Works on Raspberry Pi 5 with Adafruit Blinka backend (lgpio) and SPI enabled.
# Wiring change: connect the display's CS to GPIO5 (pin 29), not CE0.

import time
import digitalio
import board

from adafruit_rgb_display.rgb import color565
import adafruit_rgb_display.st7789 as st7789
import webcolors

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
display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
    # rotation=0  # uncomment/change if your screen orientation is off
)

# ---------------------------
# Backlight + Buttons
# ---------------------------
backlight = digitalio.DigitalInOut(board.D22)  # GPIO22 (PIN 15)
backlight.switch_to_output(value=True)

buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
# Use internal pull-ups; buttons then read LOW when pressed.
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# ---------------------------
# Ask user for a color
# ---------------------------
screenColor = None
while not screenColor:
    try:
        name = input('Type the name of a color and hit enter: ')
        rgb = webcolors.name_to_rgb(name)
        screenColor = color565(rgb.red, rgb.green, rgb.blue)
    except ValueError:
        print("whoops I don't know that one")

# ---------------------------
# Main loop
# ---------------------------
print("Press A for WHITE, B for your color, both to turn backlight OFF.")
while True:
    # Buttons are active-LOW because of pull-ups
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)

    if a_pressed and b_pressed:
        backlight.value = False  # turn off backlight
    else:
        backlight.value = True   # turn on backlight

    if b_pressed and not a_pressed:
        display.fill(screenColor)               # user's color
    elif a_pressed and not b_pressed:
        display.fill(color565(255, 255, 255))   # white
    else:
        display.fill(color565(0, 255, 0))       # green

    time.sleep(0.02)  # small debounce / CPU break
