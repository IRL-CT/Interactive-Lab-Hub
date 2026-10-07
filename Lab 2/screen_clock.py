import json
import math
import random
import time
from pathlib import Path

import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# Mini PiTFT hardware
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
spi = board.SPI()
disp = st7789.ST7789(
    spi, cs=cs_pin, dc=dc_pin, rst=None, baudrate=64000000,
    width=135, height=240, x_offset=53, y_offset=40,
)
width, height = disp.height, disp.width
rotation = 90
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

WAX_COLORS = [
    (227, 143, 157),  # pink
    (234, 164, 111),  # apricot
    (154, 192, 224),  # sky blue star
    (238, 206, 125),  # yellow daisy
    (135, 188, 177),  # mint bow
    (184, 144, 214),  # purple moon
]
sessions_file = Path(__file__).with_name("focus_sessions.json")
try:
    saved_sessions = json.loads(sessions_file.read_text())
    if not isinstance(saved_sessions, list):
        saved_sessions = []
except (FileNotFoundError, json.JSONDecodeError):
    saved_sessions = []

# Older versions saved only a duration. Give those seals a color too.
sessions = []
for item in saved_sessions:
    if isinstance(item, (int, float)):
        sessions.append({"duration": float(item), "color": list(WAX_COLORS[len(sessions) % len(WAX_COLORS)])})
    elif isinstance(item, dict) and isinstance(item.get("duration"), (int, float)):
        color = item.get("color")
        if not isinstance(color, list) or len(color) != 3:
            color = list(WAX_COLORS[len(sessions) % len(WAX_COLORS)])
        sessions.append({"duration": float(item["duration"]), "color": color})
if sessions != saved_sessions:
    sessions_file.write_text(json.dumps(sessions, indent=2))


