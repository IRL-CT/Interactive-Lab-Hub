# image_fixed.py
# Button A always shows img1.jpg, Button B always shows img2.jpg

import time
import digitalio
import board
from PIL import Image
import adafruit_rgb_display.st7789 as st7789

# ---- Display & SPI setup ----
BAUDRATE = 24000000
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)  # same as your original image.py
spi = board.SPI()

disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
    rotation=90,  # landscape
)

# Effective screen dimensions in landscape
height = disp.width
width = disp.height

# ---- Backlight ----
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

# ---- Buttons ----
btnA = digitalio.DigitalInOut(board.D23)
btnA.switch_to_input(pull=digitalio.Pull.UP)
btnB = digitalio.DigitalInOut(board.D24)
btnB.switch_to_input(pull=digitalio.Pull.UP)

def load_fitted_image(path: str) -> Image.Image:
    """Load image, preserve aspect ratio, then center-crop to screen size."""
    img = Image.open(path).convert("RGB")
    image_ratio = img.width / img.height
    screen_ratio = width / height
    if screen_ratio < image_ratio:
        scaled_width = img.width * height // img.height
        scaled_height = height
    else:
        scaled_width = width
        scaled_height = img.height * width // img.width
    img = img.resize((scaled_width, scaled_height), Image.BICUBIC)
    x = (scaled_width - width) // 2
    y = (scaled_height - height) // 2
    img = img.crop((x, y, x + width, y + height))
    return img

def show(path: str):
    disp.image(load_fitted_image(path))

# Initial display: img1
show("img1.jpg")

def wait_release(pin):
    time.sleep(0.02)
    while not pin.value:
        time.sleep(0.02)

print("Button A = img1, Button B = img2. Ctrl+C to exit.")
try:
    while True:
        if not btnA.value:
            show("img1.jpg")
            wait_release(btnA)
        if not btnB.value:
            show("img2.jpg")
            wait_release(btnB)
        time.sleep(0.01)
except KeyboardInterrupt:
    pass
