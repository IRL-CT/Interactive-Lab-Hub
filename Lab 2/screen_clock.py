import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import requests

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

def wrap_text(text, font, max_width):
    lines = []
    if not text:
        return lines
    words = text.split(' ')
    current_line = ""
    for word in words:
        if len(current_line + word + " ") < 27:
            if current_line:
                current_line += " "
            current_line += word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

# --- Pomodoro config ---
WORK_MINUTES = 25
BREAK_MINUTES = 5

session_type = "work"   # "work" or "break"
session_length = WORK_MINUTES * 60
start_time = time.time()

while True:
    # Clear screen
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

    # Time tracking
    elapsed = int(time.time() - start_time)
    if elapsed > session_length:
        # Switch session
        if session_type == "work":
            session_type = "break"
            session_length = BREAK_MINUTES * 60
        else:
            session_type = "work"
            session_length = WORK_MINUTES * 60
        start_time = time.time()
        elapsed = 0

    remaining = session_length - elapsed
    progress = elapsed / session_length
    bar_width = int(progress * width)

    # Progress bar background
    bar_height = 20
    bar_y = height - bar_height - 5
    draw.rectangle((0, bar_y, width, bar_y + bar_height), outline=0, fill=(50, 50, 50))

    # Bar color depends on session
    bar_color = (0, 200, 0) if session_type == "work" else (0, 120, 255)
    draw.rectangle((0, bar_y, bar_width, bar_y + bar_height), outline=0, fill=bar_color)

    # Session label and timer
    minutes = remaining // 60
    seconds = remaining % 60
    timer_text = f"{minutes:02}:{seconds:02}"
    draw.text((5, 5), f"{session_type.capitalize()} - {timer_text}", font=font, fill="#FFFF00")

    # Fetch affirmation (only once per session)
    if elapsed == 0:
        try:
            response = requests.get("https://www.affirmations.dev/")
            if response.status_code == 200:
                data = response.json()
                affirmation = data["affirmation"]
            else:
                affirmation = "Error fetching affirmation."
        except requests.exceptions.RequestException:
            affirmation = "Network error."

    # Wrap and draw the affirmation text
    wrapped_lines = wrap_text(affirmation, font, width)
    line_y = 30
    for line in wrapped_lines:
        draw.text((5, line_y), line, font=font, fill="#FFFFFF")
        line_y += 25  

    # Push to display
    disp.image(image, rotation)
    time.sleep(1)
