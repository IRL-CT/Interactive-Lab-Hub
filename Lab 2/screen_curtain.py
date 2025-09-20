import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageOps, ImageFont
import adafruit_rgb_display.st7789 as st7789
from datetime import datetime, timedelta


# ===== Display setup =====
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

# Rotate display to landscape
height = disp.width
width  = disp.height
rotation = 90

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)

# Backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# ===== Load images =====
bg = Image.open("image/lionking-blue.jpg").convert("RGB")
curtain = Image.open("image/curtain.jpg").convert("RGBA")

# Fit images to screen
bg = ImageOps.fit(bg, (width, height), method=Image.Resampling.LANCZOS)
curtain = ImageOps.fit(curtain, (width, height), method=Image.Resampling.LANCZOS)

# ===== Draw partial curtain =====

def curtain_mask(fraction_closed):
    """Return a mask image for the curtain, where fraction_closed is between
    0.0 (fully open) and 1.0 (fully closed)."""
    drop_px = int(curtain.height * fraction_closed)
    mask = Image.new("L", curtain.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((0, 0, curtain.width, drop_px), fill=255)
    return mask

state = None
target = None
flash = False

lottery_open = 9
lottery_close = 15
performance_time = 20
performance_duration = 2

while True: 
    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 
    now = datetime.now()
    # Target time (9:00 AM today) for the lottery to be opened next
    if now.hour < lottery_open or now.hour >= performance_time + performance_duration:
        state = "waiting_lottery"
        target = now.replace(hour=lottery_open, minute=0, second=0, microsecond=0)
    # if it's past 9 AM but before 3pm, set target to 3 PM today
    if now.hour < lottery_close and now.hour >= lottery_open: 
        state = "lottery_open"
        target = now.replace(hour=lottery_close, minute=0, second=0, microsecond=0)
    # if it's past 3pm, set target to 9 AM tomorrow
    if now.hour >= lottery_close and now.hour < performance_time: 
        state = "waiting_performance"
        target = now.replace(hour=performance_time, minute=0, second=0, microsecond=0)
    if now.hour >= performance_time and now.hour < (performance_time+performance_duration):
        state = "performance_time"
        target = now.replace(hour= (performance_time + performance_duration), minute=0, second=0, microsecond=0)

    # Calculate remaining time
    remaining = target - now

    # Break it into hours/minutes/seconds
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format nicely
    waiting_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Draw it on your canvas
    # draw.text((15, top), day_name, font=font, fill=(255, 255, 255))
    match state: 
        case "waiting_lottery":
            image.paste(curtain, (0,0))
            draw.text((10, top+5), "Lottery Opens in...", font=font, fill=(255, 255, 255))
            draw.text((40, top + 30), waiting_time, font=font2, fill=(255, 255, 255))
        case "lottery_open":
            image.paste(curtain, (0,0))
            flash = not flash
            draw.text((40, top+5), "Lottery Closes In...", font=font, fill=(255, 255, 255))
            if flash:
                draw.text((40,  top + 30), waiting_time, font=font2, fill=(255, 255, 255))
        case "waiting_performance":
            fraction = remaining.total_seconds() / ((performance_time - lottery_close)*3600)
            mask = curtain_mask(fraction)
            # print(remaining.total_seconds() / (6*3600))
            image = bg.copy()
            image.paste(curtain, (0,0), mask)   
            draw = ImageDraw.Draw(image) 
            draw.text((20, top+5), "SHOW TIME IN...", font=font, fill=(255, 255, 255))
            draw.text((40, top + 30), waiting_time, font=font2, fill=(255, 255, 255))
        case "performance_time":
            image.paste(bg, (0,0))
    
    # Display image.
    disp.image(image, rotation)
    time.sleep(1)
