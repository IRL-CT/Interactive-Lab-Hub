# MiniPiTFT joystick painter + APDS9960 color brush
import time, sys
from PIL import Image, ImageDraw
import qwiic_joystick
import board, digitalio
import adafruit_rgb_display.st7789 as st7789

# Seesaw encoder
from adafruit_seesaw import seesaw as ss_mod, rotaryio as srotaryio, digitalio as sdio

# APDS9960 color sensor
from adafruit_apds9960.apds9960 import APDS9960

# ===== Display setup =====
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None
BAUDRATE = 64_000_000
spi = board.SPI()

disp = st7789.ST7789(
    spi, cs=cs_pin, dc=dc_pin, rst=reset_pin, baudrate=BAUDRATE,
    width=135, height=240, x_offset=53, y_offset=40
)

rotation = 90          # rotate on send
W, H = 240, 135        # draw in landscape

img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
disp.image(img, rotation)

# ===== Joystick =====
js = qwiic_joystick.QwiicJoystick()
if not js.connected:
    print("Qwiic Joystick not found.", file=sys.stderr); sys.exit(1)
js.begin()

# ===== Seesaw encoder (0x36) =====
ss = ss_mod.Seesaw(board.I2C(), addr=0x36)
prod = (ss.get_version() >> 16) & 0xFFFF
print(f"Seesaw product: {prod}")
ss.pin_mode(24, ss.INPUT_PULLUP)
enc_button = sdio.DigitalIO(ss, 24)
encoder = srotaryio.IncrementalEncoder(ss)
last_position = encoder.position

# ===== APDS9960 color =====
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_color = True

# --- state ---
x, y = W // 2, H // 2
brush = 4
palette = [(255,0,0),(0,255,0),(0,128,255),(255,255,0),(255,255,255)]
ci = 0

prev_js_btn = 1
isDrawing = False

# color control
auto_color = True            # start with sensor-driven color
curr_color = (255, 255, 255) # smoothed color
last_color_read = 0

def clamp(v, lo, hi): return max(lo, min(hi, v))

def rot_vec(dx, dy, rot):
    r = rot % 360
    if r == 0:   return dx, dy
    if r == 90:  return dy, -dx
    if r == 180: return -dx, -dy
    if r == 270: return -dy, dx
    return dx, dy

def rgb_from_apds(r, g, b, c):
    """Normalize sensor RGB by clear channel and clamp to 0..255."""
    if c <= 0:
        return (0, 0, 0)
    rn = int(255 * r / c)
    gn = int(255 * g / c)
    bn = int(255 * b / c)
    return (clamp(rn, 0, 255), clamp(gn, 0, 255), clamp(bn, 0, 255))

def lerp(a, b, t):
    return int(a + (b - a) * t)

def smooth_rgb(old, new, alpha=0.3):
    return (lerp(old[0], new[0], alpha),
            lerp(old[1], new[1], alpha),
            lerp(old[2], new[2], alpha))

try:
    while True:
        # ----- joystick movement -----
        jx = js.horizontal   # 0..1023
        jy = js.vertical
        js_btn = js.button   # 0 when pressed

        dead = 40
        raw_dx = jx - 512
        raw_dy = jy - 512
        if abs(raw_dx) < dead: raw_dx = 0
        if abs(raw_dy) < dead: raw_dy = 0

        sens = 64.0
        dx, dy = int(raw_dx / sens), int(raw_dy / sens)
        dx, dy = rot_vec(dx, dy, rotation)

        x = clamp(x + dx, 0, W - 1)
        y = clamp(y + dy, 0, H - 1)

        # JS button: toggle draw on press edge
        if prev_js_btn == 1 and js_btn == 0:
            isDrawing = not isDrawing
            print("🖌️ ON" if isDrawing else "✋ OFF")
        prev_js_btn = js_btn

        # ----- encoder brush size & color toggle -----
        pos = encoder.position
        if pos != last_position:
            diff = pos - last_position
            last_position = pos
            brush = clamp(brush + diff, 1, 30)
            print(f"Brush: {brush}")

        # encoder button: short = cycle manual color; long = toggle auto_color
        # detect press length
        static_press_t = getattr(enc_button, "_press_t", None)
        if not enc_button.value and static_press_t is None:   # pressed now
            enc_button._press_t = time.time()
        if enc_button.value and static_press_t is not None:   # released now
            held = time.time() - enc_button._press_t
            enc_button._press_t = None
            if held > 0.7:
                auto_color = not auto_color
                print(f"Auto color: {'ON' if auto_color else 'OFF'}")
            else:
                ci = (ci + 1) % len(palette)
                print(f"Color idx: {ci}")

        # ----- APDS9960 read (non-blocking-ish) -----
        now = time.time()
        if auto_color and (now - last_color_read) > 0.05:  # ~20 Hz
            # wait briefly for ready without stalling the frame
            if apds.color_data_ready:
                r, g, b, c = apds.color_data
                sensed = rgb_from_apds(r, g, b, c)
                curr_color = smooth_rgb(curr_color, sensed, 0.35)
                last_color_read = now

        # choose brush color
        brush_color = curr_color if auto_color else palette[ci]

        # ----- draw -----
        if isDrawing:
            draw.ellipse((x - brush, y - brush, x + brush, y + brush),
                         fill=brush_color)

        # push frame
        disp.image(img, rotation)
        time.sleep(0.016)  # ~60 FPS

except KeyboardInterrupt:
    pass
