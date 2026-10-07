from time import monotonic, sleep
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

from pomodoro_logic import PomodoroState, RAINBOW_COLORS, tick

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

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
summary_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Button A is active-low because of the internal pull-up.
buttonA = digitalio.DigitalInOut(board.D23)
buttonA.switch_to_input(pull=digitalio.Pull.UP)

# Button B: hold for HOLD_DURATION seconds to reset the timer to idle.
buttonB = digitalio.DigitalInOut(board.D24)
buttonB.switch_to_input(pull=digitalio.Pull.UP)


# Test profile: 30 MIN uses focus=10, wrap=2, break=3.
# Tap B while idle to switch to the 60 MIN profile.
state = PomodoroState(session_minutes=30)

while True:
    now = monotonic()
    a_pressed = not buttonA.value
    b_pressed = not buttonB.value
    tick(state, now, a_pressed, b_pressed)

    display_phase = state.display_phase()
    display_text = state.display_text()
    if display_phase == "WRAP":
        display_text = "WRAP UP"

    # state.color(now) makes the amber wrap-up screen "breathe".
    draw.rectangle((0, 0, width, height), outline=0, fill=state.color(now))

    text_color = "#000000" if display_phase == "IDLE" else "#FFFFFF"
    if state.show_summary:
        draw.text(
            (width // 2, height // 2 - 20),
            state.summary_lines()[0],
            font=summary_font,
            fill=text_color,
            anchor="mm",
        )
        strip_top = height - 18
        strip_width = width // len(RAINBOW_COLORS)
        for index, color in enumerate(state.rainbow_colors()):
            left = index * strip_width
            right = width if index == len(RAINBOW_COLORS) - 1 else (index + 1) * strip_width
            draw.rectangle((left, strip_top, right, height), fill=color)
    else:
        draw.text((width // 2, height // 2), display_text, font=font, fill=text_color, anchor="mm")

    # Display image.
    disp.image(image, rotation)
    sleep(0.05)
