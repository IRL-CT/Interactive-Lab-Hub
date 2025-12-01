# -*- coding: utf-8 -*-
import time
import board, busio, digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

# ==== I2C devices ====
import adafruit_apds9960.apds9960 as apds_lib
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
import adafruit_mpr121
import adafruit_pcf8574
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw import rotaryio

# 可选：SparkFun Qwiic Button
try:
    import qwiic_button
    HAS_QWIIC_BTN = True
except Exception:
    HAS_QWIIC_BTN = False

# ---------- 显示屏参数 ----------
# 目标：逻辑尺寸变为 240x135。若运行后打印仍是 135x240，把 270 改为 90 再试。
ROTATION = 270
X_OFFSET, Y_OFFSET = 53, 40     # 若有黑边/偏移可改 0,0 试试
BAUDRATE = 64_000_000

# ---------- ST7789 初始化（240x135 小屏的常规做法） ----------
spi = board.SPI()
dc_pin    = digitalio.DigitalInOut(board.D25)
reset_pin = None

# 注意：小屏原生显存为 135x240，旋转后才得到 240x135 的逻辑尺寸
disp = st7789.ST7789(
    spi,
    cs=None,                   # 交给内核管理 CE0，避免 "GPIO busy"
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,                 # 原生宽高：135x240（不要写 240x135）
    height=240,
    x_offset=X_OFFSET,
    y_offset=Y_OFFSET,
    rotation=ROTATION,         # 期望使 disp.width=240, disp.height=135
)

# —— 用驱动返回的逻辑尺寸创建画布（至关重要） ——
WIDTH, HEIGHT = disp.width, disp.height
print("Display logical size:", WIDTH, HEIGHT)  # 期望 240 135
image = Image.new("RGB", (WIDTH, HEIGHT))
print("PIL image size:", image.size)
draw  = ImageDraw.Draw(image)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except Exception:
    font = ImageFont.load_default()

# ---------- I2C 总线 ----------
i2c = busio.I2C(board.SCL, board.SDA)

# 传感器初始化（按你的 i2cdetect: 0x39, 0x6A, 0x5A, 0x20, 0x36, 0x6F/0x40）
apds = apds_lib.APDS9960(i2c)
apds.enable_proximity = True
apds.enable_gesture   = True
apds.enable_color     = True

imu  = LSM6DS3(i2c)
mpr  = adafruit_mpr121.MPR121(i2c)

pcf  = adafruit_pcf8574.PCF8574(i2c)
pcf_p0 = pcf.get_pin(0)
pcf_p0.switch_to_output(False)

ss   = Seesaw(i2c, addr=0x36)
encoder = rotaryio.IncrementalEncoder(ss)
enc_last = encoder.position

btns = []
if HAS_QWIIC_BTN:
    for addr in (0x6F, 0x40):      # 你的 i2cdetect 结果；若只有一个就保留 0x6F
        try:
            b = qwiic_button.QwiicButton(address=addr)
            if b.begin():
                btns.append(b)
        except Exception:
            pass

page = 0
pages = ["SENSORS", "TOUCH", "GESTURE"]

def rebuild_canvas_if_needed():
    global image, draw
    if image.size != (disp.width, disp.height):
        image = Image.new("RGB", (disp.width, disp.height))
        draw  = ImageDraw.Draw(image)
        print("Rebuilt canvas to:", image.size)

def banner(txt):
    draw.rectangle((0, 0, disp.width, 26), fill=(20,20,20))
    draw.text((6, 4), txt, font=font, fill=(255,255,255))

def status_line(y, label, val, ok=True):
    col = (80,220,120) if ok else (230,90,90)
    draw.text((6, y),  f"{label}", font=font, fill=(200,200,200))
    draw.text((118, y), f"{val}",  font=font, fill=col)

while True:
    rebuild_canvas_if_needed()
    draw.rectangle((0,0,disp.width,disp.height), fill=(0,0,0))

    # 旋钮切页
    pos = encoder.position
    if pos != enc_last:
        page = (page + 1) % len(pages) if pos > enc_last else (page - 1) % len(pages)
        enc_last = pos

    if page == 0:
        banner("SENSORS — rotate knob to change page")
        ax, ay, az = imu.acceleration
        gx, gy, gz = imu.gyro
        status_line(30, "IMU Accel", f"{ax:+.1f},{ay:+.1f},{az:+.1f}")
        status_line(48, "IMU Gyro ", f"{gx:+.2f},{gy:+.2f},{gz:+.2f}")

        r,g,b,c = apds.color_data
        prox = apds.proximity
        status_line(70, "APDS RGB ", f"{r},{g},{b}")
        status_line(88, "APDS C/P ", f"C={c}  P={prox}")

        y = 108
        for i, bt in enumerate(btns):
            pressed = bt.is_button_pressed()
            status_line(y, f"QwiicBtn{i}({hex(bt.address)})",
                        "PRESSED" if pressed else "idle", ok=not pressed)
            y += 16

        pcf_p0.value = not pcf_p0.value
        if y <= disp.height - 14:
            status_line(y, "PCF8574 P0", "blink")

    elif page == 1:
        banner("TOUCH (MPR121)")
        rad = 10
        gap_x = (disp.width - 2*12 - 6*2*rad) / 5
        for i in range(12):
            row, col = divmod(i, 6)
            x0 = 12 + col * (2*rad + gap_x)
            y0 = 34 + row * 46
            touched = mpr[i].value
            fill = (90,180,255) if touched else (50,50,50)
            draw.ellipse((x0, y0, x0+2*rad, y0+2*rad),
                         outline=(200,200,200), width=2, fill=fill)
            draw.text((x0+6, y0+2*rad+3), str(i), font=font, fill=(200,200,200))

    else:
        banner("GESTURE (APDS9960)")
        g = apds.gesture()  # 0=None, 1=Up, 2=Down, 3=Left, 4=Right（不同库版本略有差异）
        mapping = {0:"None",1:"Up",2:"Down",3:"Left",4:"Right"}
        draw.text((8, 44), f"Gesture: {mapping.get(g,'?')}",
                  font=font, fill=(180,220,180))
        draw.text((8, 66), "Wave your hand over the top sensor",
                  font=font, fill=(200,200,200))

    disp.image(image)
    time.sleep(0.08)
