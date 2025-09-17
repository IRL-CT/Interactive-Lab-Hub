import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from time import localtime

# Configuration for CS and DC pins
cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate
BAUDRATE = 64000000

# Setup SPI bus
spi = board.SPI()

# Create the ST7789 display
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

# Create blank image
height = disp.width   # swap to rotate to landscape
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Drawing object
draw = ImageDraw.Draw(image)

# Load fonts
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

while True:
    # Clear screen
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

    # Time info
    minutes_today = localtime().tm_hour * 60 + localtime().tm_min
    seconds_today = minutes_today * 60 + localtime().tm_sec

    # Trips
    trips_float = seconds_today / 1800   # 30min = 1800s
    trips_int = int(trips_float)
    seconds_in_cycle = seconds_today % 1800

    # Display trip counts
    draw.text((10, 10), f"Cable round trips: {trips_int}", font=font_small, fill=(255, 255, 0))
    draw.text((10, height - 30), f"Trips = {trips_float:.2f}", font=font_large, fill=(0, 255, 0))

    # Draw cable line
    cable_y = height // 2
    draw.line((0, cable_y, width, cable_y), fill=(200, 200, 200), width=3)

    # Cable car position (smooth by seconds)
    if seconds_in_cycle < 900:
        # Moving right
        progress = seconds_in_cycle / 900
        car_x = int(progress * (width - 30))
    else:
        # Moving left
        progress = (seconds_in_cycle - 900) / 900
        car_x = int((1 - progress) * (width - 30))

    car_y = cable_y - 15
    draw.rectangle((car_x, car_y, car_x + 30, car_y + 20), fill=(0, 128, 255))  # cable car
    draw.line((car_x + 15, car_y, car_x + 15, cable_y), fill=(255, 255, 255), width=2)  # hanging line

    # Update display
    disp.image(image, rotation)
    time.sleep(1)
