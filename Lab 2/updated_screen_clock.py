import time
from time import strftime, sleep, localtime
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

matcha_image =  Image.open("matcha.png").convert("RGBA")
matcha_image = matcha_image.resize((25,25))

cranky_image = Image.open("cranky.png").convert("RGBA")
cranky_image = cranky_image.resize((50,50))

mild_image = Image.open("mild.png").convert("RGBA")
mild_image = mild_image.resize((50,50))

happy_image = Image.open("happy.png").convert("RGBA")
happy_image = happy_image.resize((50,50))

MAX_MATCHA = 6
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

# includes picture of matcha to indicate how caffinated the user is
def draw_matcha(draw, image, width, height):
    hour = localtime().tm_hour
    num_cups = hour // (24//MAX_MATCHA)
    draw.rectangle((0, 0, width, height), outline=0, fill=(0,0,0))
   
    reaction_x = width//2 - 15
    reaction_y = 5

    if num_cups == 0:
      image.paste(cranky_image, (reaction_x, reaction_y), cranky_image)
        
    elif num_cups == 1:
      image.paste(mild_image, (reaction_x, reaction_y), mild_image)
        
    elif num_cups == 2:
      image.paste(happy_image, (reaction_x, reaction_y), happy_image)
        
   
    spacing = width // (MAX_MATCHA + 1)
    y = height // 2 - 15

    if num_cups >=3 or num_cups >= MAX_MATCHA:
      image.paste(cranky_image, (reaction_x, reaction_y), cranky_image)

    for i in range(MAX_MATCHA):
      cup_x = spacing * (i + 1) - 15
      if i < num_cups:
        image.paste(matcha_image, (cup_x, y), matcha_image)
      else:
        draw.ellipse((cup_x, y, cup_x + 30, y + 30), outline=(100, 100, 100), width=2)

while True:
    # Draw a black filled box to clear the image.
    #draw.rectangle((0, 0, width, height), outline=0, fill=400)
    
    draw_matcha(draw, image, width, height)
    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py
    current_time = strftime("%m/%d/%Y %H:%M:%S") 
    y = top
    draw.text((x, y), current_time, font=font, fill="#FFFFFF")

    # Display image.
    disp.image(image, rotation)
    time.sleep(1)
