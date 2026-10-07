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

# Button A
button_A = digitalio.DigitalInOut(board.D23)
button_A.direction = digitalio.Direction.INPUT
button_A.pull = digitalio.Pull.UP

# Button B
button_B = digitalio.DigitalInOut(board.D24)
button_B.direction = digitalio.Direction.INPUT
button_B.pull = digitalio.Pull.UP

 #TODO:Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 

start_hour = 8
bedtime_hour = 24

ice_frames = [
    "ice_100.png",
    "ice_75.png",
    "ice_50.png",
    "ice_25.png",
    "ice_10.png",
    "ice_0.png"
]

# Personal day state
day_active = False
button_b_start = None
button_b_triggered = False

while True:
    now = time.localtime()
    # Button B: hold for 2 seconds to start/end the day
    if not button_B.value:

        # Start timing when Button B is first pressed
        if button_b_start is None and not button_b_triggered:
            button_b_start = time.monotonic()

        # Trigger once after holding for 2 seconds
        elif (
            button_b_start is not None
            and not button_b_triggered
            and time.monotonic() - button_b_start >= 2
        ):
            day_active = not day_active
            button_b_triggered = True

    # Button B released: reset for the next press
    else:
        button_b_start = None
        button_b_triggered = False

    # Calculate progress from expected wake time to bedtime
    if day_active:
        current_minutes = now.tm_hour * 60 + now.tm_min

        wake_minutes = 8 * 60
        bedtime_minutes = 24 * 60

        progress = (
            (current_minutes - wake_minutes)
            / (bedtime_minutes - wake_minutes)
        )

        progress = max(0, min(progress, 1))

        frame_index = min(
            int(progress * len(ice_frames)),
            len(ice_frames) - 1
        )

    else:
        frame_index = 0

    # If the day has ended
    if not day_active:
        sleep_image = Image.new("RGB", (width, height), "black")
        sleep_draw = ImageDraw.Draw(sleep_image)

        sleep_draw.text(
            (65, 40),
            "DAY ENDED",
            font=font,
            fill="white"
        )

        sleep_draw.text(
            (45, 70),
            "Hold B to start",
            font=font,
            fill="white"
        )

        disp.image(sleep_image, rotation)

    # If Button A is being held down, show exact time
    elif not button_A.value:
        time_image = Image.new("RGB", (width, height), "black")
        time_draw = ImageDraw.Draw(time_image)

        current_time = time.strftime("%H:%M")

        time_draw.text(
            (85, 50),
            current_time,
            font=font,
            fill="white"
        )

        disp.image(time_image, rotation)

    # Otherwise show the ice clock
    else:
        ice_image = Image.open(ice_frames[frame_index]).convert("RGB")
        ice_image = ice_image.resize((width, height))

        disp.image(ice_image, rotation)

    time.sleep(0.1)


#    current_time = time.strftime("%H:%M:%S")

#   draw.text(
#        (20, 50),
#        current_time,
#        font=font,
#        fill="white"
#    )
    # Display image.

