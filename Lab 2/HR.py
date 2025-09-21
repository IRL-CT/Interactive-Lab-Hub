# -*- coding: utf-8 -*-
import time, math, random
import board, busio, digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

# ===== 显示：ST7789 240x135（原生 135x240）=====
ROTATION = 180          # 横屏：270 或 90（二选一）
X_OFFSET, Y_OFFSET = 0, 0
BAUDRATE = 64_000_000

spi = board.SPI()
dc_pin = digitalio.DigitalInOut(board.D25)
disp = st7789.ST7789(
    spi, cs=None, dc=dc_pin, rst=None, baudrate=BAUDRATE,
    width=135, height=240, x_offset=X_OFFSET, y_offset=Y_OFFSET,
    rotation=ROTATION
)

# —— 画布严格使用驱动给的尺寸（避免尺寸报错）——
from PIL import Image
W, H = disp.width, disp.height
image = Image.new("RGB", (W, H))
draw  = ImageDraw.Draw(image)
def ensure_canvas():
    global image, draw
    if image.size != (disp.width, disp.height):
        image = Image.new("RGB", (disp.width, disp.height))
        draw  = ImageDraw.Draw(image)

# ===== 字体 =====
try:
    from PIL import ImageFont
    font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    font_sm  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except Exception:
    font_big = font_sm = ImageFont.load_default()

# ===== I2C 设备 =====
import adafruit_mpr121
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw import rotaryio
try:
    import qwiic_button
    HAS_QWIIC=True
except Exception:
    HAS_QWIIC=False

i2c  = busio.I2C(board.SCL, board.SDA)
mpr  = adafruit_mpr121.MPR121(i2c)          # 触摸
imu  = LSM6DS3(i2c)                          # IMU
ss   = Seesaw(i2c, addr=0x36)                # 旋钮
encoder = rotaryio.IncrementalEncoder(ss); enc_last = encoder.position

# Qwiic 按钮LED：0x6F=红 秒闪，0x40=绿 分闪（若反了就对调地址）
RED_ADDR, GREEN_ADDR = 0x6F, 0x40
red_btn = green_btn = None
if HAS_QWIIC:
    try:
        rb = qwiic_button.QwiicButton(RED_ADDR)
        if rb.begin(): rb.set_led_brightness(255); rb.LED_off(); red_btn = rb
    except: pass
    try:
        gb = qwiic_button.QwiicButton(GREEN_ADDR)
        if gb.begin(): gb.set_led_brightness(255); gb.LED_off(); green_btn = gb
    except: pass
def led_on(dev): 
    try: dev and dev.LED_on()
    except: pass
def led_off(dev): 
    try: dev and dev.LED_off()
    except: pass

# ===== 页面 & ECG 状态 =====
page = 0            # 0=时间页, 1=ECG页
bpm  = 72
phase = 0.0
noise_amp = 0.0
band_h = int(H * 0.35)            # ECG 带高度（更小更精致）
band_top = (H - band_h)//2        # 居中放
band_mid = band_top + band_h//2
prev_y = band_mid                 # 上一帧 y（画“线”用）
extra_beat = 0.0                  # 触摸触发的强脉冲

def qrs_wave(t):
    v = 0.0
    if 0.05 <= t < 0.15: v += 0.4 * math.sin(math.pi*(t-0.05)/0.10)  # P
    if 0.18 <= t < 0.22: v += -1.2                                   # Q
    if 0.22 <= t < 0.24: v += +2.5                                   # R
    if 0.24 <= t < 0.30: v += -0.8                                   # S
    if 0.40 <= t < 0.65: v += 0.6 * math.sin(math.pi*(t-0.40)/0.25)  # T
    return v

def update_motion():
    global noise_amp
    ax, ay, az = imu.acceleration
    gmag = min(3.0, abs(ax)+abs(ay))
    noise_amp = 0.5 * (gmag/3.0)  # 0..0.5

def check_touch():
    global extra_beat
    for i in range(12):
        if mpr[i].value:
            extra_beat = 1.0      # 立刻强脉冲
            return True
    return False

