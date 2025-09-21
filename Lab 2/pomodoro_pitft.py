# pomodoro_pitft.py
# Mini-PiTFT 1.14" (ST7789 240x135) Pomodoro clock with two buttons.
# A = GPIO23: short -> start/pause, long -> reset
# B = GPIO24: short -> skip (focus<->break), long -> toggle backlight

import time
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# ---------------------------
# Display setup (matches your examples)
# ---------------------------
cs_pin = digitalio.DigitalInOut(board.D5)      # GPIO5  (PIN 29)
dc_pin = digitalio.DigitalInOut(board.D25)     # GPIO25 (PIN 22)
reset_pin = None
BAUDRATE = 64_000_000
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

# Render in portrait (240x135) then rotate 90° like your sample code
height = disp.width     # 135
width  = disp.height    # 240
rotation = 90

image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)

# Backlight on D22 (optional)
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)
backlight_enabled = True

# ---------------------------
# Buttons
# ---------------------------
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input(pull=digitalio.Pull.UP)  # active low
buttonB.switch_to_input(pull=digitalio.Pull.UP)

def read_button(btn) -> bool:
    """Return True if pressed (active low)."""
    return btn.value is False

# ---------------------------
# Fonts & colors
# ---------------------------
def load_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()

font_title = load_font(22)
font_time  = load_font(72)   # large digits fit 240px width
font_emoji = load_font(26)

RED_FOCUS    = (226, 61, 61)     # #E23D3D
GREEN_BREAK  = (49, 184, 106)    # #31B86A
WHITE        = (255, 255, 255)

# ---------------------------
# Pomodoro state
# ---------------------------
FOCUS_SECS = 25 * 60
BREAK_SECS = 5 * 60

mode = "focus"          # "focus" or "break"
running = False
remaining = FOCUS_SECS
last_tick = time.time()

# Button press timing (for short/long detection)
LONG_SEC = 1.2
a_down_time = None
b_down_time = None
a_prev = False
b_prev = False

def fmt_time(secs: int) -> str:
    secs = max(0, int(secs))
    m = secs // 60
    s = secs % 60
    return f"{m:02d}:{s:02d}"

def reset_current():
    global remaining, running
    remaining = FOCUS_SECS if mode == "focus" else BREAK_SECS
    running = False

def skip_mode():
    global mode, remaining, running
    if mode == "focus":
        mode = "break"
        remaining = BREAK_SECS
    else:
        mode = "focus"
        remaining = FOCUS_SECS
    running = False  # start paused after skip

def toggle_backlight():
    global backlight_enabled
    backlight_enabled = not backlight_enabled
    backlight.value = backlight_enabled

def tick(dt: float):
    global remaining, mode, running
    if not running:
        return
    remaining -= dt
    if remaining <= 0:
        # auto-switch at end (flash handled in draw)
        if mode == "focus":
            mode = "break"
            remaining = BREAK_SECS
        else:
            mode = "focus"
            remaining = FOCUS_SECS
        running = False  # pause after auto switch

def text_size(txt: str, font: ImageFont.FreeTypeFont):
    """Return (w, h) using Pillow >=10 textbbox."""
    bbox = draw.textbbox((0, 0), txt, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def draw_screen(flash: bool = False):
    """Render the solid color view with big time and tiny emoji."""
    bg = RED_FOCUS if mode == "focus" else GREEN_BREAK
    title = "POMODORO" if mode == "focus" else "BREAK"
    emoji = "🙂" if mode == "focus" else "☕"

    # optional flash (end-of-session micro celebration)
    if flash:
        draw.rectangle((0, 0, width, height), fill=WHITE)
        disp.image(image, rotation)
        time.sleep(0.08)

    # background
    draw.rectangle((0, 0, width, height), fill=bg)

    # title
    tw, th = text_size(title, font_title)
    draw.text(((width - tw) // 2, 6), title, font=font_title, fill=WHITE)

    # time
    t = fmt_time(remaining)
    tw2, th2 = text_size(t, font_time)
    draw.text(((width - tw2) // 2, (height - th2) // 2 - 6), t, font=font_time, fill=WHITE)

    # emoji under time
    ew, eh = text_size(emoji, font_emoji)
    draw.text(((width - ew) // 2, (height + th2) // 2 + 2), emoji, font=font_emoji, fill=WHITE)

    disp.image(image, rotation)

def handle_buttons():
    """Detect short/long presses for A/B."""
    global a_down_time, b_down_time, a_prev, b_prev, running

    a_now = read_button(buttonA)
    b_now = read_button(buttonB)
    now = time.time()

    # --- A: start/pause (short), reset (long)
    if a_now and not a_prev:
        a_down_time = now
    if not a_now and a_prev and a_down_time is not None:
        duration = now - a_down_time
        if duration >= LONG_SEC:
            reset_current()
        else:
            running = not running
        a_down_time = None

    # --- B: skip (short), backlight toggle (long)
    if b_now and not b_prev:
        b_down_time = now
    if not b_now and b_prev and b_down_time is not None:
        duration = now - b_down_time
        if duration >= LONG_SEC:
            toggle_backlight()
        else:
            skip_mode()
        b_down_time = None

    a_prev = a_now
    b_prev = b_now

def main():
    global last_tick
    draw_screen()

    while True:
        now = time.time()
        dt = now - last_tick
        last_tick = now

        handle_buttons()

        prev_mode = mode
        prev_remaining = remaining
        tick(dt)

        # micro-celebration flash if we just wrapped
        flash = (not running and prev_mode != mode and prev_remaining <= 0)

        draw_screen(flash=flash)
        time.sleep(0.05)  # ~20 FPS UI update / debounce

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
