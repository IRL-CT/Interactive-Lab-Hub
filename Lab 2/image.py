# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import digitalio
import board
from PIL import Image, ImageDraw

import adafruit_rgb_display.ili9341 as ili9341
import adafruit_rgb_display.st7789 as st7789
import adafruit_rgb_display.hx8357 as hx8357
import adafruit_rgb_display.st7735 as st7735
import adafruit_rgb_display.ssd1351 as ssd1351
import adafruit_rgb_display.ssd1331 as ssd1331


# --------------------------------------------------
# DISPLAY SETUP
# --------------------------------------------------

# Configuration for CS and DC pins
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

# Display baudrate
BAUDRATE = 24000000

# Setup SPI
spi = board.SPI()

# Create display
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
)


# --------------------------------------------------
# SCREEN SIZE
# --------------------------------------------------

if disp.rotation % 180 == 90:
    height = disp.width
    width = disp.height
else:
    width = disp.width
    height = disp.height


# --------------------------------------------------
# CLEAR SCREEN
# --------------------------------------------------

image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)

draw.rectangle(
    (0, 0, width, height),
    outline=0,
    fill=(0, 0, 0)
)

disp.image(image)


# --------------------------------------------------
# BACKLIGHT
# --------------------------------------------------

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True


# --------------------------------------------------
# BUTTON SETUP
# --------------------------------------------------

# Change D23 if your button uses a different GPIO pin
button = digitalio.DigitalInOut(board.D23)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP


# --------------------------------------------------
# IMAGES
# --------------------------------------------------

# Put your image filenames here
images = [
    "spiderman.jpg",
    "batman.jpg"
]

current_image = 0


# --------------------------------------------------
# FUNCTION TO DISPLAY AN IMAGE
# --------------------------------------------------

def display_image(filename):

    image = Image.open(filename)

    # Make sure image is RGB
    image = image.convert("RGB")

    # Determine image and screen ratios
    image_ratio = image.width / image.height
    screen_ratio = width / height

    # Resize image while maintaining aspect ratio
    if screen_ratio < image_ratio:
        scaled_width = image.width * height // image.height
        scaled_height = height
    else:
        scaled_width = width
        scaled_height = image.height * width // image.width

    image = image.resize(
        (scaled_width, scaled_height),
        Image.BICUBIC
    )

    # Crop and center image
    x = scaled_width // 2 - width // 2
    y = scaled_height // 2 - height // 2

    image = image.crop(
        (x, y, x + width, y + height)
    )

    # Display image
    disp.image(image)


# --------------------------------------------------
# SHOW FIRST IMAGE
# --------------------------------------------------

display_image(images[current_image])


# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------

while True:

    # Button is pressed
    if not button.value:

        # Move to next image
        current_image = (current_image + 1) % len(images)

        # Display new image
        display_image(images[current_image])

        # Wait until button is released
        while not button.value:
            time.sleep(0.01)

        # Small debounce delay
        time.sleep(0.1)

    time.sleep(0.01)