# rpi5_minipitft_st7789.py
# Works on Raspberry Pi 5 with Adafruit Blinka backend (lgpio) and SPI enabled.
# Wiring change: connect the display's CS to GPIO5 (pin 29), not CE0.

import time
import digitalio
import board

import csv
from adafruit_rgb_display.rgb import color565
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
display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
    # rotation=0  # uncomment/change if your screen orientation is off
)

# ---------------------------
# Backlight + Buttons
# ---------------------------
backlight = digitalio.DigitalInOut(board.D22)  # GPIO22 (PIN 15)
backlight.switch_to_output(value=True)

buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
# Use internal pull-ups; buttons then read LOW when pressed.
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)


# Evergreen tracker application
# 1. Read the tracker CSV file from disk.
# 2. Extract a sequence of (date, hours) pairs.
# 3. Only keep the most recent consecutive sequence of days with nonzero working hours.
# 4. Visualize each day's hours as a green bar:
#    - Each bar's brightness and lightness reflect the number of hours worked (more hours = brighter green).

# --- User Interaction ---
# - Button A: Increments today's working hours by 1 (adds to today's entry in the CSV).
# - Button B: Decrements today's working hours by 1 (subtracts from today's entry, but not below zero).
# - Buttons A + B together: Turns off the backlight to save power.
# - After each button press, update the display to reflect the new value for today.

# --- Display ---
# - The display shows a series of vertical green bars, one for each day in the current consecutive sequence.
# - The height of each bar is fixed, but the brightness of the green color varies based on the number of hours worked that day.
# - The display updates in real-time as buttons are pressed.
def draw_streak(streak):
    """Draw green blocks for streak on 3x7 grid with square blocks"""
    rows = 7
    spacing = 3
    block_size = 30
    start_x = 16
    start_y = 3

    for i, (d, hours) in enumerate(streak[-21:]):
        row = i // rows
        col = i - (rows * row)
        x = start_x + col * (block_size + spacing)
        y = start_y + row * (block_size + spacing)
        green = min(int((hours / 8) * 255), 255)
        display.fill_rectangle(x, y, block_size, block_size, color565(0, green, 0))

# Read CSV into a list of (date, hours) tuples
tracker_file = "tracker.csv"
data = []

prev_date = None
with open(tracker_file, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        date_str, hours_str = row
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        hours = int(hours_str)

        if prev_date and (date - prev_date).days > 1:
            data = []  # reset if non-consecutive dates
        if hours == 0:
            data = []  # reset if zero hours
        data.append((date, hours))
        prev_date = date

# display the data as green bars
draw_streak(data)

while True:
    # Buttons are active-LOW because of pull-ups
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)

    if a_pressed and b_pressed:
        backlight.value = False  # turn off backlight
    else:
        backlight.value = True   # turn on backlight

    if a_pressed and not b_pressed:
        # Increment today's hours
        today = datetime.now().date()
        if data and data[-1][0] == today:
            data[-1] = (today, data[-1][1] + 1)
        else:
            data.append((today, 1))
    elif b_pressed and not a_pressed:
        # Decrement today's hours
        today = datetime.now().date()
        if data and data[-1][0] == today and data[-1][1] > 0:
            data[-1] = (today, data[-1][1] - 1)
    draw_streak(data)
    # write back to CSV
    with open(tracker_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for date, hours in data:
            writer.writerow([date.strftime("%Y-%m-%d"), hours])
    time.sleep(0.02)  # small debounce / CPU break
