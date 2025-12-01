# -*- coding: utf-8 -*-
import time, math
import board, busio, digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

# ====== 显示屏（ST7789 240x135；原生 135x240）======
ROTATION = 180          # 横屏一般用 270 或 90，不对就换另一个
X_OFFSET, Y_OFFSET = 53, 40
BAUDRATE = 64_000_000

spi = board.SPI()
dc_pin = digitalio.DigitalInOut(board.D25)
disp = st7789.ST7789(
    spi, cs=None, dc=dc_pin, rst=None, baudrate=BAUDRATE,
    width=135, height=240, x_offset=X_OFFSET, y_offset=Y_OFFSET,
    rotation=ROTATION
)

W, H = disp.width, disp.height
image = Image.new("RGB", (W, H))
draw  = ImageDraw.Draw(image)

def ensure_canvas():
    global image, draw, W, H
    if image.size != (disp.width, disp.height):
        W, H = disp.width, disp.height
        image = Image.new("RGB", (W, H))
        draw  = ImageDraw.Draw(image)

# ====== I2C 设备 ======
import adafruit_mpr121   # 没用到也可移除
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
try:
    import qwiic_button
    HAS_QWIIC = True
except Exception:
    HAS_QWIIC = False

i2c = busio.I2C(board.SCL, board.SDA)
imu = LSM6DS3(i2c)

# 两个 Qwiic Button（按你之前的地址：0x6F=红, 0x40=绿；如反了就调换）
RED_ADDR, GREEN_ADDR = 0x6F, 0x40
red_btn = green_btn = None
if HAS_QWIIC:
    try:
        b = qwiic_button.QwiicButton(RED_ADDR)
        if b.begin():
            red_btn = b
            try: red_btn.set_led_brightness(0)
            except: pass
            red_btn.LED_off()
    except: pass
    try:
        b = qwiic_button.QwiicButton(GREEN_ADDR)
        if b.begin():
            green_btn = b
            try: green_btn.set_led_brightness(0)
            except: pass
            green_btn.LED_off()
    except: pass

def led_set(dev, val):   # 0..255
    if not dev: return
    v = max(0, min(255, int(val)))
    try:
        dev.set_led_brightness(v)
        if v > 0: dev.LED_on()
        else: dev.LED_off()
    except: pass

def led_on(dev):
    if dev:
        try: dev.LED_on()
        except: pass

def led_off(dev):
    if dev:
        try: dev.LED_off()
        except: pass

def btn_pressed(dev) -> bool:
    if not dev: return False
    try:
        return bool(dev.is_button_pressed())
    except:
        return False

# ====== 沙漏状态机 ======
DURATION = 60.0          # 一次漏完的时间（秒），随意改：30/60/120 ...
active = "red"           # 当前回合：'red' 或 'green'
start_t = time.monotonic()
done = False             # 当前回合是否结束（进入闪烁等待翻转）

# IMU 侧倾→沙漏左右“形变”，不影响时间
def get_tilt_pixels():
    ax, ay, az = imu.acceleration
    tilt = max(-1.0, min(1.0, ax/9.8))  # -1..1 左右倾斜
    sway = int(10 * tilt)               # 最大 ~10 像素横向形变
    return sway

