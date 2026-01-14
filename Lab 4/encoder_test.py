# SPDX-FileCopyrightText: 2021 John Furcean
# SPDX-License-Identifier: MIT
# Simple test for Adafruit I2C QT Rotary Encoder

import board
from adafruit_seesaw import seesaw, rotaryio, digitalio

# Initialize I2C connection to the rotary encoder at address 0x36
seesaw = seesaw.Seesaw(board.I2C(), addr=0x36)

# Check product ID to make sure it’s the correct firmware
seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF
print("Found encoder product {}".format(seesaw_product))
if seesaw_product != 4991:
    print("Warning: Unexpected product ID, expected 4991")

# Configure built-in push button
seesaw.pin_mode(24, seesaw.INPUT_PULLUP)
button = digitalio.DigitalIO(seesaw, 24)
button_held = False

# Configure rotary encoder
encoder = rotaryio.IncrementalEncoder(seesaw)
last_position = None

print("Rotate the knob or press the button...")

# Main loop
while True:
    # Negate position so clockwise rotation gives positive numbers
    position = -encoder.position

    if position != last_position:
        last_position = position
        print("Position:", position)

    # Detect button press
    if not button.value and not button_held:
        button_held = True
        print("Button pressed")

    # Detect button release
    if button.value and button_held:
        button_held = False
        print("Button released")
