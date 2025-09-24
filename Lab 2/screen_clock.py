import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

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

buttonA = digitalio.DigitalInOut(board.D23)   #GPI023 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)   #GPI024 (PIN 18)
# Use internal pull-ups; buttons then read LOW when pressed.


buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

diff = 0    #calculate the difference caused by pressing buttons

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
time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",32)
date_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)

    if a_pressed and b_pressed:
        diff = 0
    elif a_pressed:
        diff += 5
    elif b_pressed:
        diff -= 5

    t = time.localtime()
    hour, min, sec = t.tm_hour, t.tm_min, t.tm_sec
    min = min + diff
    hour_adj = min // 60
    hour = hour + hour_adj
    min = min % 60
    current_time = f"{hour:02d}:{min:02d}:{sec:02d}"
    current_date = time.strftime("%m-%d-%Y")
    alabel = "B:-5min"
    blabel = "A:+5min"

    if diff > 0:
        hint = f"Hurry! +{diff}"
    elif diff < 0:
        hint = f"Easy! -{-diff}"
    else:
        hint = "0"

    time_bbox = draw.textbbox((0,0), current_time, font=time_font)
    time_width = time_bbox[2] - time_bbox[0]
    time_height = time_bbox[3] - time_bbox[0]

    date_bbox = draw.textbbox((0,0), current_date, font=date_font)
    date_width = date_bbox[2] - date_bbox[0]
    date_height = date_bbox[3] - date_bbox[0]

    alabel_bbox = draw.textbbox((0,0), alabel, font=date_font)
    alabel_width = alabel_bbox[2] - alabel_bbox[0]
    alabel_height = alabel_bbox[3] - alabel_bbox[0]

    blabel_bbox = draw.textbbox((0,0), blabel, font=date_font)
    blabel_width = blabel_bbox[2] - blabel_bbox[0]
    blabel_height = blabel_bbox[3] - blabel_bbox[0]

    hint_bbox = draw.textbbox((0,0), hint, font=date_font)
    hint_width = hint_bbox[2] - hint_bbox[0]
    hint_height = hint_bbox[3] - hint_bbox[0]

    draw.text((width//2 - time_width//2, height//2 - time_height//2 - 20), current_time, font=time_font, fill="#FFFFFF")
    draw.text((width//2 - date_width//2, height//2 + 10), current_date, font=date_font, fill="#FFFFFF")
    draw.text((0, height - alabel_height), alabel, font=date_font, fill="#FFFFFF")
    draw.text((0, 0), blabel, font=date_font, fill="#FFFFFF")
    draw.text((width - hint_width, height - hint_height//2 - 10), hint, font=date_font, fill="#FFFFFF")



    # Display image.
    disp.image(image, rotation)
    time.sleep(0.1)
