import time
from datetime import datetime
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# ------------------- Config -------------------
WIDTH, HEIGHT = 135, 240
X_OFS, Y_OFS = 53, 40
BAUDRATE = 64_000_000

PIN_DC  = board.D25
PIN_RST = None
PIN_CS  = None
PIN_BL  = board.D22
PIN_BTN_A = board.D23
PIN_BTN_B = board.D24

VIEW_MODE_FILE = "/tmp/reminder_view_mode"
DEBOUNCE_SEC = 0.02
SAFE_PAD = 8
CARD_RAD = 16
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ------------------- Input -------------------
def prompt_user_for_reminders():
    print("\nEnter reminders (leave title empty to finish).")
    items = []
    while True:
        title = input("Title: ").strip()
        if title == "":
            break
        try:
            mins = int(input("Minutes from now (0-240): ").strip())
        except ValueError:
            print("Invalid minutes, try again.")
            continue
        mins = max(0, min(240, mins))
        items.append({"title": title, "mins_left": mins})
    if not items:
        items = [
            {"title": "Meeting with TA", "mins_left": 45},
            {"title": "Call Mom",       "mins_left": 10},
            {"title": "Submit Lab 2",   "mins_left": 55},
        ]
        print("No input given. Using defaults.")
    return items

reminders = prompt_user_for_reminders()
current_idx = 0

# ------------------- Helpers -------------------
def ensure_one_reminder():
    global reminders, current_idx
    if not reminders:
        reminders = [{"title": "Reminder", "mins_left": 30}]
        current_idx = 0

def read_view_mode():
    try:
        with open(VIEW_MODE_FILE, "r") as f:
            t = f.read().strip()
            return t if t in ("detail", "minimal") else "detail"
    except FileNotFoundError:
        return "detail"

def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def autosize_font(text, max_w, max_h, max_size, min_size=8):
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    size = max_size
    while size >= min_size:
        f = load_font(size)
        bbox = draw.textbbox((0,0), text, font=f)
        w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
        if w <= max_w and h <= max_h:
            return f
        size -= 1
    return load_font(min_size)

def wrap_text(draw, text, font, max_w, max_lines=2, ellipsize=True):
    words, lines, cur, i = text.split(), [], "", 0
    while i < len(words) and len(lines) < max_lines:
        w = words[i]
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test; i += 1
        else:
            if cur:
                lines.append(cur); cur = ""
                if len(lines) == max_lines - 1:
                    cur = " ".join(words[i:]); break
            else:
                cur = w; i += 1; break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if ellipsize and len(lines) == max_lines:
        last = lines[-1]
        while draw.textlength(last + "…", font=font) > max_w and len(last) > 0:
            last = last[:-1]
        if last != lines[-1]:
            lines[-1] = last + "…"
        elif i < len(words) and draw.textlength(last + "…", font=font) <= max_w:
            lines[-1] = last + "…"
    return lines

# ------------------- Display init -------------------
spi = board.SPI()
display = st7789.ST7789(
    spi,
    cs=PIN_CS,
    dc=digitalio.DigitalInOut(PIN_DC),
    rst=PIN_RST,
    baudrate=BAUDRATE,
    width=WIDTH,
    height=HEIGHT,
    x_offset=X_OFS,
    y_offset=Y_OFS,
)

backlight = digitalio.DigitalInOut(PIN_BL)
backlight.switch_to_output(value=True)

buttonA = digitalio.DigitalInOut(PIN_BTN_A)
buttonB = digitalio.DigitalInOut(PIN_BTN_B)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

def read_button(btn): 
    return (btn.value == False)

# ------------------- Drawing -------------------
def v_gradient(img, top_rgb, bottom_rgb):
    d = ImageDraw.Draw(img)
    r1,g1,b1 = top_rgb; r2,g2,b2 = bottom_rgb
    for y in range(HEIGHT):
        t = y / max(1, HEIGHT-1)
        r = int(r1 + (r2-r1)*t); g = int(g1 + (g2-g1)*t); b = int(b1 + (b2-b1)*t)
        d.line((0,y,WIDTH,y), fill=(r,g,b))

bg_cache = {"detail": None, "minimal": None}
def prepare_background(mode):
    if bg_cache[mode] is not None: 
        return bg_cache[mode]
    bg = Image.new("RGB", (WIDTH, HEIGHT))
    if mode == "detail":
        v_gradient(bg, (10,60,180), (30,100,220))  # blue gradient
    else:
        v_gradient(bg, (20,20,30), (10,10,15))
    bg_cache[mode] = bg
    return bg

