# Portions of this code were generated with the help of OpenAI's ChatGPT.
# Reviewed and adapted for Interactive Device Design, 2025.

import time
import threading
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# --- Stepper setup ---
step_pins = [board.D6, board.D12, board.D16, board.D26]  # IN1–IN4
control_pins = [digitalio.DigitalInOut(pin) for pin in step_pins]
for pin in control_pins:
    pin.direction = digitalio.Direction.OUTPUT
    pin.value = False

# Half-step sequence
halfstep_seq = [
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
    [1,0,0,1],
]

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

width = disp.width
height = disp.height

# --- Buttons ---
btn_a = digitalio.DigitalInOut(board.D23)
btn_a.switch_to_input(pull=digitalio.Pull.UP)

btn_b = digitalio.DigitalInOut(board.D24)
btn_b.switch_to_input(pull=digitalio.Pull.UP)

# --- Fonts ---
big_font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60
)
small_font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30
)

# --- Drawing helper ---
def draw_text_rotated(text, angle=90, wait_time=1, use_small=False, y_offset=0):
    font = small_font if use_small else big_font
    image = Image.new("RGB", (width, height), "black")

    temp = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp)

    bbox = temp_draw.textbbox((0, 0), str(text), font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2 + y_offset

    temp_draw.text((x, y), str(text), font=font, fill="white")

    rotated = temp.rotate(angle, expand=True)

    image.paste(rotated, ((width - rotated.width) // 2,
                          (height - rotated.height) // 2),
                          rotated)

    disp.image(image)

    start = time.monotonic()
    while time.monotonic() - start < wait_time:
        pass

def clear_screen():
    image = Image.new("RGB", (width, height), "black")
    disp.image(image)

# --- Stepper functions ---
def step_motor(steps, delay=0.001, reverse=False):
    """Step motor forward or reverse."""
    seq = halfstep_seq[::-1] if reverse else halfstep_seq
    for _ in range(steps):
        for halfstep in seq:
            for i, pin in enumerate(control_pins):
                pin.value = halfstep[i]
            time.sleep(delay)
    for pin in control_pins:
        pin.value = False

def step_continuous():
    # Draw "ADJUST" once when rotation starts
    draw_text_rotated("ADJUST", angle=270, wait_time=0.1, use_small=True)

    while continuous_flag[0]:
        for halfstep in halfstep_seq:
            for i, pin in enumerate(control_pins):
                pin.value = halfstep[i]
            time.sleep(0.001)  # fast stepping
    for pin in control_pins:
        pin.value = False
    clear_screen()


def step_90_with_animation():
    # Countdown numbers shifted down a bit
    for n in range(10, -1, -1):
        draw_text_rotated(n, angle=270, wait_time=1, y_offset=-5)

    draw_text_rotated("WAKE\nUP!!!", angle=270, wait_time=2, use_small=True)

    # Reverse 90° first
    step_motor(200, delay=0.001, reverse=True)
    time.sleep(2)

    # Then forward 90°
    step_motor(200, delay=0.001, reverse=False)

    clear_screen()

# --- State flags ---
continuous_flag = [False]
thread_b = None

# --- Startup ---
draw_text_rotated("ADJUST", angle=270, wait_time=2, use_small=True)
clear_screen()

# --- Main loop ---
print("Press A for countdown + 90° step, B to toggle continuous rotation.")
try:
    while True:
        if not btn_a.value:
            time.sleep(0.2)
            print("Running countdown + 90° sequence.")
            step_90_with_animation()

        if not btn_b.value:
            time.sleep(0.2)
            continuous_flag[0] = not continuous_flag[0]
            if continuous_flag[0]:
                print("Continuous rotation started.")
                thread_b = threading.Thread(target=step_continuous)
                thread_b.start()
            else:
                print("Continuous rotation stopped.")

        time.sleep(0.05)

except KeyboardInterrupt:
    for pin in control_pins:
        pin.value = False
    clear_screen()
    print("Exiting cleanly.")
