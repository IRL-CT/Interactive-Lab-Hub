import time
import datetime
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

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
font_car = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# ================= Helper Functions =================
def gradient_colors(trips, max_trips=48):
    """Compute top and bottom colors for gradient background"""
    intensity = min(trips / max_trips, 1.0)

    r_top = int(200 + 55 * intensity)
    g_top = int(80 * (1 - intensity))
    b_top = int(80 * (1 - intensity))

    r_bottom = int(128 + 127 * intensity)
    g_bottom = int(40 * (1 - intensity))
    b_bottom = int(40 * (1 - intensity))

    return (r_top, g_top, b_top), (r_bottom, g_bottom, b_bottom)


def draw_vertical_gradient(draw, width, height, top_color, bottom_color):
    """Draw vertical gradient background"""
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line((0, y, width, y), fill=(r, g, b))


# ================= Main Loop =================
while True:
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

    # Time and trip calculation
    now = datetime.datetime.now()
    minutes_since_midnight = now.hour * 60 + now.minute + now.second / 60
    trips_float = minutes_since_midnight / 30  

    # Dynamic gradient background
    top_color, bottom_color = gradient_colors(trips_float)
    draw_vertical_gradient(draw, width, height, top_color, bottom_color)

    # ================= Draw Cable Car =================
    cable_y = height // 4 + 10
    draw.line((0, cable_y, width, cable_y), fill=(0, 100, 255), width=4)

    rope_length = 20
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

    car_color = (135, 206, 250)  # Sky blue
    shadow_color = (50, 80, 120)  # Dark blue shadow

    # Rope
    draw.line((car_x + car_w//2, cable_y, car_x + car_w//2, car_y), fill=(0, 100, 255), width=3)

    # Roof shadow
    roof_height = 10
    draw.polygon(
        [(car_x+3, car_y+3), (car_x + car_w+3, car_y+3),
         (car_x + car_w - 7, car_y - roof_height+3), (car_x + 13, car_y - roof_height+3)],
        fill=shadow_color
    )
    # Roof
    draw.polygon(
        [(car_x, car_y), (car_x + car_w, car_y),
         (car_x + car_w - 10, car_y - roof_height), (car_x + 10, car_y - roof_height)],
        fill=car_color
    )

    # Car shadow
    draw.rounded_rectangle((car_x+3, car_y+3, car_x + car_w+3, car_y + car_h+3), radius=8, fill=shadow_color)
    # Car body
    draw.rounded_rectangle((car_x, car_y, car_x + car_w, car_y + car_h), radius=8, fill=car_color)

    # Windows with highlight
    win_margin = 6
    win_w, win_h = 12, 14
    for i in range(2):
        wx = car_x + win_margin + i*(win_w + 14)
        wy = car_y + 10
        draw.rounded_rectangle(
            (wx, wy, wx+win_w, wy+win_h),
            radius=4,
            fill=(200, 230, 250),
            outline=(255, 255, 255)
        )
        draw.line((wx+2, wy+2, wx+win_w-2, wy+6), fill=(255, 255, 255), width=2)

    # Trip count inside car
    trips_text = f"{trips_float:.2f}"
    text_bbox = draw.textbbox((0, 0), trips_text, font=font_car)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    text_x = car_x + (car_w - text_w) // 2
    text_y = car_y + (car_h - text_h) // 2

    draw.rectangle((text_x-2, text_y-2, text_x+text_w+2, text_y+text_h+2), fill=(0, 0, 0))
    draw.text((text_x, text_y), trips_text, font=font_car, fill=(255, 255, 255))

    # ================= Labels =================
    draw.text((5, 5), "Cable round trips", font=font_title, fill=(255, 255, 255))
    draw.text((5, height-18), "1 round trip = 30 min", font=font_small, fill=(255, 255, 255))

    # Update display
    disp.image(image, rotation)
    time.sleep(1)
