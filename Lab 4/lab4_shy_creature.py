#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lab 4 – Shy Creature Box (Distance + Joystick → Servo + [OLED] + [Sound])

Features
- Inputs: VCNL4040 (0x60) proximity → pseudo-mm, or ToF VL53L1X/VL53L0X (0x29); optional Qwiic Joystick (0x20), Qwiic Button (0x6F)
- Outputs: Servo via PCA9685/Servo pHAT (0x40); optional OLED SSD1306 128x32 (0x3C); optional sound (pygame or terminal bell)
- Joystick center auto-calibration on startup
- Threshold/open-angle adjustment ONLY while the joystick button is held; mode toggle (AUTO/MANUAL) on button release edge
- Hysteresis + EMA smoothing to avoid flicker
- Safe when any device is missing; code runs with whatever is present

Run
  python3 lab4_shy_creature.py --log
  # if no audio device:
  python3 lab4_shy_creature.py --no-sound

Wiring
  I2C/Qwiic shared bus (SDA/SCL). Typical addresses:
  - 0x60 VCNL4040  - proximity
  - 0x29 VL53L1X/L0X - time-of-flight distance
  - 0x20 Qwiic Joystick
  - 0x6F Qwiic Button
  - 0x3C SSD1306 OLED (optional)
  - 0x40 PCA9685 (Servo pHAT)
⚡ Servo power: use Servo pHAT USB-C external power. Do NOT power servos from Pi 5V rail.

Deps (install inside your Lab4 venv, adjust as needed)
  pip install --upgrade adafruit-circuitpython-vcnl4040 sparkfun-qwiic \
      adafruit-circuitpython-vl53l1x adafruit-circuitpython-vl53l0x \
      adafruit-circuitpython-ssd1306 pillow adafruit-circuitpython-servokit
