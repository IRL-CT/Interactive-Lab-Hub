#!/usr/bin/env python3
"""
Time Garden - Lab 2 Part 2
Standalone Raspberry Pi MiniPiTFT clock prototype.

Controls
--------
Button A (GPIO 23):
    IDLE -> start
    RUNNING -> pause
    PAUSED -> resume
    COMPLETE -> start a new session

Button B (GPIO 24):
    Switch between the current focus session and today's garden.

The demo session is 30 seconds so it is easy to show in class/video.
For a real 25-minute Pomodoro-style session, change:
    SESSION_SECONDS = 25 * 60
"""

import time
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789


# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------

SESSION_SECONDS = 30          # Demo length. Change to 25 * 60 for 25 minutes.
REFRESH_SECONDS = 0.20

SCREEN_WIDTH = 240
SCREEN_HEIGHT = 135
ROTATION = 90

BACKGROUND = (245, 242, 230)
TEXT = (35, 45, 35)
MUTED = (95, 105, 95)
GREEN = (66, 130, 82)
DARK_GREEN = (44, 100, 62)
LIGHT_GREEN = (116, 170, 105)
BROWN = (125, 88, 58)
PINK = (220, 105, 135)
YELLOW = (245, 194, 66)
POT = (180, 120, 80)


# ---------------------------------------------------------
# Display setup
# ---------------------------------------------------------

cs_pin = digitalio.DigitalInOut(board.D5)  # GPIO5 (pin 29), matches course Pi 5 wiring
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

spi = board.SPI()

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=64000000,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)


# ---------------------------------------------------------
# Buttons
# ---------------------------------------------------------

button_a = digitalio.DigitalInOut(board.D23)
button_b = digitalio.DigitalInOut(board.D24)

button_a.switch_to_input(pull=digitalio.Pull.UP)
button_b.switch_to_input(pull=digitalio.Pull.UP)

# Buttons use internal pull-ups, so they are active-LOW:
# True = not pressed, False = pressed.
def button_a_pressed():
    return button_a.value == False


def button_b_pressed():
    return button_b.value == False


# ---------------------------------------------------------
# Fonts
# ---------------------------------------------------------

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


font_small = load_font(FONT_PATH, 12)
font_medium = load_font(BOLD_FONT_PATH, 16)
font_large = load_font(BOLD_FONT_PATH, 24)


# ---------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------

def centered_text(draw, text, y, font, fill=TEXT):
    """Draw text centered horizontally."""
    try:
        box = draw.textbbox((0, 0), text, font=font)
        text_width = box[2] - box[0]
    except AttributeError:
        text_width = draw.textsize(text, font=font)[0]

    x = (SCREEN_WIDTH - text_width) // 2
    draw.text((x, y), text, font=font, fill=fill)


def draw_pot(draw, center_x, base_y):
    """Draw a simple flower pot."""
    draw.polygon(
        [
            (center_x - 18, base_y - 18),
            (center_x + 18, base_y - 18),
            (center_x + 13, base_y),
            (center_x - 13, base_y),
        ],
        fill=POT,
    )


def draw_seed(draw, center_x, base_y):
    """Stage 1: seed."""
    draw_pot(draw, center_x, base_y)
    draw.ellipse(
        (center_x - 4, base_y - 27, center_x + 4, base_y - 19),
        fill=BROWN,
    )


def draw_sprout(draw, center_x, base_y):
    """Stage 2: small sprout."""
    draw_pot(draw, center_x, base_y)

    draw.line(
        (center_x, base_y - 18, center_x, base_y - 48),
        fill=DARK_GREEN,
        width=4,
    )

    draw.ellipse(
        (center_x - 17, base_y - 43, center_x, base_y - 29),
        fill=LIGHT_GREEN,
    )
    draw.ellipse(
        (center_x, base_y - 50, center_x + 17, base_y - 36),
        fill=GREEN,
    )


def draw_plant(draw, center_x, base_y):
    """Stage 3: larger leafy plant."""
    draw_pot(draw, center_x, base_y)

    draw.line(
        (center_x, base_y - 18, center_x, base_y - 62),
        fill=DARK_GREEN,
        width=5,
    )

    leaves = [
        (-25, -50, -3, -34, LIGHT_GREEN),
        (3, -58, 25, -42, GREEN),
        (-23, -68, -1, -52, GREEN),
        (1, -76, 23, -60, LIGHT_GREEN),
    ]

    for x1, y1, x2, y2, color in leaves:
        draw.ellipse(
            (center_x + x1, base_y + y1, center_x + x2, base_y + y2),
            fill=color,
        )


def draw_flower(draw, center_x, base_y):
    """Stage 4: blooming flower."""
    draw_pot(draw, center_x, base_y)

    draw.line(
        (center_x, base_y - 18, center_x, base_y - 67),
        fill=DARK_GREEN,
        width=5,
    )

    draw.ellipse(
        (center_x - 26, base_y - 53, center_x - 2, base_y - 37),
        fill=GREEN,
    )
    draw.ellipse(
        (center_x + 2, base_y - 61, center_x + 26, base_y - 45),
        fill=LIGHT_GREEN,
    )

    flower_y = base_y - 78

    petals = [
        (0, -13),
        (12, -4),
        (8, 10),
        (-8, 10),
        (-12, -4),
    ]

    for dx, dy in petals:
        draw.ellipse(
            (
                center_x + dx - 8,
                flower_y + dy - 8,
                center_x + dx + 8,
                flower_y + dy + 8,
            ),
            fill=PINK,
        )

    draw.ellipse(
        (center_x - 7, flower_y - 7, center_x + 7, flower_y + 7),
        fill=YELLOW,
    )


