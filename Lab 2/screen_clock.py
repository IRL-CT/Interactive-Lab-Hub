import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from time import strftime

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

while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=400)

    # Shell scripts for system monitoring from here:
    # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-USD-usage-and-WTTR-load
    cmd = "hostname -I | cut -d' ' -f1"
    IP = "IP: " + subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "curl -s wttr.in/?format=2"
    WTTR = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = 'curl -s ils.rate.sx/1USD | cut -c1-6'
    USD = "$1USD = ₪" + subprocess.check_output(cmd, shell=True).decode("utf-8") + "ILS"
    cmd = "cat /sys/class/thermal/thermal_zone0/temp |  awk '{printf \"CPU Temp: %.1f C\", $(NF-0) / 1000}'" 
    Temp = subprocess.check_output(cmd, shell=True).decode("utf-8")

    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 
    # Draw the clock
    current_time = strftime("%m/%d/%Y %H:%M:%S")
    y = top
    draw.text((x, y), current_time, font=font, fill="#00FF00")  # green clock
    y += draw.textbbox((0,0), current_time, font=font)[3]

    # System info below the clock
    draw.text((x, y), IP, font=font, fill="#FFFFFF")
    y += draw.textbbox((0,0), IP, font=font)[3]
    draw.text((x, y), WTTR, font=font, fill="#FFFF00")
    y += draw.textbbox((0,0), WTTR, font=font)[3]
    draw.text((x, y), USD, font=font, fill="#0000FF")
    y += draw.textbbox((0,0), USD, font=font)[3]
    draw.text((x, y), Temp, font=font, fill="#FF0000")
    y += draw.textbbox((0,0), Temp, font=font)[3]

    # Display image.
    disp.image(image, rotation)
    time.sleep(1)
