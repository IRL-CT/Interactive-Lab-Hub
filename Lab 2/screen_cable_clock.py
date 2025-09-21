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
font_car = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)  # bigger font for car
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# ================= Helper Functions =================
def gradient_colors(trips, t, max_trips=48):
    """Dynamic gradient background"""
    intensity = min(trips / max_trips, 1.0)
    wave = (math.sin(t / 5) + 1) / 2

    r_top = int(180 + 50 * intensity + 30 * wave)
    g_top = int(50 * (1 - intensity) + 40 * wave)
    b_top = int(120 + 40 * wave)

    r_bottom = int(120 + 100 * intensity + 40 * wave)
    g_bottom = int(30 * (1 - intensity) + 20 * wave)
    b_bottom = int(60 + 50 * wave)
    return (r_top, g_top, b_top), (r_bottom, g_bottom, b_bottom)


def draw_vertical_gradient(draw, width, height, top_color, bottom_color):
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line((0, y, width, y), fill=(r, g, b))


def rotate_point(x, y, cx, cy, angle):
    """Rotate (x,y) around center (cx,cy) by angle (radians)"""
    dx, dy = x - cx, y - cy
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    rx = cx + dx * cos_a - dy * sin_a
    ry = cy + dx * sin_a + dy * cos_a
    return rx, ry


def draw_shadow(base_img, car_poly, blur_radius=6, offset=5):
    """Soft shadow under car"""
    shadow = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)

    shadow_poly = [(x+offset, y+offset) for (x,y) in car_poly]
    shadow_draw.polygon(shadow_poly, fill=(0, 0, 0, 120))

    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    base_img.paste(shadow, (0, 0), shadow)


# ================= Main Loop =================
while True:
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

    now = datetime.datetime.now()
    t = time.time()
    minutes_since_midnight = now.hour * 60 + now.minute + now.second / 60
    trips_float = minutes_since_midnight / 30  

    # Background
    top_color, bottom_color = gradient_colors(trips_float, t)
    draw_vertical_gradient(draw, width, height, top_color, bottom_color)

    # ================= Cable =================
    cable_y = height // 4 + 10
    draw.line((0, cable_y, width, cable_y), fill=(0, 100, 255), width=4)

    rope_length = 20
    car_w, car_h = 60, 40
    car_y = cable_y + rope_length
    car_x_offset = 60

    # Horizontal motion (back & forth every 30 min)
    seconds_in_day = now.hour * 3600 + now.minute * 60 + now.second
    seconds_in_cycle = seconds_in_day % 1800
    if seconds_in_cycle < 900:  
        progress = seconds_in_cycle / 900
        car_x = int(progress * (width - car_x_offset))
    else:  
        progress = (seconds_in_cycle - 900) / 900
        car_x = int((1 - progress) * (width - car_x_offset))

    # ===== Pendulum sway angle =====
    sway_angle = 0.1 * math.sin(t * 2)  # ±0.1 rad ≈ ±6°

    pivot_x = car_x + car_w // 2
    pivot_y = cable_y

    # Define car polygon (roof + body)
    roof_h = 10
    car_poly = [
        (car_x, car_y),
        (car_x + car_w, car_y),
        (car_x + car_w - 10, car_y - roof_h),
        (car_x + 10, car_y - roof_h),
        (car_x, car_y),  # back to left-bottom roof
        (car_x, car_y + car_h),
        (car_x + car_w, car_y + car_h),
        (car_x + car_w, car_y),
    ]
    car_poly = [rotate_point(x, y, pivot_x, pivot_y, sway_angle) for (x,y) in car_poly]

    # Shadow
    draw_shadow(image, car_poly)

    # Draw car
    draw.polygon(car_poly[:4], fill=(135,206,250))  # roof
    draw.polygon(car_poly[3:] + [car_poly[0]], fill=(135,206,250))  # body

    # Windows (just approximate, simpler)
    for i in range(2):
        wx = car_x + 12 + i*24
        wy = car_y + 12
        box = [(wx, wy), (wx+12, wy+14)]
        box = [rotate_point(x, y, pivot_x, pivot_y, sway_angle) for (x,y) in box]
        draw.rectangle(box, fill=(200,230,250), outline=(255,255,255))

    # Rope line
    draw.line((pivot_x, pivot_y, *rotate_point(pivot_x, car_y, pivot_x, pivot_y, sway_angle)),
              fill=(0,100,255), width=3)

    # Text inside car (rotate together with car)
    trips_text = f"{trips_float:.2f}"
    text_w, text_h = draw.textsize(trips_text, font=font_car)
    text_x, text_y = rotate_point(car_x + car_w//2, car_y + car_h//2, pivot_x, pivot_y, sway_angle)
    draw.text((text_x - text_w//2, text_y - text_h//2), trips_text, font=font_car, fill=(0,0,0))

    # Labels
    draw.text((5, 5), "Cable round trips", font=font_title, fill=(255,255,255))
    draw.text((5, height-18), "1 round trip = 30 min", font=font_small, fill=(255,255,255))

    # Update
    disp.image(image, rotation)
    time.sleep(0.05)
