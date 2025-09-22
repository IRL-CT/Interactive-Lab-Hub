# pomodoro_pitft.py
# Mini-PiTFT (ST7789 240x135, x/y offsets 53/40)
# Buttons:
#   A (GPIO23): short = start/pause, long(≥1.2s) = reset
#   B (GPIO24): short = skip focus/break, long(≥1.2s) = cycle theme (Normal↔Pink), very long(≥3s) = backlight on/off
#
# Focus: PNG background (images/focus.png)
# Break: animated GIF (images/break.gif)
# Visible themes: progress bar accent + title/time colors (no banner, no translucent panel).

import os
import time
import random
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import adafruit_rgb_display.st7789 as st7789

# ---------------------------
# Display setup
# ---------------------------
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
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

HEIGHT = disp.width    # 135
WIDTH  = disp.height   # 240
ROTATION = 90

canvas = Image.new("RGB", (WIDTH, HEIGHT))
draw = ImageDraw.Draw(canvas)

# Backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)
backlight_on = True

# Buttons
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

def pressed(btn) -> bool:
    return btn.value is False

# ---------------------------
# Assets
# ---------------------------
FOCUS_IMG_PATH = "images/focus.png"
BREAK_GIF_PATH = "images/break.gif"

# ---------------------------
# Fonts & colors
# ---------------------------
def load_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()

font_title = load_font(22)
font_time  = load_font(72)
font_msg   = load_font(28)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED_FALLBACK   = (226, 61, 61)
GREEN_FALLBACK = (49, 184, 106)
PINK = (255, 105, 180)

# --- Two themes only: Normal & Pink ---
THEMES = [
    {
        "name": "Normal",
        "accent": (255, 184, 108),
        "confetti": [(255,184,108),(181,234,215),(255,218,185),(255,155,170)],
        "title_focus": WHITE,
        "text_focus":  WHITE,
        "title_break": BLACK,
        "text_break":  BLACK,
    },
    {
        "name": "Pink",
        "accent": (255, 160, 200),
        "confetti": [(255,160,200),(255,105,180),(255,200,220),(255,170,210)],
        "title_focus": PINK,
        "text_focus":  PINK,
        "title_break": PINK,
        "text_break":  PINK,
    },
]
theme_idx = 0
def T(key): return THEMES[theme_idx][key]
def theme_name(): return THEMES[theme_idx]["name"]

# ---------------------------
# Helpers
# ---------------------------
def cover_fit(img: Image.Image, tw: int, th: int) -> Image.Image:
    w, h = img.size
    if w * th < tw * h:
        nw, nh = tw, int(h * tw / w)
    else:
        nh, nw = th, int(w * th / h)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top  = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))

