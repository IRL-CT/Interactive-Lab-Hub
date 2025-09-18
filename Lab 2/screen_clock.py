import time
from time import localtime
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# ---------------------------
# Display setup (MiniPiTFT 240x135)
# ---------------------------
cs_pin = digitalio.DigitalInOut(board.D5)      # GPIO5 for CS
dc_pin = digitalio.DigitalInOut(board.D25)     # GPIO25 for DC
reset_pin = None                               # optional

# Backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# SPI bus
spi = board.SPI()

# Create ST7789 display
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=64000000,
    width=135,    # logical width of driver
    height=240,   # logical height of driver
    x_offset=53,
    y_offset=40,
)
rotation = 90


btn_top = digitalio.DigitalInOut(board.D23)
btn_top.switch_to_input(pull=digitalio.Pull.UP)

btn_bottom = digitalio.DigitalInOut(board.D24)
btn_bottom.switch_to_input(pull=digitalio.Pull.UP)

# Image must match the driver’s logical size
WIDTH = disp.width
HEIGHT = disp.height
image = Image.new("RGB", (WIDTH, HEIGHT))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()


def pages_today(total_pages=24):
    t = localtime()
    seconds_today = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
    return int((seconds_today / 86400.0) * total_pages)


page_counter = 0
show_counter = False


def page_turn():
    for offset in range(0, WIDTH // 2, 20):
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))
        mid = WIDTH // 2

        # static right page
        draw.rectangle((mid + 5, 40, WIDTH - 10, 200), outline=(255, 255, 255))
        # animated left page sliding away
        draw.rectangle((10 + offset, 40, mid - 5 + offset, 200), outline=(255, 255, 255))

        disp.image(image, rotation)
        time.sleep(0.05)


while True:
    if not btn_top.value:
        page_counter += 1
        page_turn()

    if not btn_bottom.value:
        show_counter = not show_counter

    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))

    if show_counter:
        draw.text((50, 120), f"Counter: {page_counter}", font=font, fill=(0, 255, 0))
    else:
        total_pages = 24
        current_page = pages_today(total_pages)
        mid = WIDTH // 2

        # Draw book outline
        draw.rectangle((10, 40, mid - 5, 200), outline=(255, 255, 255))
        draw.rectangle((mid + 5, 40, WIDTH - 10, 200), outline=(255, 255, 255))

        # Page numbers
        draw.text((30, 100), f"Page {current_page}", font=font, fill=(255, 255, 0))
        draw.text((mid + 20, 100), f"of {total_pages}", font=font, fill=(0, 255, 255))

        # Progress bar
        progress = current_page / total_pages
        bar_width = int((WIDTH - 20) * progress)
        draw.rectangle((10, 210, 10 + bar_width, 230), fill=(150, 75, 0))

    disp.image(image, rotation)
    time.sleep(0.1)