# 画沙漏（带倾斜形变），并根据 progress(0..1) 画沙子上下量 & 中央沙流
def draw_hourglass(progress, sway_px):
    # 背景
    draw.rectangle((0, 0, W, H), fill=(0, 0, 0))

    # 沙漏外廓参数
    margin = 16
    top_y   = margin
    mid_y   = H // 2
    bot_y   = H - margin
    neck_w  = 14                 # 中部“瓶颈”宽度
    body_w  = W - margin*2       # 上下最宽处
    line_col = (180, 180, 200)

    # 根据倾斜在左右方向做“剪切形变”（四角横向偏移）
    # 左上、右上、左下、右下分别按 sway_px / -sway_px 偏移
    sx = sway_px
    # 上半部分外轮廓（梯形）
    top_poly = [
        (margin + sx,        top_y),
        (W - margin + sx,    top_y),
        (W//2 + neck_w//2,   mid_y),
        (W//2 - neck_w//2,   mid_y),
    ]
    # 下半部分外轮廓
    bot_poly = [
        (W//2 - neck_w//2,   mid_y),
        (W//2 + neck_w//2,   mid_y),
        (W - margin - sx,    bot_y),
        (margin - sx,        bot_y),
    ]

    draw.line(top_poly + [top_poly[0]], fill=line_col, width=2)
    draw.line(bot_poly + [bot_poly[0]], fill=line_col, width=2)

    # ----- 沙子 -----
    # progress: 0..1（上：从满到空；下：从空到满）
    top_fill = 1.0 - max(0.0, min(1.0, progress))
    bot_fill = 1.0 - top_fill

    sand_top = (240, 210, 90)   # 上半部沙子颜色
    sand_bot = (255, 190, 70)

    # 上半：在 top_poly 内画一个“倒三角”填充，顶面高度按 top_fill 变化
    # 估算上半的垂直高度
    top_h = mid_y - top_y
    top_level_y = top_y + int(top_h * (1.0 - top_fill))

    # 顶面横向宽度（线性从 body_w -> neck_w）
    def interp_w(y, y0, y1, w0, w1):
        t = (y - y0) / float(y1 - y0)
        return int(w0 * (1 - t) + w1 * t)

    # 画上半“填充层”：从 top_y..top_level_y 的一系列横线
    for y in range(top_level_y, mid_y):
        w = interp_w(y, top_y, mid_y, body_w, neck_w)
        cx = W//2 + int(sway_px * (1 - (y - top_y)/max(1, top_h)))  # 轻微随高度偏移
        x1 = cx - w//2
        x2 = cx + w//2
        draw.line((x1, y, x2, y), fill=sand_top)

    # 下半：从 mid_y..bot_y 的“正三角”填充，底部厚起来
    bot_h = bot_y - mid_y
    bot_level_y = bot_y - int(bot_h * bot_fill)
    for y in range(mid_y, bot_level_y):
        w = interp_w(y, mid_y, bot_y, neck_w, body_w)
        cx = W//2 - int(sway_px * ( (y - mid_y)/max(1, bot_h) ))    # 反向偏移增加立体感
        x1 = cx - w//2
        x2 = cx + w//2
        draw.line((x1, y, x2, y), fill=sand_bot)

    # 中央沙流：细线从瓶颈往下
    flow_y1 = mid_y - 6
    flow_y2 = min(bot_level_y, mid_y + 18)
    draw.line((W//2, flow_y1, W//2, flow_y2), fill=(255, 220, 120), width=1)

    # 顶部沙面（可见的横线）
    if top_fill > 0.02:
        w = interp_w(top_level_y, top_y, mid_y, body_w, neck_w)
        cx = W//2 + int(sway_px * (1 - (top_level_y - top_y)/max(1, top_h)))
        x1 = cx - w//2; x2 = cx + w//2
        draw.line((x1, top_level_y, x2, top_level_y), fill=(255, 235, 140))

# LED 渐亮或闪烁
def update_leds(active_side, progress, done, tnow):
    # 渐亮：随 progress 从 0→255
    val = int(max(0, min(255, 255*progress)))
    # 闪烁：2Hz
    blink_on = int(tnow*2) % 2 == 0

    if active_side == "red":
        if red_btn:
            led_set(red_btn, val if not done else (255 if blink_on else 0))
        if green_btn:
            led_set(green_btn, 0)  # 另一侧灭
    else:
        if green_btn:
            led_set(green_btn, val if not done else (255 if blink_on else 0))
        if red_btn:
            led_set(red_btn, 0)

def try_flip_on_press(active_side):
    global start_t, done, active
    # 只有“已完成（闪烁中）”状态下才响应按键翻转
    if not done:
        return
    if active_side == "red":
        if btn_pressed(red_btn):
            active = "green"
            start_t = time.monotonic()
            done = False
    else:
        if btn_pressed(green_btn):
            active = "red"
            start_t = time.monotonic()
            done = False

# ====== 主循环 ======
try:
    while True:
        ensure_canvas()

        # 进度（与时间绑定，与 IMU 无关）
        now = time.monotonic()
        elapsed = now - start_t
        progress = min(1.0, elapsed / DURATION)
        if progress >= 1.0:
            done = True

        # 视觉摇晃
        sway = get_tilt_pixels()

        # 画面
        draw_hourglass(progress, sway)
        # 标签
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except Exception:
            font = ImageFont.load_default()
        label = f"{active.upper()} {int(DURATION - elapsed) if not done else 0:2d}s"
        draw.text((6, 6), label, font=font, fill=(200, 200, 220))

        # LED 逻辑
        update_leds(active, progress, done, now)
        # 完成后等待对应按钮按下→翻转
        try_flip_on_press(active)

        disp.image(image)
        time.sleep(0.016)  # ~60 FPS
except KeyboardInterrupt:
    pass
finally:
    led_off(red_btn); led_off(green_btn)
