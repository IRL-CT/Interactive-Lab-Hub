# MiniPiTFT joystick painter + APDS9960 color brush
import time, sys
from PIL import Image, ImageDraw
import qwiic_joystick
import board, digitalio,busio
import adafruit_rgb_display.st7789 as st7789

# Seesaw encoder
from adafruit_seesaw import seesaw as ss_mod, rotaryio as srotaryio, digitalio as sdio

# APDS9960 color sensor
from adafruit_apds9960.apds9960 import APDS9960

# ===== MPR121 touch sensor =====
import adafruit_mpr121

from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
# ===== touch sensor setup =====
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)
sensor = LSM6DS3(i2c)

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

background_color = (0, 0, 0, 255) # black
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
brush_type = "circle" 

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
        # ----- accelerometer read -----
        accel_x, accel_y, accel_z = sensor.acceleration

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
            print("ON" if isDrawing else "OFF")
        prev_js_btn = js_btn

        # ----- encoder brush size & color toggle -----
        pos = encoder.position
        if pos != last_position:
            diff = pos - last_position
            last_position = pos
            brush = clamp(brush + diff, 1, 30)
            print(f"Brush: {brush}")

        #clean when the accelerometer is tilted forward 
        if accel_y < 0.0: 
            img.paste((0,0,0), [0,0,img.size[0],img.size[1]])
            print("Canvas cleared")
            time.sleep(0.5)  # debounce
    
        # ----- APDS9960 read (non-blocking-ish) -----
        # now = time.time()
        # if auto_color and (now - last_color_read) > 0.05:  # ~20 Hz
            # wait briefly for ready without stalling the frame
        if apds.color_data_ready:
            # print("reading color")
            r, g, b, c = apds.color_data
            sensed = rgb_from_apds(r, g, b, c)
            curr_color = smooth_rgb(curr_color, sensed, 0.35)
            # last_color_read = now

        # choose brush color
        brush_color = curr_color if auto_color else brush_color
        
        brush_coordinates = [x - brush, y - brush, x + brush, y + brush]
        #change brush choices
        # draw_options = ["erase", "clear", "save", "draw", "rectangle", "circle", "line", "fill", "triangle", "polygon", "ellipse"]
        # drawing_methods = {
        #     "clear": lambda: img.paste(background_color, [0,0,img.size[0],img.size[1]]),
        #     "save": lambda: img.save(f"my_drawing_{int(time.time())}.png"),
        # }
        for i in range(12):
            if mpr121[i].value:
                # print(f"Option selected: {i]}")
                if i == 0:
                    #this is erase
                    print("ERASING")
                    auto_color = False
                    brush_color = background_color
                
                if i == 3:
                    print("DRAWING")
                    auto_color = True    
                    brush_type = "circle" if brush_type == "rectangle" else "rectangle"
                    print(f"Brush type: {brush_type}")            
                    
                if i == 5:
                    #this is save
                    img.save(f"drawing/my_drawing_{int(time.time())}.png")
                    print(f"Image saved to drawing/my_drawing_{int(time.time())}.png")

                if i == 7:
                    background_color = brush_color
                    img.paste(background_color, [0,0,img.size[0],img.size[1]])
                    print("Background color set")

                time.sleep(0.3)  # debounce

        # ----- draw -----
        if isDrawing:
            if brush_type == "rectangle":
                draw.rectangle(brush_coordinates, outline= brush_color, width=brush)
            if brush_type == "circle":
                draw.ellipse((x - brush, y - brush, x + brush, y + brush),
                            fill=brush_color)

        # push frame
        disp.image(img, rotation)
        time.sleep(0.016)  # ~60 FPS

except KeyboardInterrupt:
    pass