# —— 时间页（大号时间 + 右侧刻度环）——
def draw_time_page():
    draw.rectangle((0,0,W,H), fill=(0,0,0))
    t = time.localtime()
    hhmm = f"{t.tm_hour:02d}:{t.tm_min:02d}"
    sec  = t.tm_sec
    draw.text((12, 28), hhmm, font=font_big, fill=(255,220,120))
    draw.text((12, 75), f":{sec:02d}", font=font_sm, fill=(255,160,80))
    cx, cy = int(W*0.75), int(H*0.5)
    r = 45
    draw.ellipse((cx-r,cy-r,cx+r,cy+r), outline=(255,160,80), width=2)
    for k in range(12):
        ang = math.radians(k*30 - 90)
        x1,y1 = cx + int(r*0.92*math.cos(ang)), cy + int(r*0.92*math.sin(ang))
        x2,y2 = cx + int(r*1.03*math.cos(ang)), cy + int(r*1.03*math.sin(ang))
        draw.line((x1,y1,x2,y2), fill=(255,160,80), width=2)

# —— ECG 页（横向带状，小而精；用“线段”而不是点）——
def draw_ecg_page():
    global phase, prev_y, extra_beat
    # 背景 & 带区域
    # 整体左移 1px
    left = image.crop((1, 0, W, H))
    image.paste(left, (0, 0))
    # 擦除最右列
    draw.line((W-1, 0, W-1, H), fill=(0,0,0))
    # 带区域边框（淡）
    draw.rectangle((0, band_top, W-1, band_top+band_h), outline=(30,30,30), width=1)

    # 新相位
    beat_hz = bpm/60.0
    dt = 0.016
    phase = (phase + beat_hz*dt) % 1.0

    # 波形 + 触摸强脉冲 + 噪声
    v = qrs_wave(phase)
    if extra_beat > 0:
        v += 1.2 * extra_beat
        extra_beat = max(0.0, extra_beat - 0.05)
    v += (random.random()-0.5)*2.0*noise_amp

    # 映射到带区域
    amp = int(band_h * 0.40)
    y = band_mid - int(v * amp)
    y = max(band_top+1, min(band_top+band_h-2, y))

    # 在最右两列画“连线”（更顺滑）
    # 上一帧 y 在列 W-2，本帧 y 在列 W-1
    draw.line((W-2, prev_y, W-1, y), fill=(120,255,140), width=2)
    prev_y = y

    # 右上角 BPM 标签
    draw.rectangle((0,0,86,18), fill=(0,0,0))
    draw.text((2,2), f"{bpm:3d} BPM", font=font_sm, fill=(120,255,140))

# —— LED：红灯每秒闪一次，绿灯每分钟闪一下（200ms）——
last_minute = -1
def drive_leds_by_clock():
    global last_minute
    t = time.localtime()
    # 红：每秒方波
    if t.tm_sec % 2 == 0: led_on(red_btn)
    else: led_off(red_btn)
    # 绿：每分钟第 0 秒闪 200ms
    if t.tm_min != last_minute and t.tm_sec == 0:
        last_minute = t.tm_min
        led_on(green_btn)
    if t.tm_sec != 0:
        led_off(green_btn)

# ===== 主循环：旋钮换页，触摸触发强脉冲，IMU 加噪 =====
last_switch = 0.0
try:
    while True:
        ensure_canvas()

        # 旋钮：动一下换页（去抖 120ms）
        pos = encoder.position
        now = time.monotonic()
        if pos != enc_last and (now - last_switch) > 0.12:
            page = (page + 1) % 2 if pos > enc_last else (page - 1) % 2
            enc_last = pos
            last_switch = now

        update_motion()
        _ = check_touch()  # 触摸=立刻强脉冲

        if page == 0:
            draw_time_page()
        else:
            draw_ecg_page()

        drive_leds_by_clock()
        disp.image(image)
        time.sleep(0.016)
except KeyboardInterrupt:
    pass
finally:
    led_off(red_btn); led_off(green_btn)