def rounded_card(d, xy, radius=CARD_RAD, fill=(240,248,255), outline=(180,200,220), width=1):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def progress_bar(d, x, y, w, h, pct, fg=(40,120,220), brd=(20,40,80), bg=(200,220,255)):
    r = min(h//2, 6)
    d.rounded_rectangle((x, y, x+w, y+h), radius=r, fill=bg, outline=brd, width=1)
    fw = int(max(0, min(1, pct)) * (w-2))
    if fw > 0:
        d.rounded_rectangle((x+1, y+1, x+1+fw, y+h-1), radius=r-1 if r>1 else r, fill=fg)

def draw_time_and_date(d, y):
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%a, %b %d")
    f_time = load_font(36)
    f_date = load_font(14)
    bbox = d.textbbox((0,0), time_str, font=f_time)
    w,h = bbox[2]-bbox[0], bbox[3]-bbox[1]
    d.text(((WIDTH-w)//2, y), time_str, font=f_time, fill=(255,255,255))
    dw = d.textlength(date_str, font=f_date)
    d.text(((WIDTH-dw)//2, y+h+4), date_str, font=f_date, fill=(230,240,255))
    return y + h + 20

def footer_hint(d):
    hint = "A=Prev  B=Next  A+B=Delete"
    f = load_font(11)
    tw = d.textlength(hint, font=f)
    x = (WIDTH - tw)//2
    y = HEIGHT - SAFE_PAD - 12
    d.text((x, y), hint, font=f, fill=(255,255,255))

def draw_detail_screen(reminders, idx):
    base = prepare_background("detail").copy()
    d = ImageDraw.Draw(base)
    d.text((SAFE_PAD, SAFE_PAD-2), "Reminder Clock", font=load_font(12), fill=(255,255,255))
    y0 = draw_time_and_date(d, SAFE_PAD+20) + 8
    cx0, cy0 = SAFE_PAD, y0
    cx1, cy1 = WIDTH - SAFE_PAD, HEIGHT - SAFE_PAD - 28
    rounded_card(d, (cx0, cy0, cx1, cy1))
    in_pad = 10
    ix0, iy0 = cx0 + in_pad, cy0 + in_pad
    ix1, iy1 = cx1 - in_pad, cy1 - in_pad
    inner_w = max(0, ix1 - ix0)
    title_f = load_font(16); info_f = load_font(12)
    reminder = reminders[idx] if reminders else None
    if reminder:
        title = reminder["title"]; mins = reminder["mins_left"]
        lines = wrap_text(d, title, title_f, inner_w, max_lines=2, ellipsize=True)
        y = iy0
        for ln in lines:
            d.text((ix0, y), ln, font=title_f, fill=(20,30,80))
            lh = d.textbbox((0,0), ln, font=title_f)[3] - d.textbbox((0,0), ln, font=title_f)[1]
            y += lh + 2
        d.text((ix0, y+6), f"{mins:02d} min remaining", font=info_f, fill=(40,80,160))
        progress_bar(d, ix0, y+24, inner_w, 10, max(0.0, min(1.0, 1.0 - mins/60.0)))
    else:
        d.text((ix0, iy0), "No reminders", font=title_f, fill=(50,50,50))
    footer_hint(d)
    return base

def draw_minimal_screen():
    base = prepare_background("minimal").copy()
    d = ImageDraw.Draw(base)
    draw_time_and_date(d, (HEIGHT//2) - 28)
    return base

# ------------------- Main loop -------------------
print("A=Prev | B=Next | A+B=Delete")
last_tick = time.monotonic()
countdown_accum = 0.0

try:
    while True:
        a = read_button(buttonA)
        b = read_button(buttonB)
        backlight.value = not (a and b)

        if a and not b:
            while read_button(buttonA): time.sleep(DEBOUNCE_SEC)
            if reminders: current_idx = (current_idx - 1) % len(reminders)
            time.sleep(0.05)

        if b and not a:
            while read_button(buttonB): time.sleep(DEBOUNCE_SEC)
            if reminders: current_idx = (current_idx + 1) % len(reminders)
            time.sleep(0.05)

        if a and b:
            while read_button(buttonA) or read_button(buttonB): time.sleep(DEBOUNCE_SEC)
            if reminders:
                del reminders[current_idx]
                current_idx = (current_idx % len(reminders)) if reminders else 0
            ensure_one_reminder()
            time.sleep(0.05)

        dt = time.monotonic() - last_tick
        last_tick = time.monotonic()
        countdown_accum += dt
        if countdown_accum >= 60.0:
            countdown_accum = 0.0
            if reminders:
                reminders[current_idx]["mins_left"] = max(0, reminders[current_idx]["mins_left"] - 1)

        mode = read_view_mode()
        frame = draw_detail_screen(reminders, current_idx) if mode=="detail" else draw_minimal_screen()
        display.image(frame)
        time.sleep(0.02)

except KeyboardInterrupt:
    try: backlight.value = False
    except Exception: pass
    print("\nBye.")
