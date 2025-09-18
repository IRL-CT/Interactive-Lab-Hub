# # rpi5_minipitft_st7789.py
# # Works on Raspberry Pi 5 with Adafruit Blinka backend (lgpio) and SPI enabled.
# # Wiring change: connect the display's CS to GPIO5 (pin 29), not CE0.

# import time
# import digitalio
# import board

# from adafruit_rgb_display.rgb import color565
# import adafruit_rgb_display.st7789 as st7789
# import webcolors

# # ---------------------------
# # SPI + Display configuration
# # ---------------------------
# # Use a FREE GPIO for CS to avoid conflicts with the SPI driver owning CE0/CE1.
# cs_pin = digitalio.DigitalInOut(board.D5)     # GPIO5  (PIN 29)  <-- wire display CS here
# dc_pin = digitalio.DigitalInOut(board.D25)    # GPIO25 (PIN 22)
# reset_pin = None

# # Safer baudrate for stability; you can try 64_000_000 if your wiring is short/clean.
# BAUDRATE = 64000000

# # Create SPI object on SPI0 (spidev0.* must exist; enable SPI in raspi-config).
# spi = board.SPI()

# # For Adafruit mini PiTFT 1.14" (240x135) ST7789 use width=135, height=240, x/y offsets below.
# # If you actually have a 240x240 panel, set width=240, height=240 and x_offset=y_offset=0.
# display = st7789.ST7789(
#     spi,
#     cs=cs_pin,
#     dc=dc_pin,
#     rst=reset_pin,
#     baudrate=BAUDRATE,
#     width=135,
#     height=240,
#     x_offset=53,
#     y_offset=40,
#     # rotation=0  # uncomment/change if your screen orientation is off
# )

# # ---------------------------
# # Backlight + Buttons
# # ---------------------------
# backlight = digitalio.DigitalInOut(board.D22)  # GPIO22 (PIN 15)
# backlight.switch_to_output(value=True)

# buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
# buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
# # Use internal pull-ups; buttons then read LOW when pressed.
# buttonA.switch_to_input(pull=digitalio.Pull.UP)
# buttonB.switch_to_input(pull=digitalio.Pull.UP)

# # ---------------------------
# # Ask user for a color
# # ---------------------------
# screenColor = None
# while not screenColor:
#     try:
#         name = input('Type the name of a color and hit enter: ')
#         rgb = webcolors.name_to_rgb(name)
#         screenColor = color565(rgb.red, rgb.green, rgb.blue)
#     except ValueError:
#         print("whoops I don't know that one")

# # ---------------------------
# # Main loop
# # ---------------------------
# print("Press A for WHITE, B for your color, both to turn backlight OFF.")
# while True:
#     # Buttons are active-LOW because of pull-ups
#     a_pressed = (buttonA.value == False)
#     b_pressed = (buttonB.value == False)

#     if a_pressed and b_pressed:
#         backlight.value = False  # turn off backlight
#     else:
#         backlight.value = True   # turn on backlight

#     if b_pressed and not a_pressed:
#         display.fill(screenColor)               # user's color
#     elif a_pressed and not b_pressed:
#         display.fill(color565(255, 255, 255))   # white
#     else:
#         display.fill(color565(0, 255, 0))       # green

#     time.sleep(0.02)  # small debounce / CPU break



import time
from time import localtime
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# --- Display setup ---
# MiniPiTFT pins (hardwired)
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

# Turn on backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# SPI bus
spi = board.SPI()

# Create ST7789 display
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=64000000,
    width=240,
    height=240,
    x_offset=0,
    y_offset=80,
)
rotation = 90
width = disp.width
height = disp.height

# --- Buttons ---
btn_top = digitalio.DigitalInOut(board.D23)   # Button A
btn_top.switch_to_input(pull=digitalio.Pull.UP)

btn_bottom = digitalio.DigitalInOut(board.D24)  # Button B
btn_bottom.switch_to_input(pull=digitalio.Pull.UP)

# --- Drawing setup ---
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

# --- Helper ---
def pages_today(total_pages=24):
    t = localtime()
    seconds_today = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
    return int((seconds_today / 86400.0) * total_pages)

# --- State ---
page_counter = 0
show_counter = False

# --- Page turn animation ---
def page_turn():
    for offset in range(0, width // 2, 20):
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
        mid = width // 2

        # static right page
        draw.rectangle((mid + 5, 40, width - 10, 200), outline=(255, 255, 255))
        # animated left page sliding away
        draw.rectangle((10 + offset, 40, mid - 5 + offset, 200), outline=(255, 255, 255))

        disp.image(image, rotation)
        time.sleep(0.05)

# --- Main loop ---
while True:
    if not btn_top.value:  # pressed (LOW)
        page_counter += 1
        page_turn()

    if not btn_bottom.value:  # pressed
        show_counter = not show_counter

    # Clear screen
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

    if show_counter:
        draw.text((50, 120), f"Counter: {page_counter}", font=font, fill=(0, 255, 0))
    else:
        total_pages = 24
        current_page = pages_today(total_pages)
        mid = width // 2

        # Draw book outline
        draw.rectangle((10, 40, mid - 5, 200), outline=(255, 255, 255))
        draw.rectangle((mid + 5, 40, width - 10, 200), outline=(255, 255, 255))

        # Show page numbers
        draw.text((30, 100), f"Page {current_page}", font=font, fill=(255, 255, 0))
        draw.text((mid + 20, 100), f"of {total_pages}", font=font, fill=(0, 255, 255))

        # Progress bar
        progress = current_page / total_pages
        bar_width = int((width - 20) * progress)
        draw.rectangle((10, 210, 10 + bar_width, 230), fill=(150, 75, 0))

    # Push to display
    disp.image(image, rotation)
    time.sleep(0.1)
