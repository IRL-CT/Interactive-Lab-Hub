import time
from time import strftime
from time import localtime
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


# --- Buttons ---
btn_top = digitalio.DigitalInOut(board.D5)   # Button A
btn_top.switch_to_input(pull=digitalio.Pull.UP)

btn_bottom = digitalio.DigitalInOut(board.D6)  # Button B
btn_bottom.switch_to_input(pull=digitalio.Pull.UP)

# --- Drawing setup ---
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

# --- Helper ---
def pages_today(total_pages=24):
    t = localtime()
    seconds_today = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
    return int((seconds_today / 86400.0) * total_pages)

# --- State ---
page_counter = 0
show_counter = False

# --- Page turn animation ---
def page_turn():
    for offset in range(0, width//2, 20):
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
        mid = width // 2

        # static right page
        draw.rectangle((mid + 5, 40, width - 10, 200), outline=(255, 255, 255))

        # animated left page sliding away
        draw.rectangle((10 + offset, 40, mid - 5 + offset, 200), outline=(255, 255, 255))

        disp.image(image, rotation)
        time.sleep(0.05)

# --- Main loop ---
while True:
    if not btn_top.value:  # pressed (LOW)
        page_counter += 1
        page_turn()

    if not btn_bottom.value:  # pressed
        show_counter = not show_counter

    # Clear screen
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

    if show_counter:
        draw.text((50, 120), f"Counter: {page_counter}", font=font, fill=(0, 255, 0))
    else:
        total_pages = 24
        current_page = pages_today(total_pages)
        mid = width // 2

        # Draw book outline
        draw.rectangle((10, 40, mid - 5, 200), outline=(255, 255, 255))
        draw.rectangle((mid + 5, 40, width - 10, 200), outline=(255, 255, 255))

        # Show page numbers
        draw.text((30, 100), f"Page {current_page}", font=font, fill=(255, 255, 0))
        draw.text((mid + 20, 100), f"of {total_pages}", font=font, fill=(0, 255, 255))

        # Progress bar
        progress = current_page / total_pages
        bar_width = int((width - 20) * progress)
        draw.rectangle((10, 210, 10 + bar_width, 230), fill=(150, 75, 0))

    # Push to display
    disp.image(image, rotation)
    time.sleep(0.1)



# # Create blank image for drawing.
# # Make sure to create image with mode 'RGB' for full color.
# height = disp.width  # we swap height/width to rotate it to landscape!
# width = disp.height
# image = Image.new("RGB", (width, height))
# rotation = 90

# # Get drawing object to draw on image.
# draw = ImageDraw.Draw(image)

# # Draw a black filled box to clear the image.
# draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
# disp.image(image, rotation)
# # Draw some shapes.
# # First define some constants to allow easy resizing of shapes.
# padding = -2
# top = padding
# bottom = height - padding
# # Move left to right keeping track of the current x position for drawing shapes.
# x = 0

# # Alternatively load a TTF font.  Make sure the .ttf font file is in the
# # same directory as the python script!
# # Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# # Turn on the backlight
# backlight = digitalio.DigitalInOut(board.D22)
# backlight.switch_to_output()
# backlight.value = True

# while True:
#     # Draw a black filled box to clear the image.
#     draw.rectangle((0, 0, width, height), outline=0, fill=400)

#     #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 
#     draw.rectangle((0, 0, width, height), outline=0, fill=0)
#     clock_text = strftime("%m/%d/%Y %H:%M:%S")
    
#     try:
#         cmd = "hostname -I | cut -d' ' -f1"
#         IP = "IP: " + subprocess.check_output(cmd, shell=True).decode("utf-8").strip()

#         cmd = "curl -s wttr.in/?format=2"
#         WTTR = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()

#         cmd = 'curl -s ils.rate.sx/1USD | cut -c1-6'
#         USD = "$1USD = ₪" + subprocess.check_output(cmd, shell=True).decode("utf-8").strip() + "ILS"

#         cmd = "cat /sys/class/thermal/thermal_zone0/temp | awk '{printf \"CPU Temp: %.1f C\", $(NF-0) / 1000}'"
#         Temp = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    
#     except Exception as e:
#         IP, WTTR, USD, Temp = "ERR", "ERR", "ERR", "ERR"

#     # image drawing code
#     y = top
#     draw.text((x, y), clock_text, font=font, fill="#00FF00")
#     y += draw.textbbox((0, 0), clock_text, font=font)[3]

#     draw.text((x, y), IP, font=font, fill="#FFFFFF")
#     y += draw.textbbox((0, 0), IP, font=font)[3]

#     draw.text((x, y), WTTR, font=font, fill="#FFFF00")
#     y += draw.textbbox((0, 0), WTTR, font=font)[3]

#     draw.text((x, y), USD, font=font, fill="#0000FF")
#     y += draw.textbbox((0, 0), USD, font=font)[3]

#     draw.text((x, y), Temp, font=font, fill="#FF0000")


#     # Display image.
#     disp.image(image, rotation)
#     time.sleep(1)
