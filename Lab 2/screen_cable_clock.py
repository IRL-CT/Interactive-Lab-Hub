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
font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
font_car   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
font_note  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

while True:
    # Current time → seconds from midnight
    lt = localtime()
    seconds_today = lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec

    # Trips calculation
    trips_float = seconds_today / 1800   # 30min = 1800s
    seconds_in_cycle = seconds_today % 1800

    # Background color: interpolate from light red → dark red
    max_trips = 48  # 24h / 0.5h
    ratio = min(trips_float / max_trips, 1.0)
    r = int(255 - (127 * ratio))  # 255 → 128
    g = int(180 - (180 * ratio))  # 180 → 0
    b = int(180 - (180 * ratio))  # 180 → 0
    bg_color = (r, g, b)

    # Fill background
    draw.rectangle((0, 0, width, height), outline=0, fill=bg_color)

    # Draw title
    draw.text((10, 10), "CABLE ROUND TRIPS", font=font_title, fill=(255, 255, 255))

    # Cable line position (move up a bit)
    cable_y = height // 3
    draw.line((0, cable_y, width, cable_y), fill=(0, 100, 255), width=4)

    # Cable car movement (smooth left ↔ right)
    if seconds_in_cycle < 900:
        progress = seconds_in_cycle / 900
        car_x = int(progress * (width - 60))
    else:
        progress = (seconds_in_cycle - 900) / 900
        car_x = int((1 - progress) * (width - 60))

    # Draw hanging line
    rope_length = 35
    draw.line((car_x + 30, cable_y, car_x + 30, cable_y + rope_length), fill=(0, 100, 255), width=3)

    # Car body parameters
    car_w, car_h = 60, 40
    car_y = cable_y + rope_length
    car_color = (135, 206, 250)  # sky blue

    # Draw car roof (triangle/trapezoid)
    roof_height = 10
    draw.polygon(
        [(car_x, car_y), (car_x + car_w, car_y), (car_x + car_w - 10, car_y - roof_height), (car_x + 10, car_y - roof_height)],
        fill=car_color
    )

    # Draw car body (rounded rectangle)
    draw.rounded_rectangle((car_x, car_y, car_x + car_w, car_y + car_h), radius=8, fill=car_color)

    # Write trips inside car (centered)
    trips_text = f"{trips_float:.2f}"
    text_bbox = draw.textbbox((0, 0), trips_text, font=font_car)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    text_x = car_x + (car_w - text_w) // 2
    text_y = car_y + (car_h - text_h) // 2
    draw.text((text_x, text_y), trips_text, font=font_car, fill=(255, 255, 255))

    # Note at bottom-left
    note_text = "1 round trip = 30 min"
    draw.text((10, height - 20), note_text, font=font_note, fill=(255, 255, 255))

    # Update display
    disp.image(image, rotation)
    time.sleep(1)
