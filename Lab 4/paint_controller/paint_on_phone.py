# MiniPiTFT joystick painter + APDS9960 color brush
# Output selectable: MiniPiTFT (SPI) or Phone (VNC window via Tkinter)

import time, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

import qwiic_joystick
import board, digitalio
import adafruit_rgb_display.st7789 as st7789
from adafruit_seesaw import seesaw as ss_mod, rotaryio as srotaryio, digitalio as sdio
from adafruit_apds9960.apds9960 import APDS9960

# ======= CHOOSE OUTPUT =======
USE_TFT   = False   # False → show in a Tkinter window (VNC on phone), True → MiniPiTFT
ROTATION  = 0

# ======= Canvas =======
W, H = 480, 270
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)

# ======= Display backends =======
disp = None
tk_root = None
canvas = None
_tk_img = None

def _init_tft():
    BAUDRATE = 64_000_000
    cs_pin = digitalio.DigitalInOut(board.D5)
    dc_pin = digitalio.DigitalInOut(board.D25)
    spi = board.SPI()
    d = st7789.ST7789(
        spi, cs=cs_pin, dc=dc_pin, rst=None, baudrate=BAUDRATE,
        width=135, height=240, x_offset=53, y_offset=40
    )
    d.image(img, ROTATION)
    return d

def _init_tk():
    import tkinter as tk
    from PIL import ImageTk
    root = tk.Tk()
    root.title("Pi Painter")
    SCALE = 2  # make it bigger for phone
    cvs = tk.Canvas(root, width=W*SCALE, height=H*SCALE, bg="black", highlightthickness=0)
    cvs.pack()
    return root, cvs, SCALE

if USE_TFT:
    disp = _init_tft()
else:
    tk_root, canvas, TK_SCALE = _init_tk()

def push_frame(pil_img=None):
    """Show current frame on the selected output."""
    global _tk_img
    pil_img = pil_img if pil_img is not None else img
    if USE_TFT:
        disp.image(pil_img, ROTATION)
    else:
        from PIL import ImageTk
        rotated = pil_img.rotate(ROTATION, expand=True)
        display_img = rotated.resize((W*TK_SCALE, H*TK_SCALE), Image.NEAREST)
        _tk_img = ImageTk.PhotoImage(display_img)
        canvas.create_image(0, 0, anchor="nw", image=_tk_img)
        tk_root.update_idletasks()
        tk_root.update()

# ======= Controls / sensors =======
js = qwiic_joystick.QwiicJoystick()
if not js.connected:
    print("Qwiic Joystick not found.", file=sys.stderr); sys.exit(1)
js.begin()

ss = ss_mod.Seesaw(board.I2C(), addr=0x36)
prod = (ss.get_version() >> 16) & 0xFFFF
print(f"Seesaw product: {prod}")
ss.pin_mode(24, ss.INPUT_PULLUP)
enc_button = sdio.DigitalIO(ss, 24)
encoder = srotaryio.IncrementalEncoder(ss)
last_position = encoder.position
enc_button._press_t = None

i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_color = True

# ======= State =======
x, y = W // 2, H // 2
brush = 4
palette = [(255,0,0),(0,255,0),(0,128,255),(255,255,0),(255,255,255)]
ci = 0
prev_js_btn = 1
isDrawing = False
auto_color = True
curr_color = (255, 255, 255)
last_color_read = 0
SAVE_PATH = "painting.png"

def clamp(v, lo, hi): return max(lo, min(hi, v))
def rot_vec(dx, dy, rot):
    r = rot % 360
    if r == 0:   return dx, dy
    if r == 90:  return dy, -dx
    if r == 180: return -dx, -dy
    if r == 270: return -dy, dx
    return dx, dy
def rgb_from_apds(r, g, b, c):
    if c <= 0: return (0,0,0)
    rn = int(255 * r / c); gn = int(255 * g / c); bn = int(255 * b / c)
    return (clamp(rn,0,255), clamp(gn,0,255), clamp(bn,0,255))
def lerp(a,b,t): return int(a + (b-a)*t)
def smooth_rgb(old, new, alpha=0.3):
    return (lerp(old[0],new[0],alpha), lerp(old[1],new[1],alpha), lerp(old[2],new[2],alpha))

# ---------- overlay helpers (works for both outputs) ----------
def overlay_text_block(base_img, text, box_alpha=180, seconds=4):
    max_chars = 44
    lines = []
    for para in text.split("\n"):
        lines += textwrap.wrap(para, width=max_chars) or [""]
    msg = "\n".join(lines[:8])

    over = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(over)
    pad = 6
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()
    # estimate box height
    box_h = 12 * (msg.count("\n") + 1) + pad*2 + 4
    box_y0 = H - box_h - 4
    d.rectangle((4, box_y0, W-4, H-4), fill=(0,0,0,box_alpha), outline=(255,255,255,180), width=1)
    d.multiline_text((8, box_y0 + pad), msg, fill=(255,255,255,255), font=font, spacing=2)

    composed = Image.alpha_composite(base_img.convert("RGBA"), over).convert("RGB")
    push_frame(composed)

    t0 = time.time()
    while time.time() - t0 < seconds:
        time.sleep(0.05)
    push_frame(base_img)

# ======= Main loop =======
try:
    while True:
        # Joystick movement
        jx, jy, js_btn = js.horizontal, js.vertical, js.button
        dead = 40
        raw_dx, raw_dy = jx-512, jy-512
        if abs(raw_dx) < dead: raw_dx = 0
        if abs(raw_dy) < dead: raw_dy = 0
        dx, dy = int(raw_dx/64.0), int(raw_dy/64.0)
        dx, dy = rot_vec(dx, dy, ROTATION)
        x = clamp(x + dx, 0, W-1)
        y = clamp(y + dy, 0, H-1)

        # Toggle draw on press edge
        if prev_js_btn == 1 and js_btn == 0:
            isDrawing = not isDrawing
            print("ON" if isDrawing else "OFF")
        prev_js_btn = js_btn

        # Encoder size
        pos = encoder.position
        if pos != last_position:
            diff = pos - last_position
            last_position = pos
            brush = clamp(brush + diff, 1, 30)
            print(f"Brush: {brush}")

        # Encoder button: short = palette, long = save
        if not enc_button.value and enc_button._press_t is None:
            enc_button._press_t = time.time()
        if enc_button.value and enc_button._press_t is not None:
            held = time.time() - enc_button._press_t
            enc_button._press_t = None
            if held > 0.7:
                img.save(SAVE_PATH, format="PNG")
                overlay_text_block(img.copy(), f"Saved: {SAVE_PATH}", seconds=2)
                print(f"Saved to {SAVE_PATH}")
            else:
                ci = (ci + 1) % len(palette)
                overlay_text_block(img.copy(), f"Color idx: {ci}", seconds=1)
                print(f"Color idx: {ci}")

        # APDS color (~20 Hz)
        now = time.time()
        if auto_color and (now - last_color_read) > 0.05 and apds.color_data_ready:
            r,g,b,c = apds.color_data
            curr_color = smooth_rgb(curr_color, rgb_from_apds(r,g,b,c), 0.35)
            last_color_read = now

        # Draw + push frame
        brush_color = curr_color if auto_color else palette[ci]
        if isDrawing:
            draw.ellipse((x - brush, y - brush, x + brush, y + brush), fill=brush_color)

        push_frame()
        time.sleep(0.016)

except KeyboardInterrupt:
    pass