def plant_stage(progress):
    """
    Return plant stage from progress 0.0 to 1.0.

    0-25%   seed
    25-50%  sprout
    50-75%  plant
    75-100% flower
    """
    if progress < 0.25:
        return 0
    if progress < 0.50:
        return 1
    if progress < 0.75:
        return 2
    return 3


def draw_progress_bar(draw, progress):
    x1 = 22
    y1 = 108
    x2 = 218
    y2 = 117

    draw.rounded_rectangle(
        (x1, y1, x2, y2),
        radius=4,
        fill=(220, 220, 210),
    )

    progress = max(0.0, min(1.0, progress))
    filled_x = x1 + int((x2 - x1) * progress)

    if filled_x > x1:
        draw.rounded_rectangle(
            (x1, y1, filled_x, y2),
            radius=4,
            fill=GREEN,
        )


def show_image(image):
    display.image(image, ROTATION)


# ---------------------------------------------------------
# Screens
# ---------------------------------------------------------

def draw_session_screen(state, elapsed):
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    centered_text(draw, "TIME GARDEN", 5, font_medium, DARK_GREEN)

    progress = min(elapsed / SESSION_SECONDS, 1.0)
    remaining = max(0, int(SESSION_SECONDS - elapsed))

    minutes = remaining // 60
    seconds = remaining % 60

    if state == "IDLE":
        status = "Press A to start"
        time_text = f"{SESSION_SECONDS // 60:02d}:{SESSION_SECONDS % 60:02d}"

    elif state == "RUNNING":
        status = "Focusing..."
        time_text = f"{minutes:02d}:{seconds:02d}"

    elif state == "PAUSED":
        status = "Paused - press A"
        time_text = f"{minutes:02d}:{seconds:02d}"

    else:
        status = "Session complete!"
        time_text = "BLOOM!"

    # Plant on the left
    center_x = 65
    base_y = 99

    stage = plant_stage(progress)

    if state == "IDLE":
        draw_seed(draw, center_x, base_y)
    elif state == "COMPLETE":
        draw_flower(draw, center_x, base_y)
    elif stage == 0:
        draw_seed(draw, center_x, base_y)
    elif stage == 1:
        draw_sprout(draw, center_x, base_y)
    elif stage == 2:
        draw_plant(draw, center_x, base_y)
    else:
        draw_flower(draw, center_x, base_y)

    # Timer and status on the right
    draw.text((125, 42), time_text, font=font_large, fill=TEXT)
    draw.text((125, 75), status, font=font_small, fill=MUTED)

    draw_progress_bar(draw, progress)

    draw.text(
        (22, 121),
        "A: start/pause",
        font=font_small,
        fill=MUTED,
    )
    draw.text(
        (139, 121),
        "B: garden",
        font=font_small,
        fill=MUTED,
    )

    show_image(image)


def draw_garden_screen(completed_sessions):
    image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    centered_text(draw, "TODAY'S GARDEN", 7, font_medium, DARK_GREEN)

    # Show up to 5 flowers on screen.
    flowers_to_show = min(completed_sessions, 5)

    if flowers_to_show == 0:
        centered_text(draw, "No flowers yet", 49, font_medium, MUTED)
        centered_text(draw, "Complete a focus session!", 75, font_small, MUTED)
    else:
        spacing = 40
        start_x = 120 - ((flowers_to_show - 1) * spacing) // 2

        for i in range(flowers_to_show):
            x = start_x + i * spacing
            draw_flower(draw, x, 94)

        centered_text(
            draw,
            f"{completed_sessions} session(s) completed",
            100,
            font_small,
            TEXT,
        )

    draw.text(
        (78, 121),
        "Press B to go back",
        font=font_small,
        fill=MUTED,
    )

    show_image(image)


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():
    state = "IDLE"
    view = "SESSION"

    # Total active focus time accumulated so far.
    elapsed = 0.0

    # Timestamp of the most recent resume/start.
    running_since = None

    completed_sessions = 0

    previous_a = False
    previous_b = False

    try:
        while True:
            now = time.monotonic()

            current_a = button_a_pressed()
            current_b = button_b_pressed()

            # Detect a new Button A press.
            a_clicked = current_a and not previous_a

            # Detect a new Button B press.
            b_clicked = current_b and not previous_b

            if a_clicked:
                if state == "IDLE":
                    elapsed = 0.0
                    running_since = now
                    state = "RUNNING"
                    view = "SESSION"

                elif state == "RUNNING":
                    elapsed += now - running_since
                    running_since = None
                    state = "PAUSED"

                elif state == "PAUSED":
                    running_since = now
                    state = "RUNNING"

                elif state == "COMPLETE":
                    elapsed = 0.0
                    running_since = now
                    state = "RUNNING"
                    view = "SESSION"

            if b_clicked:
                if view == "SESSION":
                    view = "GARDEN"
                else:
                    view = "SESSION"

            # Calculate the live elapsed time while running.
            live_elapsed = elapsed

            if state == "RUNNING" and running_since is not None:
                live_elapsed += now - running_since

                if live_elapsed >= SESSION_SECONDS:
                    elapsed = SESSION_SECONDS
                    running_since = None
                    state = "COMPLETE"
                    completed_sessions += 1
                    live_elapsed = elapsed
                    view = "SESSION"

            # Draw current screen.
            if view == "GARDEN":
                draw_garden_screen(completed_sessions)
            else:
                draw_session_screen(state, live_elapsed)

            previous_a = current_a
            previous_b = current_b

            time.sleep(REFRESH_SECONDS)

    except KeyboardInterrupt:
        print("\nTime Garden stopped.")

    finally:
        backlight.value = False


if __name__ == "__main__":
    print("Time Garden is running.")
    print("Button A: start / pause / resume")
    print("Button B: switch to today's garden")
    print("Press Ctrl+C to stop.")
    main()