"""
import os, sys, time, argparse
from dataclasses import dataclass

import board, busio

# ----------------------------- Utils -----------------------------------
def clamp(x, a, b): return a if x < a else b if x > b else x

class Lazy:
    """Create resource on first use; store exception for graceful degrade."""
    def __init__(self, factory): self._f=factory; self._obj=None; self._exc=None
    def get(self):
        if self._obj is None and self._exc is None:
            try: self._obj = self._f()
            except Exception as e: self._exc = e
        return self._obj
    def ok(self): _=self.get(); return self._obj is not None
    def error(self): return self._exc

# ----------------------------- Config ----------------------------------
@dataclass
class Config:
    i2c_freq: int = 400000
    ema_alpha: float = 0.25
    fps: float = 20.0

    # Servo/behavior
    servo_channel: int = 0
    servo_min: int = 10       # closed angle
    servo_open: int = 95      # open angle (runtime tweakable)
    servo_speed_dps: float = 180.0

    # Hysteresis thresholds (runtime tweakable)
    approach_mm: float = 140.0   # close→hide
    leave_mm: float = 200.0      # far→open

    sound_enabled: bool = True
    log: bool = False

CFG = Config()

# ----------------------------- I2C scan --------------------------------
def i2c_scan(i2c):
    while not i2c.try_lock(): pass
    try:
        addrs = i2c.scan()
    finally:
        i2c.unlock()
    return set(addrs)

# -------------------------- Device factories ---------------------------
def make_distance_sensor(i2c, addrs):
    """Return Lazy that yields ('kind', dev) where kind in:
       'vl53l1x_adafruit' | 'vl53l1x_sparkfun' | 'vl53l0x_adafruit' |
       'vcnl4040_adafruit' | 'vcnl4040_qwiic'
    """
    if 0x29 in addrs:
        def factory():
            # Try VL53L1X (Adafruit)
            try:
                import adafruit_vl53l1x
                vl = adafruit_vl53l1x.VL53L1X(i2c)
                vl.distance_mode = 1   # short
                vl.timing_budget = 33
                vl.start_ranging()
                return ("vl53l1x_adafruit", vl)
            except Exception:
                pass
            # Try VL53L1X (SparkFun Qwiic)
            try:
                import qwiic_vl53l1x
                vl = qwiic_vl53l1x.QwiicVL53L1X()
                if not vl.sensor_init():
                    raise RuntimeError("VL53L1X init failed")
                vl.set_distance_mode_short()
                vl.start_ranging()
                return ("vl53l1x_sparkfun", vl)
            except Exception:
                pass
            # Fallback: VL53L0X (Adafruit)
            try:
                import adafruit_vl53l0x
                v0 = adafruit_vl53l0x.VL53L0X(i2c)  # .range in mm
                return ("vl53l0x_adafruit", v0)
            except Exception as e:
                raise RuntimeError("0x29 present, but no usable VL53 driver (L1X/L0X)") from e
        return Lazy(factory)
    elif 0x60 in addrs:
        def factory():
            # Adafruit VCNL4040
            try:
                import adafruit_vcnl4040
                v = adafruit_vcnl4040.VCNL4040(i2c)
                return ("vcnl4040_adafruit", v)
            except Exception:
                pass
            # SparkFun Qwiic VCNL4040
            try:
                import qwiic_vcnl4040
                v = qwiic_vcnl4040.QwiicVCNL4040()
                if not v.begin():
                    raise RuntimeError("Qwiic VCNL4040 init failed")
                return ("vcnl4040_qwiic", v)
            except Exception as e:
                raise RuntimeError("0x60 present, but no usable VCNL4040 driver") from e
        return Lazy(factory)
    else:
        def factory():
            raise RuntimeError("No distance sensor found (expect 0x29 or 0x60)")
        return Lazy(factory)

def make_oled(i2c, addrs):
    """Create OLED only if 0x3C present, else return Lazy that always None."""
    if 0x3C not in addrs:
        return Lazy(lambda: None)
    def factory():
        import adafruit_ssd1306
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception:
            # pillow missing; still create device but skip drawing
            Image = ImageDraw = ImageFont = None
        oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3C)
        pack = {"oled": oled, "img": None, "draw": None, "font": None}
        if Image:
            img = Image.new("1", (128, 32))
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            pack.update(img=img, draw=draw, font=font)
        oled.fill(0); oled.show()
        return pack
    return Lazy(factory)

def make_servo():
    def factory():
        from adafruit_servokit import ServoKit
        kit = ServoKit(channels=16, address=0x40)
        s = kit.servo[CFG.servo_channel]
        s.set_pulse_width_range(500, 2500)
        return s
    return Lazy(factory)

def make_joystick():
    def factory():
        import qwiic_joystick
        js = qwiic_joystick.QwiicJoystick()
        if not js.is_connected():
            raise RuntimeError("Qwiic Joystick not connected")
        js.begin()
        return js
    return Lazy(factory)

def make_button():
    def factory():
        import qwiic_button
        btn = qwiic_button.QwiicButton()
        if not btn.is_connected():
            raise RuntimeError("Qwiic Button not connected")
        btn.begin()
        return btn
    return Lazy(factory)

def make_beeper(sound_enabled=True):
    def factory():
        if not sound_enabled:
            return ("none", None)
        try:
            import pygame
            pygame.mixer.init()
            # use local chirp.wav if present; otherwise still OK
            path = os.path.join(os.path.dirname(__file__), "chirp.wav")
            if os.path.exists(path):
                snd = pygame.mixer.Sound(path)
                return ("pygame", snd)
            else:
                return ("terminal_bell", None)
        except Exception:
            return ("terminal_bell", None)
    return Lazy(factory)

# ----------------------------- Helpers ---------------------------------
class EMA:
    def __init__(self, a, init=None): self.a=a; self.y=init
    def update(self, x):
        self.y = x if self.y is None else (self.a*x + (1-self.a)*self.y)
        return self.y

class VCNL4040Mapper:
    """Map proximity counts → pseudo-mm using simple on-the-fly calibration."""
    def __init__(self): self.p_far=None; self.p_near=None
    def calib_far(self, p): self.p_far = p if self.p_far is None else min(self.p_far, p)
    def calib_near(self, p): self.p_near = p if self.p_near is None else max(self.p_near, p)
    def to_mm(self, p):
        pf = self.p_far if self.p_far is not None else 5
        pn = self.p_near if self.p_near is not None else 2000
        if pn <= pf: pn = pf + 1
        t = (p - pf) / (pn - pf)
        t = clamp(t, 0.0, 1.0)
        return 300.0 - t*240.0  # 300→far, 60→near

class ServoMover:
    def __init__(self, servo, speed_dps):
        self.servo = servo
        self.speed = abs(speed_dps)
        self.target = None
        self.pos = None
    def set_target(self, deg): self.target = clamp(deg, 0, 180)
    def step(self, dt):
        if self.target is None: return
        if self.pos is None: self.pos = self.target
        max_step = self.speed * dt
        delta = clamp(self.target - self.pos, -max_step, max_step)
        self.pos += delta
        if self.servo:
            try: self.servo.angle = self.pos
            except Exception: pass

@dataclass
class State:
    mode: str = "AUTO"   # AUTO / MANUAL
    face: str = "idle"
    dist_mm: float = 999.0
    servo_deg: float = 10.0

FACES = {
    "idle":   ("- _ -", "…"),
    "shy":    ("> _ <", "Hiding"),
    "peek":   ("^ _ ^", "Peeking"),
    "happy":  ("^ v ^", "Hello"),
    "manual": ("o _ o", "Manual"),
}

def draw_face(oled_pack, face_key, dist_mm, mode):
    if not oled_pack: return
    oled = oled_pack.get("oled") if isinstance(oled_pack, dict) else None
    if not oled: return
    img = oled_pack.get("img"); draw = oled_pack.get("draw"); font = oled_pack.get("font")
    if not (img and draw and font):
        # No PIL: just clear or lightweight feedback
        try:
            oled.fill(0); oled.show()
        except Exception:
            pass
        return
    draw.rectangle((0,0,128,32), outline=0, fill=0)
    title, sub = FACES.get(face_key, FACES["idle"])
    draw.text((2, 4), title, font=font, fill=255)
    s1 = f"{sub}"
    s2 = f"{dist_mm:5.0f} mm [{mode}]"
    draw.text((60, 2), s1, font=font, fill=255)
    draw.text((60, 18), s2, font=font, fill=255)
    try:
        oled.image(img); oled.show()
    except Exception:
        pass

def chirp(beeper):
    if not beeper: return
    kind, obj = beeper
    if kind == "pygame" and obj is not None:
        try: obj.play()
        except Exception: pass
    elif kind == "terminal_bell":
        sys.stdout.write("\a"); sys.stdout.flush()

# ------------------------------- Main ----------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", action="store_true")
    parser.add_argument("--no-sound", action="store_true")
    args = parser.parse_args()
    CFG.log = args.log
    CFG.sound_enabled = not args.no_sound

    i2c = busio.I2C(board.SCL, board.SDA, frequency=CFG.i2c_freq)
    addrs = i2c_scan(i2c)
    if CFG.log:
        print("I2C addresses:", [hex(a) for a in sorted(addrs)])

    dist = make_distance_sensor(i2c, addrs)
    oled = make_oled(i2c, addrs)
    servo = make_servo()
    js    = make_joystick()
    btn   = make_button()
    beep  = make_beeper(CFG.sound_enabled)

    # Construct once
    _dist = dist.get(); _oled = oled.get(); _servo = servo.get()
    if CFG.log:
        print("Distance:", _dist if _dist else dist.error())
        print("OLED:", ("ok" if _oled else ("none" if 0x3C not in addrs else oled.error())))
        print("Servo:", "ok" if _servo else servo.error())
        print("Joystick:", "ok" if js.get() else js.error())
        print("Button:", "ok" if btn.get() else btn.error())
        print("Beeper:", beep.get())

    ema = EMA(CFG.ema_alpha)
    vmap = VCNL4040Mapper()
    mover = ServoMover(_servo, CFG.servo_speed_dps)
    st = State()
    mover.set_target(CFG.servo_min)

    # ---- Joystick center calibration ----
    JS_CX = 512.0; JS_CY = 512.0
    if js.get():
        try:
            sx = sy = 0.0
            for _ in range(30):
                sx += js.get().get_horizontal()
                sy += js.get().get_vertical()
                time.sleep(0.005)
            JS_CX = sx / 30.0
            JS_CY = sy / 30.0
            if CFG.log:
                print(f"Joystick center: ({JS_CX:.1f}, {JS_CY:.1f})")
        except Exception:
            pass
    DEAD = 0.25
    prev_pressed = False

    dt = 1.0 / CFG.fps
    try:
        while True:
            t1 = time.time()

            # ---- Read distance ----
            dist_mm = None
            kind_dev = dist.get()
            if kind_dev:
                kind, dev = kind_dev
                try:
                    if kind.startswith("vl53l1x"):
                        d = dev.distance if hasattr(dev, "distance") else dev.get_distance()
                        if d is not None and d > 0: dist_mm = float(d)
                    elif kind == "vl53l0x_adafruit":
                        d = dev.range
                        if d is not None and d > 0: dist_mm = float(d)
                    elif kind in ("vcnl4040_adafruit", "vcnl4040_qwiic"):
                        if kind == "vcnl4040_qwiic":
                            p = dev.get_proximity() if hasattr(dev, "get_proximity") else dev.proximity
                        else:
                            p = dev.proximity
                        vmap.calib_far(p)
                        if p > 1500: vmap.calib_near(p)
                        dist_mm = vmap.to_mm(p)
                except Exception as e:
                    if CFG.log: print("distance read error:", e)
            if dist_mm is None: dist_mm = st.dist_mm
            st.dist_mm = ema.update(dist_mm)

            # ---- Inputs: joystick / button ----
            pressed_now = False
            js_obj = js.get()
            if js_obj:
                try:
                    x = js_obj.get_horizontal()
                    y = js_obj.get_vertical()
                    b = js_obj.button       # 0=pressed, 1=released
                    pressed_now = (b == 0)
                    dx = (x - JS_CX) / 512.0
                    dy = (y - JS_CY) / 512.0

                    # Adjust thresholds/angle ONLY while held
                    if pressed_now:
                        if abs(dx) > DEAD:
                            CFG.approach_mm = clamp(140 + dx*80, 80, 260)
                            CFG.leave_mm    = clamp(200 + dx*80, CFG.approach_mm + 20, 360)
                        if abs(dy) > DEAD:
                            CFG.servo_open  = int(clamp(95 + (-dy)*60, 20, 160))

                    # Toggle mode on release edge
                    if (not pressed_now) and prev_pressed:
                        st.mode = "MANUAL" if st.mode == "AUTO" else "AUTO"
                        chirp(beeper=beep.get())
                except Exception:
                    pass
            else:
                # No joystick: fall back to Qwiic Button to toggle mode
                btn_obj = btn.get()
                if btn_obj:
                    try:
                        if btn_obj.is_button_pressed():
                            st.mode = "MANUAL" if st.mode == "AUTO" else "AUTO"
                            chirp(beeper=beep.get())
                            time.sleep(0.2)
                    except Exception:
                        pass

            prev_pressed = pressed_now

            # ---- State machine ----
            if st.mode == "MANUAL" and js.get():
                # Map joystick Y to servo angle with deadzone
                try:
                    y = js.get().get_vertical()
                    dy = (y - JS_CY) / 512.0
                    if abs(dy) <= DEAD:
                        target = int((CFG.servo_min + CFG.servo_open) / 2)
                    else:
                        target = int(clamp((CFG.servo_min + CFG.servo_open)/2 + (-dy)*70, 0, 180))
                    mover.set_target(target)
                    st.face = "manual"
                except Exception:
                    st.mode = "AUTO"
            else:
                # AUTO with hysteresis
                if st.dist_mm <= CFG.approach_mm:
                    mover.set_target(CFG.servo_min)
                    if st.face != "shy": chirp(beeper=beep.get())
                    st.face = "shy"
                elif st.dist_mm >= CFG.leave_mm:
                    mover.set_target(CFG.servo_open)
                    if st.face != "happy": chirp(beeper=beep.get())
                    st.face = "happy"
                else:
                    mover.set_target((CFG.servo_min + CFG.servo_open) / 2)
                    st.face = "peek"

            mover.step(dt)
            draw_face(_oled, st.face if st.mode=="AUTO" else "manual", st.dist_mm, st.mode)

            # log line ~2Hz
            if CFG.log and int(time.time()*5) % 5 == 0:
                print(f"dist={st.dist_mm:6.1f}mm | thr={CFG.approach_mm:.0f}/{CFG.leave_mm:.0f} | "
                      f"servo={(mover.pos if mover.pos is not None else 0):5.1f} | face={st.face} | mode={st.mode}")

            # keep fps
            t2 = time.time()
            time.sleep(max(0.0, dt - (t2 - t1)))

    except KeyboardInterrupt:
        pass
    finally:
        # Safe shutdown: close face, clear OLED
        try:
            mover.set_target(CFG.servo_min)
            for _ in range(10):
                mover.step(0.05); time.sleep(0.05)
        except Exception:
            pass
        try:
            if _oled and isinstance(_oled, dict) and _oled.get("oled"):
                _oled["oled"].fill(0); _oled["oled"].show()
        except Exception:
            pass
        try:
            kind_dev = dist.get()
            if kind_dev:
                kind, dev = kind_dev
                if kind in ("vl53l1x_sparkfun","vl53l1x_adafruit"):
                    dev.stop_ranging()
        except Exception:
            pass

if __name__ == "__main__":
    main()
