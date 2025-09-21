from datetime import datetime
import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import busio

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
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

# Setup I2C for button - Direct I2C approach
i2c = busio.I2C(board.SCL, board.SDA)
button_available = False

# Check if button device is available
while not i2c.try_lock():
    pass
try:
    devices = i2c.scan()
    if 0x6f in devices:
        button_available = True
        print("Button connected successfully at 0x6f!")
    else:
        print("No button found, running without button control")
except:
    print("I2C scan failed, running without button control")
finally:
    i2c.unlock()

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
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Color and timer control variables
timer_mode = False
timer_start_time = None
timer_duration = 5 * 60  # 5 minutes in seconds
last_button_state = False

def read_button_state():
    """Read button state directly from I2C device"""
    if not button_available:
        return False
    
    try:
        while not i2c.try_lock():
            pass
        
        # Read from button device
        result = bytearray(4)
        i2c.readfrom_into(0x6f, result)
        
        # Button state is in the 4th byte, bit 2 (0x04)
        # 0x03 = not pressed, 0x07 = pressed
        button_pressed = bool(result[3] & 0x04)
        return button_pressed
        
    except Exception as e:
        print(f"Button read error: {e}")
        return False
    finally:
        try:
            i2c.unlock()
        except:
            pass

def draw_hourglass(x, y_top, w, h, ratio, color=(200,200,0)):
    """
    Draw hourglass.
    x, y_top: top-left corner point and top boundary
    w, h: Width and height
    ratio: fallen sand (0–1)
    """
   
    # Draw an hourglass
    top_triangle = [(x, y_top), (x+w, y_top), (x+w//2, y_top+h//2)]
    bottom_triangle = [(x, y_top+h), (x+w, y_top+h), (x+w//2, y_top+h//2)]
    draw.polygon(top_triangle, outline=(255,255,255))
    draw.polygon(bottom_triangle, outline=(255,255,255))

    # Top sand
    remain = 1 - ratio
    Ax, Ay = x, y_top
    Bx, By = x+w, y_top
    Cx, Cy = x+w//2, y_top+h//2

    pA = (int(Cx + (Ax - Cx) * remain), int(Cy + (Ay - Cy) * remain))
    pB = (int(Cx + (Bx - Cx) * remain), int(Cy + (By - Cy) * remain))

    if remain > 0:
        draw.polygon([pA, pB, (Cx, Cy)], fill=color)

    # Bottom sand
    bottom_fill = int(ratio * (h//2))
    bottom_sand = [(x, y_top+h), (x+w, y_top+h), (x+w//2, y_top+h-bottom_fill)]
    draw.polygon(bottom_sand, fill=color)

    # Middle sand
    mid_x = x + w//2
    mid_y = y_top + h//2
    bottom_y = y_top + h
    draw.line((mid_x, mid_y, mid_x, bottom_y), fill=color)

while True:
    # Check button state if available
    if button_available:
        current_button_state = read_button_state()
        
        # Detect button press (rising edge)
        if current_button_state and not last_button_state:
            if not timer_mode:
                # Start 5-minute timer
                timer_mode = True
                timer_start_time = time.time()
                print("5-minute timer started!")
            else:
                # Stop timer and return to normal clock
                timer_mode = False
                timer_start_time = None
                print("Timer stopped, back to normal clock")
        
        last_button_state = current_button_state
    
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

    if timer_mode and timer_start_time:
        # Timer mode - 5 minute countdown
        elapsed_time = time.time() - timer_start_time
        remaining_time = max(0, timer_duration - elapsed_time)
        
        if remaining_time <= 0:
            # Timer finished
            timer_mode = False
            timer_start_time = None
            print("Timer finished!")
        
        # Calculate timer display
        minutes_left = int(remaining_time // 60)
        seconds_left = int(remaining_time % 60)
        
        margin = 10
        
        # Two hourglass layout for minutes and seconds
        min_x = margin
        sec_x = width//2 + margin//2
        sand_width = width//2 - margin
        sand_height = height - 2*margin
        
        # Red colors for timer mode
        min_timer_color = (255, 80, 80)    # Bright red for minutes
        sec_timer_color = (255, 120, 120)  # Slightly lighter red for seconds
        
        # Calculate ratios for each hourglass
        # Minutes: show progress within current minute (0-4 minutes range)
        if timer_duration >= 60:
            min_total = timer_duration // 60  # Total minutes (5)
            min_elapsed = (timer_duration - remaining_time) // 60  # Minutes passed
            min_ratio = min_elapsed / min_total if min_total > 0 else 0
        else:
            min_ratio = 0
        
        # Seconds: show progress within current minute (0-59 seconds)
        sec_ratio = (60 - seconds_left) / 60
        
        # Draw two hourglasses for minutes and seconds
        draw_hourglass(min_x, margin, sand_width, sand_height, min_ratio, min_timer_color)
        draw_hourglass(sec_x, margin, sand_width, sand_height, sec_ratio, sec_timer_color)
        
        # Add labels below each hourglass
        label_y = height - margin + 5
        draw.text((min_x + sand_width//4, label_y), "MIN", font=font, fill=(255, 255, 255))
        draw.text((sec_x + sand_width//4, label_y), "SEC", font=font, fill=(255, 255, 255))
        
        # Display remaining time as text in center
        time_text = f"{minutes_left:02d}:{seconds_left:02d}"
        try:
            bbox = draw.textbbox((0, 0), time_text, font=font)
            text_width = bbox[2] - bbox[0]
        except AttributeError:
            text_width, _ = draw.textsize(time_text, font=font)
        
        text_x = (width - text_width) // 2
        text_y = height // 2 + 20
        draw.text((text_x, text_y), time_text, font=font, fill=(255, 255, 255))
        
    else:
        # Normal clock mode
        now = datetime.now()
        hour = now.hour % 12
        minute = now.minute
        second = now.second

        margin = 10
        hour_x = margin
        min_x  = width//3 + margin
        sec_x  = 2*width//3 - margin
        sand_width = width//3 - 2*margin
        sand_height = height - 2*margin

        # Normal yellow colors for clock mode
        hour_color = (200, 200, 0)      # Yellow
        min_color = (200, 180, 0)       # Yellow-orange
        sec_color = (220, 160, 0)       # Orange

        # Draw hourglass for hour, min, and sec
        draw_hourglass(hour_x, margin, sand_width, sand_height, hour/12, hour_color)
        draw_hourglass(min_x,  margin, sand_width, sand_height, minute/60, min_color)
        draw_hourglass(sec_x,  margin, sand_width, sand_height, second/60, sec_color)

    # Display image.
    disp.image(image, rotation)
    time.sleep(0.1)  # Faster refresh for button responsiveness
