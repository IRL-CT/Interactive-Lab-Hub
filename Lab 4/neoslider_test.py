"""Read the NeoSlider and light its four NeoPixels to match the position."""

import time
import board
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.analoginput import AnalogInput
from adafruit_seesaw import neopixel

seesaw = Seesaw(board.I2C(), addr=0x30)

product = (seesaw.get_version() >> 16) & 0xFFFF
print(f"Found product {product}")
if product != 5295:
    print("Wrong firmware loaded? Expected 5295")

slide = AnalogInput(seesaw, 18)
pixels = neopixel.NeoPixel(seesaw, 14, 4)

while True:
    pos = slide.value  # 0 at one end, 1023 at the other
    lit = round(4 * pos / 1023)
    for i in range(4):
        pixels[i] = (0, 40, 0) if i < lit else (0, 0, 0)
    print(f"Position: {pos}")
    time.sleep(0.05)
