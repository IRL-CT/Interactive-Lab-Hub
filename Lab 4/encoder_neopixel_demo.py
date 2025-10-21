import time, board
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel

# I2C device
ss = seesaw.Seesaw(board.I2C(), addr=0x36)

# Optional: check product ID (4991 expected)
prod = (ss.get_version() >> 16) & 0xFFFF
print("Found product", prod, "(expect 4991)")

# Inputs
ss.pin_mode(24, ss.INPUT_PULLUP)
button = digitalio.DigitalIO(ss, 24)
enc = rotaryio.IncrementalEncoder(ss)
last_pos = None

# Onboard NeoPixel on pin 6, count = 1
pix = neopixel.NeoPixel(ss, 6, 1)
pix.brightness = 0.4

def hsv_to_rgb(h, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r*255), int(g*255), int(b*255))

hue = 0.0
sat = 1.0
val = 1.0
bright_levels = [0.15, 0.4, 0.8]
b_idx = 1

print("Rotate to change color, press to toggle brightness.")
while True:
    # Encoder position (negate so clockwise is positive)
    pos = -enc.position
    if pos != last_pos:
        last_pos = pos
        hue = (pos % 360) / 360.0
        pix[0] = hsv_to_rgb(hue, sat, val)

    # Button: low when pressed
    if not button.value:
        # Debounce: wait for release
        while not button.value:
            time.sleep(0.02)
        b_idx = (b_idx + 1) % len(bright_levels)
        pix.brightness = bright_levels[b_idx]
        print("Brightness ->", pix.brightness)

    time.sleep(0.02)
