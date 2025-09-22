# rpi5_minipitft_st7789.py
# Works on Raspberry Pi 5 with Adafruit Blinka backend (lgpio) and SPI enabled.
# Wiring change: connect the display's CS to GPIO5 (pin 29), not CE0.

import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import webcolors


# ---------------------------
# SPI + Display configuration
# ---------------------------
# Use a FREE GPIO for CS to avoid conflicts with the SPI driver owning CE0/CE1.
cs_pin = digitalio.DigitalInOut(board.D5)     # GPIO5  (PIN 29)  <-- wire display CS here
dc_pin = digitalio.DigitalInOut(board.D25)    # GPIO25 (PIN 22)
reset_pin = None

# Safer baudrate for stability; you can try 64_000_000 if your wiring is short/clean.
BAUDRATE = 64000000

# Create SPI object on SPI0 (spidev0.* must exist; enable SPI in raspi-config).
spi = board.SPI()

# For Adafruit mini PiTFT 1.14" (240x135) ST7789 use width=135, height=240, x/y offsets below.
# If you actually have a 240x240 panel, set width=240, height=240 and x_offset=y_offset=0.
# Keep the “native” portrait dims for this board
DISPLAY_WIDTH  = 135
DISPLAY_HEIGHT = 240

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    x_offset=53,
    y_offset=40,
)

# ---------------------------
# Backlight + Buttons
# ---------------------------
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# ---------------------------
# Menu items
# ---------------------------
menu_items = {
    "Beef": "0:15",       # 15 seconds
    "Pork": "0:30",       # 30 seconds
    "Chicken": "1:00",    # 1 minute
    "Lamb": "1:30",       # 1 minute 30 sec
    "Fish": "0:10",       # 10 sec
    "Vegetarian": "0:05", # 5 sec
    "Vegan": "2:00"       # 2 minutes
}

# ---------------------------
# Global Variables
# ---------------------------
mode = 0 # 0 for menu, 1 for timer
selected_index = 0

image = Image.new("RGB", (display.width, display.height))
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

# ---------------------------
# Functions
# ---------------------------
def draw_menu():
    global mode, selected_index
    mode = 0
    draw.rectangle((0, 0, image.width, image.height), fill=0)

    y = 10
    for i, (item, _) in enumerate(menu_items.items()):
        prefix = "> " if i == selected_index else " "
        color = (255, 255, 0) if i == selected_index else (255, 255, 255)
        draw.text((10, y), prefix + item, font=font, fill=color)
        y += 30
    display.image(image)

def select_item():
    global mode, selected_index
    global buttonA, buttonB
    keys = list(menu_items.keys())
    selected_key = keys[selected_index]

    # --- Convert stored "M:S" string to total seconds ---
    value = menu_items[selected_key]
    if isinstance(value, str):  # e.g. "1:30"
        min_str, sec_str = value.split(":")
        countdown = int(min_str) * 60 + int(sec_str)
    else:  # fallback if already stored as seconds
        countdown = int(value)

    while countdown >= 0:
        # check if both buttons are pressed, exit the countdown
        a_pressed = not buttonA.value
        b_pressed = not buttonB.value

        # if both pressed → exit countdown
        if a_pressed and b_pressed:
            mode = 0
            selected_index = 0
            draw_menu()
            return   # exit function immediately

        draw.rectangle((0, 0, image.width, image.height), fill=0)

        # Format as MM:SS
        minutes, seconds = divmod(countdown, 60)
        time_string = f"{minutes:02}:{seconds:02}"

        draw.text((10, 10), f"{selected_key} Timer", font=font, fill="#FFFFFF")
        draw.text((10, 40), time_string, font=font, fill="#00FF00")

        display.image(image)
        time.sleep(1)

        countdown -= 1

    # Final message when countdown is done
    draw.rectangle((0, 0, image.width, image.height), fill=0)
    draw.text((10, 10), f"{selected_key} Ready!", font=font, fill="#FF0000")
    display.image(image)

# ---------------------------
# Main loop
# ---------------------------
print("Display size:", display.width, "x", display.height)
print("Press A for previous item, B for next item, both to exit.")

draw_menu()

while True:
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)

    if a_pressed and b_pressed:
        draw.rectangle((0, 0, display.width, display.height), outline=0, fill=0)
        draw.text((10, 100), "Goodbye!", font=font, fill=(255, 0, 0))
        display.image(image)
        time.sleep(1)
        break

    if a_pressed:
        if mode == 0:
            selected_index = (selected_index + 1) % len(menu_items)
            draw_menu()
            time.sleep(0.3)  # debounce delay
        else:
            selected_index = 0
            draw_menu()
            time.sleep(0.3)  # debounce delay

    if b_pressed:
        if mode == 0:
            mode = 1
            select_item()
            time.sleep(0.3)  # debounce delay
        else:
            mode = 0
            selected_index = 0
            draw_menu()
            time.sleep(0.3)  # debounce delay