import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789


# --------------------------------------------------
# Display setup
# --------------------------------------------------

BAUDRATE = 64000000

spi = board.SPI()

cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

disp = st7789.ST7789(
    spi,
    rotation=90,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

WIDTH = 240
HEIGHT = 135


# --------------------------------------------------
# Colors
# --------------------------------------------------

READY_COLOR = (25, 25, 25)
LISTENING_COLOR = (30, 150, 70)
PROCESSING_COLOR = (235, 160, 35)
SPEAKING_COLOR = (40, 110, 200)

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)


# --------------------------------------------------
# Font
# --------------------------------------------------

BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

try:
    title_font = ImageFont.truetype(
        BOLD_FONT_PATH,
        28
    )
except OSError:
    title_font = ImageFont.load_default()


# --------------------------------------------------
# Generic state screen
# --------------------------------------------------

def show_state(
    title,
    background,
    text_color=WHITE,
):
    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        background
    )

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------
    # Center title
    # --------------------------------------------------

    box = draw.textbbox(
        (0, 0),
        title,
        font=title_font
    )

    text_width = box[2] - box[0]

    x = (WIDTH - text_width) // 2
    y = 28

    draw.text(
        (x, y),
        title,
        font=title_font,
        fill=text_color
    )

    # --------------------------------------------------
    # Status dot
    # --------------------------------------------------

    radius = 11
    center_x = WIDTH // 2
    center_y = 88

    draw.ellipse(
        (
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        ),
        fill=text_color
    )

    # Send image to screen
    disp.image(image)


# --------------------------------------------------
# Public UI states
# --------------------------------------------------

def show_ready():
    show_state(
        title="READY",
        background=READY_COLOR,
        text_color=WHITE,
    )


def show_listening():
    show_state(
        title="LISTENING",
        background=LISTENING_COLOR,
        text_color=WHITE,
    )


def show_processing():
    show_state(
        title="PROCESSING",
        background=PROCESSING_COLOR,
        text_color=BLACK,
    )


def show_speaking(text=None):
    # text is intentionally ignored
    # so app.py can still call show_speaking(response)
    show_state(
        title="SPEAKING",
        background=SPEAKING_COLOR,
        text_color=WHITE,
    )


# --------------------------------------------------
# Test UI directly
# --------------------------------------------------

if __name__ == "__main__":
    import time

    print("Testing calendar assistant UI...")

    show_ready()
    time.sleep(2)

    show_listening()
    time.sleep(2)

    show_processing()
    time.sleep(2)

    show_speaking()
    time.sleep(2)

    show_ready()

    print("UI test finished.")