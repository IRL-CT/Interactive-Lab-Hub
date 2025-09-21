import time
import datetime
import math
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# ================= Display Setup =================
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

height = disp.width
width = disp.height
rotation = 90

image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
font_car = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)  # bigger text
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True


# ================= Helper Functions =================
def gradient_color(y, h, trips, max_trips=48):
    """Return stronger red gradient based on vertical position"""
    intensity = min(trips / max_trips, 1.0)
    top_red = 180
    bottom_red = 255
    r = int(top_red + (bottom_red - top_red) * (y / h))
    g = int(50 * (1 - y / h))
    b = int(50 * (1 - y / h))
    return (r, g, b)


def rotate_point(x, y, px, py, angle):
    """Rotate a point (x,y) around pivot (px,py) by angle (radians)."""
    dx, dy = x - px, y - py
    x_new = dx * math.cos(angle) - dy * math.sin(angle) + px
    y_new = dx * math.sin(angle) + dy * math.cos(angle) + py
    return x_new, y_new


# ================= Main Loop =================
while True:
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

    # Calculate trips
    now = datetime.datetime.now()
    minutes_since_midnight = now.hour * 60 + now.minute + now.second / 60
    trips_float = minutes_since_midnight / 30

    # Draw gradient background
    for y in range(height):
        color = gradient_color(y, height, trips_float)
        draw.line((0, y, width, y), fill=color)

    # Cable line
    cable_y = height // 4 + 10
    draw.line((0, cable_y, width, cable_y), fill=(0, 100, 255), width=4)

    # Car parameters
    rope_length = 25
    car_w, car_h = 60, 40
    car_y = cable_y + rope_length
    car_x_offset = 60

    seconds_in_day = now.hour * 3600 + now.minute * 60 + now.second
    seconds_in_cycle = seconds_in_day % 1800

    if seconds_in_cycle < 900:
        progress = seconds_in_cycle / 900
        car_x = int(progress * (width - car_x_offset))
    else:
        progress = (seconds_in_cycle - 900) / 900
        car_x = int((1 - progress) * (width - car_x_offset))

    car_color = (135, 206, 250)

    # Pivot point (rope connection)
    pivot_x = car_x + car_w // 2
    pivot_y = cable_y

    # Oscillation angle (±5 degrees)
    angle = math.radians(5) * math.sin(time.time() * 2)

    # Car body (before rotation)
    car_rect = [
        (car_x, car_y),
        (car_x + car_w, car_y),
        (car_x + car_w, car_y + car_h),
        (car_x, car_y + car_h),
    ]

    # Rotate car body
    car_rot = [rotate_point(x, y, pivot_x, pivot_y, angle) for x, y in car_rect]

    # Draw rope
    draw.line((pivot_x, pivot_y, pivot_x, car_y), fill=(0, 100, 255), width=3)

    # Draw car body (rounded effect by polygon approximation)
    draw.polygon(car_rot, fill=car_color)

    # Windows (calculate rotated positions)
    win_margin = 6
    win_w, win_h = 12, 14
    windows = []
    for i in range(2):
        wx = car_x + win_margin + i * (win_w + 14)
        wy = car_y + 10
        rect = [
            (wx, wy),
            (wx + win_w, wy),
            (wx + win_w, wy + win_h),
            (wx, wy + win_h),
        ]
        rect_rot = [rotate_point(x, y, pivot_x, pivot_y, angle) for x, y in rect]
        windows.append(rect_rot)

    for w in windows:
        draw.polygon(w, fill=(200, 230, 250), outline=(255, 255, 255))

    # Text inside car (rotated center)
    trips_text = f"{trips_float:.2f}"
    text_bbox = draw.textbbox((0, 0), trips_text, font=font_car)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    text_cx = (car_rect[0][0] + car_rect[1][0]) / 2
    text_cy = (car_rect[0][1] + car_rect[2][1]) / 2
    text_x = text_cx - text_w / 2
    text_y = text_cy - text_h / 2
    # Rotate text position
    text_xr, text_yr = rotate_point(text_x, text_y, pivot_x, pivot_y, angle)
    draw.text((text_xr, text_yr), trips_text, font=font_car, fill=(0, 0, 0))

    # Labels
    draw.text((5, 5), "Cable round trips", font=font, fill=(255, 255, 255))
    draw.text((5, height - 18), "1 round trip = 30 min", font=font_small, fill=(255, 255, 255))

    # Show image
    disp.image(image, rotation)
    time.sleep(0.05)
