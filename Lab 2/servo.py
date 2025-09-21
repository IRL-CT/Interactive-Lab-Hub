# showcase_seesaw_knob.py
# 4界面：Clock / Hourglass / Heartbeat / Egg
# 旋钮：Seesaw I2C(0x36) 旋转切页、按压回到第1页
# 舵机：lgpio，2s 往返；IMU：LSM6DS*；无IMU则 tilt=0 & shake=0（无“假抖动”）

import time, math, random
import board, busio, digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import lgpio

# ===== 显示屏 ST7789 =====
BAUDRATE = 64_000_000
spi = board.SPI()
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
disp = st7789.ST7789(
    spi, cs=cs_pin, dc=dc_pin, rst=None, baudrate=BAUDRATE,
    width=135, height=240, x_offset=53, y_offset=40
)
W, H = disp.height, disp.width         # 横屏
rotation = 90
image = Image.new("RGB", (W, H))
draw  = ImageDraw.Draw(image)
try:
    FONT_BIG   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    FONT_MONO  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
except Exception:
    FONT_BIG = FONT_SMALL = FONT_MONO = ImageFont.load_default()

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

# ===== 舵机（lgpio）=====
CHIP = 0
hchip = lgpio.gpiochip_open(CHIP)
SERVO_PIN = 13          # 信号脚：13/12/19 之一
FREQ = 50.0
CENTER_US, AMP_US, PERIOD = 1500, 400, 2.0  # 左1秒↔右1秒
def us2duty(us): return (us/20000.0)*100.0
lgpio.gpio_claim_output(hchip, SERVO_PIN)
lgpio.tx_pwm(hchip, SERVO_PIN, FREQ, us2duty(CENTER_US))
t0_servo = time.time()

# ===== 旋钮：Seesaw I2C(0x36) =====
i2c = busio.I2C(board.SCL, board.SDA)
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw import rotaryio, digitalio as ssdio

try:
    ss = Seesaw(i2c, addr=0x36)
    encoder = rotaryio.IncrementalEncoder(ss)
    enc_last = encoder.position
    # 常见按压脚是 24；若你的模块不同，改成实际脚号（如 9）
    try:
        btn = ssdio.DigitalIO(ss, 24)
        btn.switch_to_input(pull=ssdio.Pull.UP)
    except Exception:
        btn = None
except Exception:
    encoder = None
    enc_last = 0
    btn = None

def knob_step():
    """Seesaw 旋钮步进：+1/-1/0"""
    global enc_last
    if encoder is None:
        return 0
    pos = encoder.position
    if pos == enc_last:
        return 0
    step = +1 if pos > enc_last else -1
    enc_last = pos
    return step

def knob_pressed():
    return (btn is not None) and (btn.value is False)  # 低电平按下

# ===== IMU（LSM6*；无IMU时不造假抖动）=====
imu = None
try:
    from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
    imu = LSM6DS3(i2c)
except Exception:
    try:
        from adafruit_lsm6ds.lsm6ds33 import LSM6DS33
        imu = LSM6DS33(i2c)
    except Exception:
        try:
            from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
            imu = LSM6DSOX(i2c)
        except Exception:
            imu = None

def read_imu():
    """返回 (tilt_deg, shake[0..1]); 无IMU -> (0,0)"""
    if imu is None:
        return (0.0, 0.0)
    ax, ay, az = imu.acceleration
    g = max(1e-3, math.sqrt(ax*ax + ay*ay + az*az))
    roll = math.degrees(math.atan2(ay, math.sqrt(ax*ax + az*az)))
    tilt  = max(-15, min(15, 0.7*roll))
    shake = max(0.0, min(1.0, abs(g - 9.81) / 2.0))
    return (tilt, shake)

# ===== 四个界面 =====
class ScreenBase:
    name = "Base"
    def update(self, draw, dt, tilt, shake): ...

