import time
import random
import json
import os
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

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

# Log of past sessions, used to compare today's totals against the previous run
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "distance_clock_log.json")

# 1 second -> 1 step; km rolls over every 1400 steps; marathons roll over every 42 km
STEPS_PER_KM = 1400
KM_PER_MARATHON = 42
MESSAGE_DURATION = 3  # seconds to keep a milestone message on screen
RUN_DURATION_LIMIT = 24 * 60 * 60  # auto-stop after 24 real hours
start_time = time.time()
prev_total_km = 0
prev_marathons = 0
message = ""
message_until = 0
last_km_time = start_time
prev_km_duration = None

KM_MESSAGES = [
    "Km reached!",
    "Nice pace!",
    "Keep going!",
    "One more km down!",
    "You're cruising!",
]
MARATHON_MESSAGES = [
    "Marathon reached!",
    "Marathon complete!",
    "You crossed the line!",
    "26.2 done. Incredible!",
]

try:
    while True:
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

        total_steps = int(time.time() - start_time)
        total_km = total_steps // STEPS_PER_KM
        steps = total_steps % STEPS_PER_KM
        marathons = total_km // KM_PER_MARATHON
        km = total_km % KM_PER_MARATHON

        if total_km != prev_total_km:
            km_duration = time.time() - last_km_time
            if prev_km_duration is None:
                pace_note = ""
            elif km_duration < prev_km_duration:
                pace_note = " Speeding up!"
            elif km_duration > prev_km_duration:
                pace_note = " Slowing down!"
            else:
                pace_note = " Steady pace!"
            prev_km_duration = km_duration
            last_km_time = time.time()

            base_message = random.choice(MARATHON_MESSAGES) if marathons != prev_marathons else random.choice(KM_MESSAGES)
            message = base_message + pace_note
            message_until = time.time() + MESSAGE_DURATION
        prev_total_km = total_km
        prev_marathons = marathons

        date_string = time.strftime("%m/%d/%Y")
        distance_string = "{} Mar : {} Km : {} Step(s)".format(marathons, km, steps)
        draw.text((x, top), date_string, font=font, fill="#FFFFFF")
        draw.text((x, top + 20), distance_string, font=font, fill="#FFFFFF")

        # Elapsed time is only shown in the stop summary, not on the live screen
        elapsed_seconds = int(time.time() - start_time)
        elapsed_string = "{:02}:{:02}:{:02}".format(
            elapsed_seconds // 3600, (elapsed_seconds % 3600) // 60, elapsed_seconds % 60
        )

        if time.time() < message_until:
            draw.text((x, top + 40), message, font=font, fill="#FFFFFF")

        elapsed_minutes = (time.time() - start_time) / 60
        pace = total_steps / elapsed_minutes if elapsed_minutes > 0 else 0
        draw.text((x, top + 60), "Pace: {:.0f} steps/min".format(pace), font=font, fill="#888888")

        # Display image.
        disp.image(image, rotation)
        time.sleep(1)

        if elapsed_seconds >= RUN_DURATION_LIMIT:
            raise KeyboardInterrupt  # 24 hours reached: stop and show the same summary as ctrl-c
except KeyboardInterrupt:
    # Show a final summary on screen and in the terminal when the script is stopped
    try:
        with open(LOG_FILE, "r") as f:
            session_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        session_log = []

    previous_session = session_log[-1] if session_log else None
    if previous_session:
        step_diff = total_steps - previous_session["total_steps"]
        comparison_string = "vs {}: {}{} steps".format(
            previous_session["date"], "+" if step_diff >= 0 else "", step_diff
        )
    else:
        comparison_string = "No previous session yet"

    session_log.append(
        {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_steps": total_steps,
            "marathons": marathons,
            "km": km,
            "steps": steps,
            "elapsed": elapsed_string,
        }
    )
    with open(LOG_FILE, "w") as f:
        json.dump(session_log, f, indent=2)

    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
    draw.text((x, top), "Stopped!", font=font, fill="#FFFFFF")
    draw.text((x, top + 20), "Total steps: {}".format(total_steps), font=font, fill="#FFFFFF")
    draw.text((x, top + 40), "{} Mar : {} Km : {} Step(s)".format(marathons, km, steps), font=font, fill="#FFFFFF")
    draw.text((x, top + 60), "Elapsed: {}".format(elapsed_string), font=font, fill="#FFFFFF")
    draw.text((x, top + 80), comparison_string, font=font, fill="#888888")
    disp.image(image, rotation)
    print("Stopped! Total steps taken: {}".format(total_steps))
    print("{} Mar : {} Km : {} Step(s)".format(marathons, km, steps))
    print("Elapsed time: {}".format(elapsed_string))
    print(comparison_string)
