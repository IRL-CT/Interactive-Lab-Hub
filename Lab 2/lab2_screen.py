import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from textwrap import wrap

# -----------------------
# Display Configuration
# -----------------------
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

# Buttons
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# Fonts
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 25)

# -----------------------
# Activities
# -----------------------
activities = {
    "massage": 30,
    "face mask": 20,
    "foot bath": 15,
    "manicure": 8,
    "meditation": 5,
    "yoga": 15,
    "offline": 1,
}

activity_list = list(activities.keys())

# -----------------------
# Helper Functions
# -----------------------

def draw_wrapped_text(draw, text, font, max_width, start_y, line_spacing=2, fill="black"):
    """
    Draw text with wrapping so it doesn't go off screen.
    Returns the y position after the last line.
    """
    # figure out max characters per line by trial with 'M' (wide char)
    avg_char_width = font.getlength("M")
    max_chars = max_width // int(avg_char_width)  

    # split text into lines
    lines = wrap(text, width=max_chars)

    y = start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = (width - tw) // 2
        draw.text((tx, y), line, font=font, fill=fill)
        y += bbox[3] - bbox[1] + line_spacing
    return y

def center_text(draw, text, font, y, fill="black"):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (width - tw) // 2
    draw.text((tx, y), text, font=font, fill=fill)
    return th

def show_welcome():
    canvas = Image.new("RGB", (width, height), "#BFBCBB")
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 35), "welcome! Ready to", font=font, fill="black")
    draw.text((30, 55), "take care of yourself?", font=font, fill="#fc6203")
    disp.image(canvas, rotation)

def show_reward():
    canvas = Image.new("RGB", (width, height), "#BFBCBB")
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 35), "Congrats! Remember to", font=font, fill="black")
    draw.text((30, 55), "love yourself!", font=font, fill="#fc6203")
    disp.image(canvas, rotation)

def show_menu(selected_idx):
    canvas = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(canvas)
    y = 10
    for i, name in enumerate(activity_list):
        fill = "#fc6203" if i == selected_idx else "black"
        draw.text((10, y), name, font=font_small, fill=fill)
        y += 16
    disp.image(canvas, rotation)

def display_activity(activity_name):
    canvas = Image.new("RGB", (width, height), "#BFBCBB")
    draw = ImageDraw.Draw(canvas)

    # Load image and scale to 40% height
    try:
        image_path = f"resources/{activity_name}.png"
        image = Image.open(image_path).convert("RGBA")
        img_max_height = int(height * 0.5)
        img_max_width = int(width * 0.9)
        image.thumbnail((img_max_width, img_max_height), Image.Resampling.LANCZOS)

        x = (width - image.width) // 2
        y = 0
        canvas.paste(image, (x, y), image)
        image_bottom = y + image.height
    except Exception as e:
        print("No image:", e)
        image_bottom = 0

    activity_txt = f"{activity_name} time!"
    draw.text((15, 55), activity_txt, font=font_small, fill="black")

    instruction_txt = f"A: pause/resume B: exit"
    draw.text((15, 75), instruction_txt, font=font_small, fill="black")

    disp.image(canvas, rotation)
    return canvas

def countdown(total_seconds, canvas, ty):
    while total_seconds >= 0:
        screen = canvas.copy()
        draw = ImageDraw.Draw(screen)

        mins, secs = divmod(total_seconds, 60)
        timer_text = f"{mins:02d}:{secs:02d}"
        print(timer_text)
        draw.text((55, 100), timer_text, font=font_large, fill="black")

        disp.image(screen, rotation)

        if not buttonB.value:
            print("exit")
            return False  # exit

        # Pause if A is pressed
        if not buttonA.value:
            print("pause")
            # wait until A is released before locking pause mode
            while not buttonA.value:
                time.sleep(0.1)

            # Pause loop
            while True:
                time.sleep(0.2)

                if not buttonA.value:  # pressed again = resume
                    print("resume")
                    # wait until released to avoid double-trigger
                    while not buttonA.value:
                        time.sleep(0.1)
                    break

                if not buttonB.value:  # exit while paused
                    return False

        time.sleep(1)
        total_seconds -= 1
    # return true if completed the activity
    return True


while True:
    # frame 1: Welcome
    press_start = False
    while not press_start:
        show_welcome()
        if not buttonA.value or not buttonB.value:
            press_start = True

    # frame 2: Menu
    selected_idx = 0
    while True:
        show_menu(selected_idx)
        time.sleep(0.2)

        if not buttonA.value and not buttonB.value:  # both = select
            
            activity = activity_list[selected_idx]
            minutes = activities[activity]
            
            print("select " + activity)
            # frame 3: Activity screen
            canvas = display_activity(activity)

            # frame 4: countdown
            success = countdown(minutes * 60, canvas, 75)

            if success:
                # frame 5: Reward screen
                show_reward()
            break
        elif not buttonA.value:  # up
            selected_idx = (selected_idx - 1) % len(activity_list)
            print("up")
        elif not buttonB.value:  # down
            selected_idx = (selected_idx + 1) % len(activity_list)
            print("down")
        