def label(x, y, txt, col="#888"):
    draw.text((x, y), txt, font=FONT_MONO, fill=col)

class ScreenClock(ScreenBase):
    name = "Clock"
    def __init__(self): self.last = -1
    def update(self, draw, dt, tilt, shake):
        s = int(time.time())
        if s == self.last: return
        self.last = s
        draw.rectangle((0,0,W,H), fill=0)
        tstr = time.strftime("%H:%M:%S")
        dstr = time.strftime("%Y-%m-%d")
        bb = draw.textbbox((0,0), tstr, font=FONT_BIG)
        x=(W-(bb[2]-bb[0]))//2; y=(H-(bb[3]-bb[1]))//2
        draw.text((x,y), tstr, font=FONT_BIG, fill="#FFFFFF")
        bb2 = draw.textbbox((0,0), dstr, font=FONT_SMALL)
        x2=(W-(bb2[2]-bb2[0]))//2; y2 = y-(bb2[3]-bb2[1]) - 8
        draw.text((x2,y2), dstr, font=FONT_SMALL, fill="#AAAAAA")
        label(6, H-18, "CLOCK", "#0080FF")

class ScreenHourglass(ScreenBase):
    name = "Hourglass"
    def __init__(self):
        self.D = 60.0
        self.t0 = time.monotonic()
        self.done = False
    def update(self, draw, dt, tilt, shake):
        now = time.monotonic()
        p = min(1.0, (now - self.t0)/self.D); self.done = (p >= 1.0)
        sway = int(10 * (tilt/15.0))
        draw.rectangle((0,0,W,H), fill=0)
        m=16; top=m; mid=H//2; bot=H-m; neck=14; body=W-m*2; col=(180,180,200)
        sx=sway
        top_poly=[(m+sx,top),(W-m+sx,top),(W//2+neck//2,mid),(W//2-neck//2,mid)]
        bot_poly=[(W//2-neck//2,mid),(W//2+neck//2,mid),(W-m-sx,bot),(m-sx,bot)]
        draw.line(top_poly+[top_poly[0]], fill=col, width=2)
        draw.line(bot_poly+[bot_poly[0]], fill=col, width=2)
        top_fill=1.0-p; bot_fill=1.0-top_fill
        sand_top=(240,210,90); sand_bot=(255,190,70)
        top_h=mid-top; top_lvl=top+int(top_h*(1.0-top_fill))
        def iw(y,y0,y1,w0,w1): t=(y-y0)/float(y1-y0); return int(w0*(1-t)+w1*t)
        for y in range(top_lvl, mid):
            w=iw(y, top, mid, body, neck); cx=W//2+int(sx*(1-(y-top)/max(1,top_h)))
            draw.line((cx-w//2, y, cx+w//2, y), fill=sand_top)
        bot_h=bot-mid; bot_lvl=bot-int(bot_h*bot_fill)
        for y in range(mid, bot_lvl):
            w=iw(y, mid, bot, neck, body); cx=W//2-int(sx*((y-mid)/max(1,bot_h)))
            draw.line((cx-w//2, y, cx+w//2, y), fill=sand_bot)
        flow_y1=mid-6; flow_y2=min(bot_lvl, mid+18)
        draw.line((W//2, flow_y1, W//2, flow_y2), fill=(255,220,120), width=1)
        left = max(0, int(self.D-(now-self.t0))) if not self.done else 0
        label(6, 6, f"{left:2d}s", "#C8C8DC"); label(6, H-18, "HOURGLASS", "#FFD000")

class ScreenHeartbeat(ScreenBase):
    name = "Heartbeat"
    def __init__(self): self.speed = 120.0
    def _ecg(self, t, bpm, noise):
        per=60.0/bpm; p=(t%per)/per; v=0.0
        v+=0.15*math.sin(2*math.pi*(p*3))*(p<0.25)
        v+=math.exp(-((p-0.35)/0.02)**2)*(-0.8)
        v+=math.exp(-((p-0.40)/0.008)**2)*(+2.0)
        v+=math.exp(-((p-0.45)/0.015)**2)*(-0.5)
        v+=0.20*math.sin(2*math.pi*(p-0.55)*2)*(0.55<p<0.9)
        v+=noise*(random.random()*2-1)
        return max(-1.5, min(1.5, v))
    def update(self, draw, dt, tilt, shake):
        bpm = 70 + int(40*shake) + int(10*math.sin(time.time()*0.8))
        noise = 0.02 + 0.20*shake
        img = Image.new("RGB", (W,H), "black"); d = ImageDraw.Draw(img)
        for gx in range(0,W,20): d.line((gx,0,gx,H), fill=(20,20,20))
        for gy in range(0,H,20): d.line((0,gy,W,gy), fill=(20,20,20))
        t0 = time.time(); prev=None
        for x in range(W):
            v=self._ecg(t0 + x/self.speed, bpm, noise)
            y=int(H/2 - v*(H*0.35))
            if prev: d.line((prev[0], prev[1], x, y), fill=(0,255,0))
            prev=(x,y)
        image.paste(img, (0,0))
        label(6, H-18, f"ECG ~{bpm} bpm", "#00FF80")

class ScreenEgg(ScreenBase):
    name = "Egg"
    def __init__(self): self.ph = 0.0
    def update(self, draw, dt, tilt, shake):
        self.ph += dt
        draw.rectangle((0,0,W,H), fill=0)
        layer = Image.new("RGBA", (W,H), (0,0,0,0)); d = ImageDraw.Draw(layer)
        cx, cy = W//2, H//2 + 10; rw, rh = int(W*0.28), int(H*0.36)
        d.ellipse((cx-rw, cy-rh-10, cx+rw, cy+rh), fill=(250,250,240,255), outline=(230,230,220,255))
        d.ellipse((cx-rw//2, cy-rh, cx-rw//2+18, cy-rh+18), fill=(255,255,255,180))
        d.ellipse((cx-rw, cy+rh-8, cx+rw, cy+rh+12), fill=(0,0,0,60))
        ang = max(-12, min(12, tilt)) + (shake*6.0)*math.sin(self.ph*18.0)
        rot = layer.rotate(ang, resample=Image.BICUBIC, center=(cx,cy))
        image.paste(rot, (0,0), rot)
        label(6, H-18, "EGG", "#FF9ED1")

SCREENS = [ScreenClock(), ScreenHourglass(), ScreenHeartbeat(), ScreenEgg()]
mode = 0
prev = time.time()

try:
    while True:
        # 1) 舵机：严格 2s 往返
        t = time.time() - t0_servo
        phase = (t % PERIOD) / PERIOD
        offset = AMP_US * (-math.cos(2*math.pi*phase))
        lgpio.tx_pwm(hchip, SERVO_PIN, FREQ, us2duty(CENTER_US + offset))

        # 2) 旋钮：转动切页；按压回到第1页
        step = knob_step()
        if step: mode = (mode + step) % len(SCREENS)
        if knob_pressed(): mode = 0

        # 3) IMU
        tilt, shake = read_imu()

        # 4) 更新当前界面
        now = time.time(); dt = max(1e-3, now - prev); prev = now
        SCREENS[mode].update(draw, dt, tilt, shake)

        # 顶部状态条
        title = f"{mode+1}/4 {SCREENS[mode].name}  tilt={tilt:+.1f}°  shake={shake:.2f}"
        draw.text((W - 6 - draw.textlength(title, font=FONT_MONO), 2), title, font=FONT_MONO, fill="#888")
        disp.image(image, rotation)

        time.sleep(0.02)
except KeyboardInterrupt:
    pass
finally:
    lgpio.tx_pwm(hchip, SERVO_PIN, 0, 0)
    lgpio.gpio_free(hchip, SERVO_PIN)
    lgpio.gpiochip_close(hchip)
