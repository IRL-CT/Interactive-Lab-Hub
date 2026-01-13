import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from adafruit_rgb_display.rgb import color565
import random
from datetime import datetime

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
# font = ImageFont.truetype("/usr/share/fonts/truetype/quicksand/Quicksand-Regular.ttf", 18)
font = ImageFont.truetype("/home/pi/Interactive-Lab-Hub/Lab 2/fonts/dogica/dogicapixel.ttf", 16)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# define buttons
buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
# Use internal pull-ups; buttons then read LOW when pressed.
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# Get random letters and positions for the bouncing letters
letters = [chr(random.randint(65, 90)) for _ in range(40)]
positions = [[random.randint(0, width), random.randint(0, height)] for _ in letters]
velocities = [[random.choice([-1,1]), random.choice([-1,1])] for _ in letters]

# Daily routines words
routines = {
    "morning": ["wake", "coffee", "commute"],
    "afternoon": ["work", "focus", "lunch"],
    "evening": ["relax", "dinner", "rest"],
    "night": ["sleep", "dream", "quiet"]
}

def get_time_words():
    now = datetime.datetime.now()
    hour = now.hour
    time_str = now.strftime("%I:%M %p")
    if 6 <= hour < 12:
        routine = routines["morning"]
    elif 12 <= hour < 17:
        routine = routines["afternoon"]
    elif 17 <= hour < 22:
        routine = routines["evening"]
    else:
        routine = routines["night"]
    return time_str, routine


while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=400)

    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 
    # draw.text((x, top+5), time.strftime("%m/%d/%Y %H:%M:%S"), font=font, fill="#FFFFFF")
    for i, letter in enumerate(letters):
        x, y = positions[i]
        dx, dy = velocities[i]

        # movement
        x += dx
        y += dy

        # # bounce when hitting edge
        if x < 0 or x > width - 10:
            dx *= -1
        if y < 0 or y > height - 10:
            dy *= -1

        positions[i] = [x, y]
        velocities[i] = [dx, dy]

        # draw letter
        draw.text((x, y), letter, font=font, fill="#FFFFFF")
    
    # Display image.
    disp.image(image, rotation)
    time.sleep(0.2)