def text_size(txt: str, font: ImageFont.FreeTypeFont):
    bbox = draw.textbbox((0, 0), txt, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def draw_text_with_shadow(x, y, txt, font, fill, shadow=(0,0,0), offset=2):
    draw.text((x+offset, y+offset), txt, font=font, fill=shadow)
    draw.text((x, y), txt, font=font, fill=fill)

# Toast
toast_text = None
toast_until = 0.0
def show_toast(msg: str, seconds: float = 1.2):
    global toast_text, toast_until
    toast_text = msg
    toast_until = time.time() + seconds

def draw_toast(now: float):
    if not toast_text or now > toast_until:
        return
    bar_h = 24
    draw.rectangle((0, HEIGHT - bar_h, WIDTH, HEIGHT), fill=(0,0,0))
    tw, th = text_size(toast_text, font_title)
    draw.text(((WIDTH - tw)//2, HEIGHT - bar_h + (bar_h - th)//2),
              toast_text, font=font_title, fill=WHITE)

# ---------------------------
# Load assets
# ---------------------------
focus_bg = None
break_frames, break_durations = [], []
gif_total_frames = 0

if os.path.exists(FOCUS_IMG_PATH):
    try:
        tmp = Image.open(FOCUS_IMG_PATH).convert("RGB")
        focus_bg = cover_fit(tmp, WIDTH, HEIGHT)
    except Exception:
        focus_bg = None

if os.path.exists(BREAK_GIF_PATH):
    try:
        gif = Image.open(BREAK_GIF_PATH)
        for frame in ImageSequence.Iterator(gif):
            fr = frame.convert("RGB")
            fr = cover_fit(fr, WIDTH, HEIGHT)
            break_frames.append(fr)
            dur = frame.info.get("duration", 100)
            break_durations.append(max(20, int(dur)))
        gif_total_frames = len(break_frames)
    except Exception:
        break_frames, break_durations, gif_total_frames = [], [], 0

# ---------------------------
# Pomodoro state
# ---------------------------
FOCUS_SECS = 25 * 60
BREAK_SECS = 5 * 60
mode = "focus"
running = False
remaining = FOCUS_SECS
last_tick = time.time()

# Button state
a_down = None
b_down = None
a_prev = False
b_prev = False

# GIF state
gif_idx = 0
next_gif_time = time.time()

def fmt_time(secs: int) -> str:
    secs = max(0, int(secs))
    return f"{secs//60:02d}:{secs%60:02d}"

def total_secs_for_mode() -> int:
    return FOCUS_SECS if mode == "focus" else BREAK_SECS

def reset_session():
    global remaining, running
    remaining = total_secs_for_mode()
    running = False

def skip_session():
    global mode, remaining, running, gif_idx
    mode = "break" if mode == "focus" else "focus"
    remaining = total_secs_for_mode()
    running = False
    gif_idx = 0

def toggle_backlight():
    global backlight_on
    backlight_on = not backlight_on
    backlight.value = backlight_on
    show_toast("Backlight: ON" if backlight_on else "Backlight: OFF")

def cycle_theme():
    global theme_idx
    theme_idx = (theme_idx + 1) % len(THEMES)
    show_toast(f"Theme: {theme_name()}")

def tick_timer(dt: float) -> bool:
    global remaining, mode, running, gif_idx
    if not running:
        return False
    remaining -= dt
    if remaining <= 0:
        mode = "break" if mode == "focus" else "focus"
        remaining = total_secs_for_mode()
        running = False
        gif_idx = 0
        return True
    return False

# ---------------------------
# Drawing
# ---------------------------
PROG_H = 6
PROG_Y = 0

def draw_progress_bar():
    frac = 1.0 - (remaining / float(total_secs_for_mode()))
    frac = max(0.0, min(1.0, frac))
    draw.rectangle((0, PROG_Y, WIDTH, PROG_Y + PROG_H), fill=(0,0,0))
    w = int(WIDTH * frac)
    if w > 0:
        draw.rectangle((0, PROG_Y, w, PROG_Y + PROG_H), fill=T("accent"))

def draw_focus():
    if focus_bg:
        canvas.paste(focus_bg)
    else:
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=RED_FALLBACK)
    draw_progress_bar()
    title = "POMODORO"
    tw, th = text_size(title, font_title)
    draw_text_with_shadow((WIDTH - tw)//2, 8, title, font_title, T("title_focus"))
    draw_text_with_shadow((WIDTH - text_size(fmt_time(remaining), font_time)[0])//2,
                          HEIGHT//2 - th, fmt_time(remaining), font_time, T("text_focus"))

def draw_break(now: float):
    global gif_idx, next_gif_time
    if gif_total_frames > 0:
        if now >= next_gif_time:
            dur_ms = break_durations[gif_idx]
            next_gif_time = now + (dur_ms / 1000.0)
            gif_idx = (gif_idx + 1) % gif_total_frames
        canvas.paste(break_frames[gif_idx])
    else:
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=GREEN_FALLBACK)
    draw_progress_bar()
    title = "BREAK"
    tw, th = text_size(title, font_title)
    draw_text_with_shadow((WIDTH - tw)//2, 8, title, font_title, T("title_break"))
    draw_text_with_shadow((WIDTH - text_size(fmt_time(remaining), font_time)[0])//2,
                          HEIGHT//2 - th, fmt_time(remaining), font_time, T("text_break"))

def micro_celebration():
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,140))
    base = canvas.convert("RGBA")
    base.alpha_composite(overlay)
    for _ in range(7):
        frame = base.copy()
        d = ImageDraw.Draw(frame)
        for _i in range(28):
            r = random.randint(2, 5)
            x = random.randint(0, WIDTH-1)
            y = random.randint(0, HEIGHT-1)
            color = random.choice(T("confetti"))
            d.ellipse((x-r, y-r, x+r, y+r), fill=color)
        msg = "Nice!"
        mw, mh = d.textbbox((0,0), msg, font=font_msg)[2:]
        cx, cy = WIDTH//2, HEIGHT//2
        d.text((cx - mw//2, cy - mh//2), msg, font=font_msg, fill=(255,255,255))
        disp.image(frame.convert("RGB"), ROTATION)
        time.sleep(0.07)

# ---------------------------
# Input handling
# ---------------------------
def handle_buttons():
    global a_down, b_down, a_prev, b_prev, running
    now = time.time()

    a_now = pressed(buttonA)
    b_now = pressed(buttonB)

    if a_now and not a_prev:
        a_down = now
    if not a_now and a_prev and a_down is not None:
        dur = now - a_down
        if dur >= 1.2:
            reset_session()
        else:
            running = not running
        a_down = None

    if b_now and not b_prev:
        b_down = now
    if not b_now and b_prev and b_down is not None:
        dur = now - b_down
        if dur >= 3.0:
            toggle_backlight()
        elif dur >= 1.2:
            cycle_theme()
        else:
            skip_session()
        b_down = None

    a_prev = a_now
    b_prev = b_now

# ---------------------------
# Main
# ---------------------------
def main():
    global last_tick
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))
    disp.image(canvas, ROTATION)

    while True:
        now = time.time()
        dt = now - last_tick
        last_tick = now

        handle_buttons()
        wrapped = tick_timer(dt)

        if mode == "focus":
            draw_focus()
        else:
            draw_break(now)

        draw_toast(now)
        disp.image(canvas, ROTATION)

        if wrapped:
            micro_celebration()

        time.sleep(0.02)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
