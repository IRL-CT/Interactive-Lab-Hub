import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

import requests

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
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

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

def wrap_text(text, font, max_width):
    lines = []
    if not text:
        return lines
    words = text.split(' ')
    current_line = ""
    for word in words:
        # Check width of current line with new word
        if len(current_line + word + " ") < 30:
            if current_line:
                current_line += " "
            current_line += word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=400)

    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 
    time_string = time.strftime("%m/%d/%Y %H:%M")
    draw.text((x, top), time_string, font=font, fill="#FFFF00")

    try:
        response = requests.get("https://www.affirmations.dev/")
        if response.status_code == 200:
            data = response.json()
            affirmation = data["affirmation"]
        else:
            affirmation = "Error fetching affirmation."
    except requests.exceptions.RequestException:
        affirmation = "Network error."

    # Wrap and draw the affirmation text
    wrapped_lines = wrap_text(affirmation, font, width)
    line_y = top + 30  # Start drawing below the time
    for line in wrapped_lines:
        draw.text((x, line_y), line, font=font, fill="#FFFFFF")
        line_y += 30  # Add some padding between lines

    # Display image.
    disp.image(image, rotation)
    time.sleep(60)