def format_duration(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"


def draw_flame(cx, tip_y, blue=False, size=1):
    # The larger candle flickers gently; its flame stays small.
    sway = math.sin(time.monotonic() * 7 + cx * 0.23) * 1.2 * size
    flame_width = 2.8 * size + math.sin(time.monotonic() * 11) * 0.5 * size
    outer = (70, 158, 246) if blue else (255, 161, 67)
    inner = (180, 226, 255) if blue else (255, 230, 144)
    draw.polygon([(cx + sway, tip_y),
                  (cx - flame_width, tip_y + 8 * size),
                  (cx, tip_y + 11 * size),
                  (cx + flame_width, tip_y + 8 * size)], fill=outer)
    draw.ellipse((cx - size + sway / 2, tip_y + 6 * size,
                  cx + size + sway / 2, tip_y + 9 * size), fill=inner)


def draw_focus_mark():
    if focus_active:
        # Static blue flame in the top-right corner, only on clock/detail.
        draw.polygon([(221, 6), (217, 14), (221, 19), (225, 14)],
                     fill=(70, 158, 246))
        draw.ellipse((220, 12, 222, 17), fill=(180, 226, 255))


def seal_radius(duration):
    # A ten-second session is small; a ten-minute session is almost twice as wide.
    return min(21, 10 + int(math.sqrt(max(0, duration) / 5)))

# Four transparent watercolor stickers in each 2 x 2 image sheet.
def split_stickers(filename):
    sheet = Image.open(Path(__file__).with_name(filename)).convert("RGBA")
    middle_x, middle_y = sheet.width // 2, sheet.height // 2
    pieces = []
    for left, top, right, bottom in ((0, 0, middle_x, middle_y),
                                    (middle_x, 0, sheet.width, middle_y),
                                    (0, middle_y, middle_x, sheet.height),
                                    (middle_x, middle_y, sheet.width, sheet.height)):
        piece = sheet.crop((left, top, right, bottom))
        bounds = piece.getchannel("A").getbbox()
        pieces.append(piece.crop(bounds) if bounds else piece)
    return pieces

CANDLES = split_stickers("candle_sheet_journal.png")
SEALS = split_stickers("seal_sheet_journal.png")[:2] + split_stickers("seal_sheet_extra_journal.png")
TABLE_OVERLAY = Image.open(Path(__file__).with_name("journal_table_overlay.png")).convert("RGBA")
room_sheet = Image.open(Path(__file__).with_name("room_backgrounds_journal.jpg")).convert("RGB")
ROOM_BACKGROUNDS = []
for row in range(2):
    for col in range(2):
        scene = room_sheet.crop((col * 240, row * 135, (col + 1) * 240, (row + 1) * 135))
        paper = Image.new("RGB", (width, height), (250, 247, 241))
        ROOM_BACKGROUNDS.append(Image.blend(scene, paper, 0.29 if col == 0 else 0.49))

def draw_scene():
    hour = time.localtime().tm_hour
    nighttime = hour < 7 or hour >= 18
    index = (0 if room == "study" else 2) + int(nighttime)
    image.paste(ROOM_BACKGROUNDS[index], (0, 0))
    image.paste(TABLE_OVERLAY, (0, 0), TABLE_OVERLAY)

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS
STICKER_CACHE = {}

def paste_sticker(piece, center_x, center_y, target_width, target_height):
    size = (max(1, int(target_width)), max(1, int(target_height)))
    key = (id(piece), size)
    if key not in STICKER_CACHE:
        STICKER_CACHE[key] = piece.resize(size, RESAMPLE)
    resized = STICKER_CACHE[key]
    image.paste(resized, (round(center_x - size[0] / 2), round(center_y - size[1] / 2)), resized)

def draw_candle(cx, base_y, body_height, lit=False, blue=False, melted=False, scale=1):
    # Keep the hand-drawn wax body; draw the changing flame separately.
    if melted:
        piece = CANDLES[3]
        target_height = max(13, body_height + 3)
    else:
        piece = CANDLES[0]
        target_height = max(15, body_height + (2 if scale == 1 else 9))
    target_width = min(17 if scale == 1 else 43,
                       max(9, round(target_height * piece.width / piece.height)))
    paste_sticker(piece, cx, base_y - target_height / 2, target_width, target_height)
    if lit:
        flame_size = 1 if scale == 1 else 2
        draw_flame(cx, base_y - target_height - (8 if scale == 1 else 14),
                   blue=blue, size=flame_size)

def draw_wax_seal(cx, cy, radius, color, seed):
    style = min(range(len(WAX_COLORS)),
                key=lambda i: sum((int(color[j]) - WAX_COLORS[i][j]) ** 2 for j in range(3)))
    diameter = 2 * radius
    paste_sticker(SEALS[style], cx, cy, diameter, diameter)

page = "clock"
room = "study"
a_long_handled = False
focus_active = False
focus_started_at = None
b_pressed_at = None
a_pressed_at = None
b_long_handled = False
combo_handled = False
popup_until = 0
popup_duration = 0
LONG_PRESS_SECONDS = 0.8

while True:
    now = time.monotonic()
    a_pressed = not buttonA.value
    b_pressed = not buttonB.value

    if a_pressed and b_pressed:
        if not combo_handled:
            page = "seals"
            popup_until = 0
        combo_handled = True
        a_pressed_at = None
        b_pressed_at = None
        a_long_handled = True
        b_long_handled = True

    elif b_pressed:
        if not combo_handled:
            a_pressed_at = None
            if b_pressed_at is None and not b_long_handled:
                b_pressed_at = now
            elif b_pressed_at is not None and not b_long_handled:
                if now - b_pressed_at >= LONG_PRESS_SECONDS:
                    focus_active = not focus_active
                    b_long_handled = True
                    page = "focus"
                    if focus_active:
                        focus_started_at = now
                        popup_until = 0
                    else:
                        duration = max(0, now - focus_started_at)
                        sessions.append({
                            "duration": round(duration, 1),
                            "color": list(WAX_COLORS[len(sessions) % len(WAX_COLORS)]),
                        })
                        sessions_file.write_text(json.dumps(sessions, indent=2))
                        focus_started_at = None
                        popup_duration = duration
                        popup_until = now + 2.5

    elif a_pressed:
        if not combo_handled:
            if a_pressed_at is None and not a_long_handled:
                a_pressed_at = now
            elif a_pressed_at is not None and not a_long_handled:
                if now - a_pressed_at >= LONG_PRESS_SECONDS:
                    room = "bedroom" if room == "study" else "study"
                    a_long_handled = True

    else:
        if not combo_handled:
            if b_pressed_at is not None and not b_long_handled:
                page = "clock" if page == "focus" else "focus"
            elif a_pressed_at is not None and not a_long_handled:
                page = "detail" if page == "clock" else "clock"
        b_pressed_at = None
        a_pressed_at = None
        a_long_handled = False
        b_long_handled = False
        combo_handled = False

    if page == "seals":
        draw.rectangle((0, 0, width, height), fill=(250, 247, 241))
    else:
        draw_scene()

    if page == "clock":
        draw.text((9, 5), room.title() + " candle clock", font=small_font, fill=(100, 77, 75))
        draw.text((155, 5), time.strftime("%H:%M"), font=small_font,
                  fill=(107, 93, 92))
        hour = time.localtime().tm_hour
        minute = time.localtime().tm_min
        current = hour // 2
        burn_step = min(5, ((hour % 2) * 60 + minute) // 20)
        for index in range(12):
            cx = 13 + index * 19
            if index < current:
                draw_candle(cx, 99, 10, melted=True)
            elif index == current:
                draw_candle(cx, 99, 39 - burn_step * 5,
                            lit=True, blue=False)
            else:
                draw_candle(cx, 99, 35)
        draw.text((9, 116), "A: zoom  B: focus  A+B: seals", font=small_font,
                  fill=(118, 106, 105))
        draw_focus_mark()

    elif page == "detail":
        draw.text((9, 6), "Current candle", font=font, fill=(100, 77, 75))
        localtime = time.localtime()
        burn_step = min(5, ((localtime.tm_hour % 2) * 60 + localtime.tm_min) // 20)
        draw_candle(175, 99, 49 - burn_step * 7, lit=True, blue=False, scale=2)
        draw.text((10, 53), time.strftime("%H:%M"), font=font,
                  fill=(94, 77, 76))
        draw.text((10, 110), "A: back", font=small_font, fill=(118, 106, 105))
        draw_focus_mark()

    elif page == "focus":
        draw.text((9, 6), "Focus", font=font, fill=(100, 77, 75))
        elapsed = now - focus_started_at if focus_active else 0
        burn_step = min(5, int(elapsed // 1200))
        draw_candle(177, 99, 49 - burn_step * 7,
                    lit=focus_active, blue=focus_active, scale=2)
        if focus_active:
            draw.text((10, 50), format_duration(now - focus_started_at), font=font,
                      fill=(68, 131, 171))
            draw.text((10, 111), "Hold B: end", font=small_font,
                      fill=(118, 106, 105))
        else:
            draw.text((10, 50), "Ready", font=font, fill=(94, 77, 76))
            draw.text((10, 111), "Hold B: start", font=small_font,
                      fill=(118, 106, 105))

    elif page == "seals":
        draw.text((9, 4), "Focus memory", font=font, fill=(100, 77, 75))
        if not sessions:
            draw.text((20, 66), "No seals yet", font=small_font,
                      fill=(107, 93, 92))
        else:
            for index, session in enumerate(sessions[-6:]):
                cx = 43 + (index % 3) * 77
                cy = 45 + (index // 3) * 53
                duration = session["duration"]
                draw_wax_seal(cx, cy, seal_radius(duration),
                              session["color"], seed=len(sessions)-6+index)
                draw.text((cx-19, cy+21), format_duration(duration),
                          font=small_font, fill=(95, 80, 80))

    if now < popup_until:
        draw.rectangle((25, 35, 215, 101), fill=(255, 251, 246),
                       outline=(213, 150, 154), width=2)
        draw.text((39, 46), "Session complete", font=small_font,
                  fill=(111, 75, 81))
        draw.text((77, 68), format_duration(popup_duration), font=font,
                  fill=(94, 77, 76))

    disp.image(image, rotation)
    time.sleep(0.05)
