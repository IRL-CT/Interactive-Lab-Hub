import time
import subprocess
import digitalio
import board
from time import strftime
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# Configuration for CS and DC pins
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

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

# Display dimensions
height = disp.width
width = disp.height
rotation = 90

# Create image
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)

# Clear screen
draw.rectangle((0, 0, width, height), fill=0)
disp.image(image, rotation)

# Font
font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    18
)

# Turn on backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True


# --------------------------------
# Load and prepare red.jpg
# --------------------------------

image = Image.open("red.jpg").convert("RGB")

# Resize image to fit the display
image_ratio = image.width / image.height
screen_ratio = width / height

if screen_ratio < image_ratio:
    scaled_width = image.width * height // image.height
    scaled_height = height
else:
    scaled_width = width
    scaled_height = image.height * width // image.width

image = image.resize(
    (scaled_width, scaled_height),
    Image.BICUBIC
)

# Crop and center
x = scaled_width // 2 - width // 2
y = scaled_height // 2 - height // 2

image = image.crop(
    (x, y, x + width, y + height)
)

# --------------------------------
# Main loop
# --------------------------------

while True:

    current_time = strftime("%H:%M:%S")

    # --------------------------------
    # 6:26:00 PM - 6:26:30 PM
    # Show red.jpg
    # --------------------------------

    if "18:26:00" <= current_time <= "18:26:30":

        disp.image(image, rotation)


    # --------------------------------
    # 6:26:31 PM - 6:26:59 PM
    # Show red.jpg + text
    # --------------------------------

    elif "18:26:31:" <= current_time <= "18:26:59":

        # Make a copy so we don't permanently
        # draw the text onto the original image
        display_image = image.copy()

        display_draw = ImageDraw.Draw(display_image)

        display_draw.text(
            (10, 10),
            "YOUR TEXT HERE",
            font=font,
            fill="black"
        )

        disp.image(display_image, rotation)


    # --------------------------------
    # Outside those times
    # --------------------------------

    else:

        # Black screen
        black = Image.new(
            "RGB",
            (width, height),
            (0, 0, 0)
        )

        disp.image(black, rotation)

    time.sleep(1)
