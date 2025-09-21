import time
import datetime
import digitalio
import board
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
font_car = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)  # slightly bigger font
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# ================= Helper Functions =================
def gradient_colors(trips, t, max_trips=48):
    """Compute top and bottom colors for gradient background, with dynamic wave"""
    intensity = min(trips / max_trips, 1.0)
    wave = (math.sin(t / 5) + 1) / 2  # oscillates between 0 and 1 every ~10s

    r_top = int(200 + 40 * intensity + 30 * wave)
    g_top = int(40 * (1 - intensity) + 30 * wave)
    b_top = int(100 + 40 * wave)

    r_bottom = int(100 + 120 * intensity + 40 * wave)
    g_bottom = int(20 * (1 - intensity) + 20 * wave)
    b_bottom = int(40 + 60 * wave)
    return (r_top, g_top, b_top), (r_bottom, g_bottom, b_bottom)


def draw_vertical_gradient(draw, width, height, top_color, bottom_color):
    """Draw vertical gradient background"""
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line((0, y, width, y), fill=(r, g, b))


def draw_shadow(base_img, car_x, car_y, car_w, car_h, roof_height, blur_radius=8, offset=6):
    """Draw soft shadow under cable car"""
    shadow = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)

    shadow_draw.polygon(
        [(car_x+offset, car_y+offset),
         (car_x+car_w+offset, car_y+offset),
         (car_x+car_w-10+offset, car_y-roof_height+offset),
         (car_x+10+offset, car_y-roof_height+offset)],
        fill=(0, 0, 0, 120)
    )

    shadow_draw.rounded_rectangle(
        (car_x+offset, car_y+offset, car_x+car_w+offset, car_y+car_h+offset),
        radius=8,
        fill=(0, 0, 0, 120)
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    base_img.paste(shadow, (0, 0), shadow)


def rotate_point(x, y, cx, cy, angle):
    """Rotate point (x,y) around (cx,cy) by angle (radians)"""
    s, c = math.sin(angle), math.cos(angle)
    x -= cx
    y -= cy
    x_new = x * c - y * s
    y_new = x * s + y * c
    return x_new + cx, y_new + cy

# ================= Main Loop =================
while True:
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

    now = datetime.datetime.now()
    t = time.time()
    minutes_since_midnight = now.hour * 60 + now.minute + now.second / 60
    trips_float = minutes_since_midnight / 30

    # Dynamic gradient background
    top_color, bottom_color = gradient_colors(trips_float, t)
    draw_vertical_gradient(draw, width, height, top_color, bottom_color)

    # ================= Draw Cable Car =================
    cable_y = height // 4 + 10
    draw.line((0, cable_y, width, cable_y), fill=(0, 100, 255), width=4)

    rope_length = 25
    car_w, car_h = 60, 40
    car_y = cable_y + rope_length
    car_x_offset = 60

    # Car moves back and forth every 30 minutes
    seconds_in_day = now.hour * 3600 + now.minute * 60 + now.second
    seconds_in_cycle = seconds_in_day % 1800
    if seconds_in_cycle < 900:
        progress = seconds_in_cycle / 900
        car_x = int(progress * (width - car_x_offset))
    else:
        progress = (seconds_in_cycle - 900) / 900
        car_x = int((1 - progress) * (width - car_x_offset))

    # Sway angle for pendulum effect
    sway_angle = math.sin(t * 2) * math.radians(5)  # ±5 degrees sway
    pivot_x = car_x + car_w // 2
    pivot_y = cable_y

    car_color = (135, 206, 250)

    # Rope with sway
    rope_end_x, rope_end_y = rotate_point(pivot_x, car_y, pivot_x, pivot_y, sway_angle)
    draw.line((pivot_x, pivot_y, rope_end_x, rope_end_y), fill=(0, 100, 255), width=3)

    # Shadow
    draw_shadow(image, int(rope_end_x - car_w/2), int(rope_end_y), car_w, car_h, roof_height=10)

    # Roof
    roof_height = 10
    roof_coords = [
        (rope_end_x - car_w/2, rope_end_y),
        (rope_end_x + car_w/2, rope_end_y),
        (rope_end_x + car_w/2 - 10, rope_end_y - roof_height),
        (rope_end_x - car_w/2 + 10, rope_end_y - roof_height),
    ]
    rotated_roof = [rotate_point(x, y, pivot_x, pivot_y, sway_angle) for x, y in roof_coords]
    draw.polygon(rotated_roof, fill=car_color)

    # Car body
    car_body_coords = (rope_end_x - car_w/2, rope_end_y, rope_end_x + car_w/2, rope_end_y + car_h)
    x0, y0 = rotate_point(car_body_coords[0], car_body_coords[1], pivot_x, pivot_y, sway_angle)
    x1, y1 = rotate_point(car_body_coords[2], car_body_coords[3], pivot_x, pivot_y, sway_angle)
    draw.rounded_rectangle((x0, y0, x1, y1), radius=8, fill=car_color)

    # Windows
    win_margin = 6
    win_w, win_h = 12, 14
    for i in range(2):
        wx = rope_end_x - car_w/2 + win_margin + i*(win_w + 14)
        wy = rope_end_y + 10
        wx0, wy0 = rotate_point(wx, wy, pivot_x, pivot_y, sway_angle)
        wx1, wy1 = rotate_point(wx+win_w, wy+win_h, pivot_x, pivot_y, sway_angle)
        draw.rounded_rectangle((wx0, wy0, wx1, wy1), radius=4, fill=(200,230,250), outline=(255,255,255))
        draw.line((wx0+2, wy0+2, wx1-2, wy0+6), fill=(255,255,255), width=2)

    # Trip count inside car (centered text, rotated with car)
    trips_text = f"{trips_float:.2f}"
    text_bbox = draw.textbbox((0, 0), trips_text, font=font_car)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    text_x, text_y = rotate_point(rope_end_x, rope_end_y + car_h//2, pivot_x, pivot_y, sway_angle)
    draw.text((text_x - text_w//2, text_y - text_h//2 - 2), trips_text, font=font_car, fill=(0,0,0))

    # ================= Labels =================
    draw.text((5, 5), "Cable round trips", font=font_title, fill=(255, 255, 255))
    draw.text((5, height-18), "1 round trip = 30 min", font=font_small, fill=(255, 255, 255))

    # Update display
    disp.image(image, rotation)
    time.sleep(0.05)
