import os
import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# Folder holding the hour-by-hour mascot images
IMAGES_DIR = "images"

# Maps 24-hour clock hour -> filename in IMAGES_DIR
HOUR_IMAGES = {
    0: "17_12AM_Hanging_Upside_Down_320x240.jpg",
    1: "18_01AM_Getting_into_Bed_320x240.jpg",
    2: "19_02AM-07AM_Sleeping_320x240.jpg",
    3: "19_02AM-07AM_Sleeping_320x240.jpg",
    4: "19_02AM-07AM_Sleeping_320x240.jpg",
    5: "19_02AM-07AM_Sleeping_320x240.jpg",
    6: "19_02AM-07AM_Sleeping_320x240.jpg",
    7: "19_02AM-07AM_Sleeping_320x240.jpg",
    8: "01_08AM_Waking_Up_320x240.jpg",
    9: "02_09AM_Brushing_Teeth_320x240.jpg",
    10: "03_10AM_Eating_Breakfast_320x240.jpg",
    11: "04_11AM_Going_to_Class_320x240.jpg",
    12: "05_12PM_Sitting_on_a_Building_320x240.jpg",
    13: "06_01PM_Eating_Lunch_320x240.jpg",
    14: "07_02PM_MidDay_Swing_320x240.jpg",
    15: "08_03PM_Gym_320x240.jpg",
    16: "09_04PM_Walking_Grandma_320x240.jpg",
    17: "10_05PM_With_Chloe_320x240.jpg",
    18: "11_06PM_Getting_Pizza_320x240.jpg",
    19: "12_07PM_Getting_Chai_320x240.jpg",
    20: "13_08PM_Doing_Homework_320x240.jpg",
    21: "14_09PM_Stopping_a_Villain_320x240.jpg",
    22: "15_10PM_With_Grandfather_320x240.jpg",
    23: "16_11PM_Visiting_a_Memorial_320x240.jpg",
}

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

# Button A: hold it down to check the exact digital time.
buttonA = digitalio.DigitalInOut(board.D23)
buttonA.switch_to_input(pull=digitalio.Pull.UP)

# Cache of mascot images, scaled/cropped to fill the screen, keyed by filename.
_mascot_cache = {}


def get_mascot(filename):
    if filename not in _mascot_cache:
        mascot = Image.open(os.path.join(IMAGES_DIR, filename)).convert("RGB")
        mascot_ratio = mascot.width / mascot.height
        screen_ratio = width / height
        if screen_ratio < mascot_ratio:
            scaled_width = mascot.width * height // mascot.height
            scaled_height = height
        else:
            scaled_width = width
            scaled_height = mascot.height * width // mascot.width
        mascot = mascot.resize((scaled_width, scaled_height), Image.BICUBIC)
        crop_x = scaled_width // 2 - width // 2
        crop_y = scaled_height // 2 - height // 2
        mascot = mascot.crop((crop_x, crop_y, crop_x + width, crop_y + height))
        _mascot_cache[filename] = mascot
    return _mascot_cache[filename]


while True:
    if not buttonA.value:
        # Button A held: show the digital time instead of the mascot.
        draw.rectangle((0, 0, width, height), outline=0, fill=400)

        curr_time = time.strftime("%m/%d/%Y %H:%M:%S")
        y = top
        draw.text((x, y), curr_time, font=font, fill="#FFFFFF")

        disp.image(image, rotation)
    else:
        # Default view: mascot for the current hour tells the time.
        hour = int(time.strftime("%H"))
        mascot = get_mascot(HOUR_IMAGES[hour])
        disp.image(mascot, rotation)
    time.sleep(0.1)