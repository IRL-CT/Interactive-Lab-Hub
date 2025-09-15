from time import localtime, sleep
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# --- Display setup ---
cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

BAUDRATE = 64000000
spi = board.SPI()

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

# Rotate so it's landscape
height = disp.width
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# Backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True


def pages_today(total_pages=24):
    """Convert time of day -> current page"""
    t = localtime()
    seconds_today = t.tm_hour*3600 + t.tm_min*60 + t.tm_sec
    return int((seconds_today / 86400.0) * total_pages)


while True:
    draw.rectangle((0,0,width,height), fill=0)  # clear screen

    total_pages = 24  # 1 page per hour
    current_page = pages_today(total_pages)

    # book outline (two facing pages)
    mid = width // 2
    draw.rectangle((10,40, mid-5, 200), outline=(255,255,255))   # left page
    draw.rectangle((mid+5,40, width-10, 200), outline=(255,255,255))  # right page

    # page numbers
    draw.text((30, 100), f"Page {current_page}", font=font, fill=(255,255,0))
    draw.text((mid+20, 100), f"of {total_pages}", font=font, fill=(0,255,255))

    stack_height = 8   # pixels per book
    spacing = 2        # space between books
    book_width = width - 40
    left = 20
    bottom = height - 20

    for i in range(current_page):
        top = bottom - (i+1)*(stack_height+spacing)

        # change book colors 
        color = (150, 75, 0) if i % 2 == 0 else (200, 150, 100)

        # book
        draw.rectangle(
            (left, top, left+book_width, top+stack_height),
            fill=color,
            outline=(255, 255, 255)
        )

        # book spine line
        draw.line((left, top+stack_height//2, left+book_width, top+stack_height//2),
                  fill=(50, 50, 50))

    disp.image(image, rotation)
    sleep(1)
