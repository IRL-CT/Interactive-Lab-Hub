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

# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("KeeponTruckin.ttf", 25)
electric_font = ImageFont.truetype("Chalkboy.ttf", 40)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Buttons
buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
# Use internal pull-ups; buttons then read LOW when pressed.
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)


# load images
image = Image.open("images/forest.jpg").resize([240, 135])
rotation = 90

leaf_h = Image.open("images/newleaf.png").convert("RGBA").resize([90, 50]).rotate(320).transpose(Image.FLIP_TOP_BOTTOM)
leaf_m = Image.open("images/newleaf.png").convert("RGBA").resize([110, 50]).rotate(330).transpose(Image.FLIP_TOP_BOTTOM)
leaf_s = Image.open("images/newleaf.png").convert("RGBA").resize([90, 50]).rotate(330).transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)

puddle = Image.open("images/puddle.webp").convert("RGBA").resize([150, 40])

drop_h = Image.open("images/waterdrop.webp").convert("RGBA").resize([50, 50])
drop_m = Image.open("images/waterdrop.webp").convert("RGBA").resize([50, 50])
drop_s = Image.open("images/waterdrop.webp").convert("RGBA").resize([50, 50])

rain = Image.open("images/rain.jpg").convert("RGBA").resize([240, 135])

# adjust puddle transparency
alpha = puddle.split()[-1]
alpha = alpha.point(lambda p: p * 0.7) 
puddle.putalpha(alpha)

# create background
image.paste(leaf_h, (-10, 10), leaf_h)
image.paste(leaf_m, (10, 45), leaf_m)
image.paste(leaf_s, (150, 20), leaf_s)
image.paste(puddle, (35, 95), puddle)
draw = ImageDraw.Draw(image)

# initialize variables
drop_h_x = 60
drop_m_x = 100
drop_s_x = 130

drop_h_y = 20
drop_m_y = 55
drop_s_y = 35

drop_h_fall = False
drop_m_fall = False
drop_s_fall = False

drop_h_size = 50
drop_m_size = 50
drop_s_size = 50

show_rain = -1
prev_a_state = False
prev_b_state = False

start_time = 0
total_time = 10

# Constants
RATE = 0.02
SECOND = 1
MINUTE = SECOND * 60
HOUR = MINUTE * 60
MAX_SIZE = 40
DROP_H_Y = 20
DROP_M_Y = 60
DROP_S_Y = 35

while True:
    # start with blank background
    clear = image.copy()
    rain2 = rain.copy()
    draw = ImageDraw.Draw(clear)
    draw_rain = ImageDraw.Draw(rain2)

    # print (time.strftime("%m/%d/%Y %H:%M:%S"), end="", flush=True)
    # print("\r", end="", flush=True)

    # get current time
    curr_time = time.time()

    # make droplets fall allowing time for falling animation
    if curr_time % HOUR <= 0.5:
        drop_h_fall = True
        
    if curr_time % MINUTE <= 0.5:
        drop_m_fall = True
    
    if curr_time % SECOND <= 0.2:
        drop_s_fall = True

    # set droplet size
    if not drop_h_fall:
        drop_h_size = MAX_SIZE*(curr_time % HOUR)/HOUR + 1
    if not drop_m_fall:
        drop_m_size = MAX_SIZE*(curr_time % MINUTE)/MINUTE + 1
    if not drop_s_fall:
        drop_s_size = MAX_SIZE*(curr_time % SECOND) + 1
    
    # move droplets
    if drop_h_fall:
        drop_h_y += 10
        if drop_h_y > 90:
            drop_h_fall = False
            drop_h_y = DROP_H_Y
            drop_h_size = 1

    if drop_m_fall:
        drop_m_y += 10
        if drop_m_y > 90:
            drop_m_fall = False
            drop_m_y = DROP_M_Y
            drop_m_size = 1

    if drop_s_fall:
        drop_s_y += 10
        if drop_s_y > 90:
            drop_s_fall = False
            drop_s_y = DROP_S_Y = 35
            drop_s_size = 1
    
    # paste drops
    drop_h_r = drop_h.resize([MAX_SIZE, int(drop_h_size)])
    clear.paste(drop_h_r, (drop_h_x, drop_h_y), drop_h_r)
    drop_m_r = drop_m.resize([MAX_SIZE, int(drop_m_size)])
    clear.paste(drop_m_r, (drop_m_x, drop_m_y), drop_m_r)
    drop_s_r = drop_s.resize([MAX_SIZE, int(drop_s_size)])
    clear.paste(drop_s_r, (drop_s_x, drop_s_y), drop_s_r)

    # print time
    hour = time.strftime("%H:")
    minute = time.strftime("%M:")
    second = time.strftime("%S")
    ampm = time.strftime("%p")

    y = bottom - 30
    draw.text((60, y), hour, font=font, fill="blue")
    draw.text((100, y), minute, font=font, fill="blue")
    draw.text((140, y), second, font=font, fill="blue")

    # decide whether to show rain or not based on button press
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)

    if not prev_a_state and a_pressed:
        show_rain *= -1 
        start_time = time.time()
        total_time = 10

    if not prev_b_state and b_pressed and show_rain == 1:
        total_time += 10

    prev_a_state = a_pressed
    prev_b_state = b_pressed

    # print timer
    time_elapsed = time.time() - start_time
    if show_rain == 1 and time_elapsed < total_time:
        draw_rain.text((30, 10), f"Rain for {int(total_time - time_elapsed)}s", font=electric_font, fill="gray")
    elif show_rain == 1 and time_elapsed >= total_time:
        show_rain = -1
        total_time = 10

    # Display image.

    if show_rain == 1:
        disp.image(rain2, rotation)
    else:
        disp.image(clear, rotation)

    time.sleep(RATE)
