import time
from time import localtime
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# --- Display setup ---
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

BAUDRATE = 64000000

disp = st7789.ST7789(
    board.SPI(),
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=240,
    height=240,
    x_offset=0,
    y_offset=80,
)

# Rotation: adjust depending on orientation
rotation = 90

# Get display size
width = disp.width
height = disp.height

# Create blank image for drawing
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)

# Load font
font = ImageFont.load_default()

# --- Helper function ---
def pages_today(total_pages=24):
    """Calculate pages based on time of day"""
    t = localtime()
    seconds_today = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
    return int((seconds_today / 86400.0) * total_pages)

# --- Main loop ---
while True:
    # Clear screen
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

    total_pages = 24  # 1 page per hour
    current_page = pages_today(total_pages)

    # Draw book outline (two facing pages)
    mid = width // 2
    draw.rectangle((10, 40, mid - 5, 200), outline=(255, 255, 255))      # left page
    draw.rectangle((mid + 5, 40, width - 10, 200), outline=(255, 255, 255))  # right page

    # Show page numbers
    draw.text((30, 100), f"Page {current_page}", font=font, fill=(255, 255, 0))
    draw.text((mid + 20, 100), f"of {total_pages}", font=font, fill=(0, 255, 255))

    # Progress bar like "ink" on bottom
    progress = current_page / total_pages
    bar_width = int((width - 20) * progress)
    draw.rectangle((10, 210, 10 + bar_width, 230), fill=(150, 75, 0))  # brown ink

    # Push image to display
    disp.image(image, rotation)

    time.sleep(1)
