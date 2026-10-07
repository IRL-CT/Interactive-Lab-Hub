# gpio_expander.py
# LED fun with PCF8574 I2C GPIO expander
#
# Demonstrates how to use an I2C GPIO expander to sink current
# and control multiple LEDs for quick breadboard prototyping.

import time
import random
import board
import adafruit_pcf8574

# Initialize I2C and PCF8574
i2c = board.I2C()
pcf = adafruit_pcf8574.PCF8574(i2c)

# Grab all 8 pins
leds = [pcf.get_pin(i) for i in range(8)]

# Configure as outputs (HIGH = off, LOW = LED on)
for ld in leds:
    ld.switch_to_output(value=True)

# --- Patterns ---
def chase():
    """Simple left-to-right chase"""
    for ld in leds:
        ld.value = False
        time.sleep(0.12)
        ld.value = True

def knight_rider():
    """Bounce back and forth"""
    for ld in leds:
        ld.value = False
        time.sleep(0.12)
        ld.value = True
    for ld in reversed(leds[1:-1]):
        ld.value = False
        time.sleep(0.12)
        ld.value = True

def disco():
    """Random LED flashing"""
    for _ in range(12):
        ld = random.choice(leds)
        ld.value = False
        time.sleep(0.08)
        ld.value = True

patterns = [chase, knight_rider, disco]

# --- Main Loop ---
pattern_index = 0
runs = 0

while True:
    # Run current pattern
    patterns[pattern_index]()
    runs += 1

    # After a few runs, switch pattern
    if runs >= 5:
        runs = 0
        pattern_index = (pattern_index + 1) % len(patterns)
