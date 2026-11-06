"""
pi_client.py - shared Hot Potato client for every Pi
=====================================================

Every player's script imports this. It does all the boring parts:
  * connects to the class MQTT broker and joins the game under your name
  * keeps `game.state` up to date with what the server sends you (it PUSHES updates;
    you never have to ask for them)
  * redraws the miniPiTFT about 12 times a second from that state
  * gives you four simple calls for your input code:

        game.aim("left" | "forward" | "right")   # choose who to throw to (no throw yet)
        game.press()                             # the "action" button:
                                                 #   holding  -> throw where you aimed
                                                 #   incoming -> catch
                                                 #   lobby / game over -> start the game
        game.throw("left")                       # throw right away
        game.catch()                             # catch right away

Minimal player script:

    from pi_client import PotatoClient, Edge
    game = PotatoClient("viktor", seat=1, input_name="touch")
    game.start()
    pressed = Edge()
    while True:
        if pressed(my_button_is_down()):
            game.press()
        time.sleep(0.01)

See PI_CLIENT_GUIDE.md for the full walkthrough. Remember: sudo systemctl stop piscreen.service
"""

import json
import math
import os
import threading
import time
import uuid

import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw, ImageFont

BROKER = os.environ.get("MQTT_BROKER", "farlab.infosci.cornell.edu")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
USER = os.environ.get("MQTT_USER", "idd")
PASSWORD = os.environ.get("MQTT_PASS", "device@theFarm")
BASE = os.environ.get("POTATO_TOPIC", "IDD/hotpotato").rstrip("/")

DIRECTIONS = ("left", "forward", "right")
ARROW = {"left": "\u2190", "forward": "\u2191", "right": "\u2192"}   # ← ↑ →

W, H = 240, 135   # miniPiTFT 1.14" in landscape
YELLOW, RED, CYAN, GREEN = (242, 193, 78), (255, 59, 48), (76, 201, 240), (123, 216, 143)
DARK, TEXT, MUTED, BROWN = (21, 18, 31), (244, 240, 255), (165, 159, 192), (150, 98, 48)


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
class Edge:
    """Turn a held input into a single event.

        pressed = Edge()
        if pressed(button.value):   # True only on the moment it goes down
    """

    def __init__(self):
        self.last = False

    def __call__(self, value):
        value = bool(value)
        fired = value and not self.last
        self.last = value
        return fired


_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
_font_cache = {}


def font(size):
    if size not in _font_cache:
        f = None
        for path in _FONT_PATHS:
            try:
                f = ImageFont.truetype(path, size)
                break
            except OSError:
                continue
        if f is None:
            try:
                f = ImageFont.load_default(size=size)
            except TypeError:
                f = ImageFont.load_default()
        _font_cache[size] = f
    return _font_cache[size]


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def text_center(draw, y, text, size, fill, max_w=W - 10):
    """Draw text centred horizontally at y, shrinking it until it fits."""
    while size > 8:
        f = font(size)
        box = draw.textbbox((0, 0), text, font=f)
        if box[2] - box[0] <= max_w:
            break
        size -= 2
    f = font(size)
    box = draw.textbbox((0, 0), text, font=f)
    draw.text(((W - (box[2] - box[0])) / 2 - box[0], y), text, font=f, fill=fill)


def draw_potato(draw, cx, cy, w, h):
    draw.ellipse([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=BROWN, outline=(90, 55, 25), width=2)
    for dx, dy in ((-0.2, -0.15), (0.15, 0.1), (0.25, -0.2), (-0.05, 0.2)):
        x, y = cx + dx * w, cy + dy * h
        draw.ellipse([x - 3, y - 2, x + 3, y + 2], fill=(110, 70, 35))


# --------------------------------------------------------------------------
# What the screen shows for each state  (pure function: easy to test on a laptop)
# --------------------------------------------------------------------------
def render_frame(st, age=0.0, aim=None, flash=None, aim_hint="pick a direction", now=None):
    """st = latest state dict from the server, age = seconds since it arrived."""
    now = time.time() if now is None else now
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    mode = st.get("mode") if st else None
    blink = int(now * 6) % 2 == 0

    if not st or mode in (None, "left", "empty"):
        d.rectangle([0, 0, W, H], fill=(40, 40, 48))
        text_center(d, 45, "connecting..." if not st else "not in the game", 24, MUTED)
        text_center(d, 85, (st.get("name") or "") if st else "", 18, TEXT)
        _overlay(d, st, flash)
        return img

    name = st.get("name") or "?"
    targets = st.get("targets") or {}
    neighbours = "  ".join(f"{ARROW[k]} {targets.get(k) or '-'}" for k in DIRECTIONS)

    if mode == "holding":
        hold_limit = st.get("hold_limit") or 10
        left = max(0.0, (st.get("time_left") or 0) - age)
        heat = 1 - left / hold_limit
        bg = mix(YELLOW, RED, heat)
        fg = (30, 15, 0) if heat < 0.55 else TEXT
        d.rectangle([0, 0, W, H], fill=bg)
        draw_potato(d, 58, 66, 78 + 10 * heat * blink, 54 + 6 * heat * blink)
        d.text((112, 34), f"{left:.1f}", font=font(44), fill=fg)
        d.text((112, 82), "seconds left", font=font(13), fill=fg)
        if aim:
            line = f"{ARROW[aim]} {targets.get(aim) or 'nobody there!'}  - press to throw"
        else:
            line = aim_hint
        d.rectangle([0, H - 22, W, H], fill=mix(bg, (0, 0, 0), 0.25))
        text_center(d, H - 20, line, 15, TEXT)

    elif mode == "incoming":
        if st.get("caught"):
            d.rectangle([0, 0, W, H], fill=GREEN)
            text_center(d, 34, "GOT IT!", 44, DARK)
        else:
            d.rectangle([0, 0, W, H], fill=CYAN if blink else (10, 45, 60))
            fg = DARK if blink else CYAN
            text_center(d, 26, "CATCH!", 50, fg)
            src = st.get("incoming_dir")
            text_center(d, 86, f"{ARROW.get(src, '')} from {st.get('incoming_from') or '?'}", 18, fg)
            flight = st.get("flight_time") or 1.5
            frac = max(0.0, ((st.get("flight_left") or 0) - age) / flight)
            d.rectangle([0, H - 8, int(W * frac), H], fill=fg)

    elif mode == "waiting":
        text_center(d, 30, "READY", 36, TEXT)
        holder = st.get("holder")
        text_center(d, 74, f"{holder} has it" if holder else "", 17, YELLOW)
        text_center(d, H - 22, neighbours, 13, MUTED)

    elif mode == "boom":
        d.rectangle([0, 0, W, H], fill=RED if blink else (255, 230, 220))
        fg = TEXT if blink else RED
        text_center(d, 24, "BOOM!", 52, fg)
        text_center(d, 88, st.get("boom_reason") or "", 18, fg)

    elif mode == "safe":
        d.rectangle([0, 0, W, H], fill=(24, 52, 38))
        text_center(d, 30, "phew!", 40, GREEN)
        who = st.get("boom_name")
        text_center(d, 84, f"{who} exploded" if who else "", 17, TEXT)

    elif mode == "lobby":
        text_center(d, 16, name, 30, YELLOW)
        text_center(d, 56, f"seat {st.get('seat')}  -  ready", 16, TEXT)
        text_center(d, 80, "waiting for start", 14, MUTED)
        text_center(d, H - 22, neighbours, 13, MUTED)

    elif mode == "gameover":
        if st.get("loser") == name:
            d.rectangle([0, 0, W, H], fill=(120, 20, 15))
            text_center(d, 34, "YOU'RE TOAST", 30, TEXT)
        else:
            d.rectangle([0, 0, W, H], fill=(24, 52, 38))
            text_center(d, 34, "YOU SURVIVED", 30, GREEN)
            text_center(d, 76, f"{st.get('loser') or '?'} lost", 16, TEXT)
        text_center(d, H - 22, "press to play again", 13, MUTED)

    _header(d, st, age, mode)
    _overlay(d, st, flash)
    return img


def _header(d, st, age, mode):
    """Round timer bar along the top + lives in the corner."""
    if st.get("phase") == "playing" and st.get("round_left") is not None and mode != "boom":
        left = max(0.0, st["round_left"] - age)
        total = st.get("round_time") or 30
        d.rectangle([0, 0, W, 5], fill=(0, 0, 0))
        d.rectangle([0, 0, int(W * left / total), 5], fill=RED if left <= 5 else (255, 255, 255))
        d.text((4, 7), f"{math.ceil(left)}s", font=font(12), fill=(255, 255, 255) if mode != "holding" else (30, 15, 0))
    max_b, booms = st.get("max_booms") or 3, st.get("booms") or 0
    d.rounded_rectangle([W - 12 - (max_b - 1) * 13 - 9, 6, W - 3, 22], radius=8, fill=(0, 0, 0))
    for i in range(max_b):          # lives: filled = still alive
        x = W - 12 - i * 13
        alive = i < max_b - booms
        d.ellipse([x - 5, 9, x + 5, 19], fill=RED if alive else None, outline=(255, 255, 255), width=1)


def _overlay(d, st, flash):
    msg = flash
    if not msg and st and st.get("butterfingers") and st.get("mode") not in ("holding", "incoming"):
        msg = "butterfingers!"
    if msg:
        d.rectangle([0, H - 24, W, H], fill=(0, 0, 0))
        text_center(d, H - 21, msg, 15, YELLOW)


# --------------------------------------------------------------------------
# The miniPiTFT (same wiring as the Lab 6 pixel grid publisher)
# --------------------------------------------------------------------------
class Screen:
    def __init__(self):
        import board
        import digitalio
        import adafruit_rgb_display.st7789 as st7789

        cs = digitalio.DigitalInOut(board.D5)
        dc = digitalio.DigitalInOut(board.D25)
        self.backlight = digitalio.DigitalInOut(board.D22)
        self.backlight.switch_to_output()
        self.backlight.value = True
        self.disp = st7789.ST7789(board.SPI(), cs=cs, dc=dc, rst=None, baudrate=64000000,
                                  width=135, height=240, x_offset=53, y_offset=40, rotation=90)

    def show(self, img):
        self.disp.image(img)

    def off(self):
        self.disp.image(Image.new("RGB", (W, H), (0, 0, 0)))


# --------------------------------------------------------------------------
# The client
# --------------------------------------------------------------------------
class PotatoClient:
    def __init__(self, name, seat=None, input_name="?", aim_hint="pick a direction", screen=True, fps=12):
        self.name = name
        self.seat = seat
        self.input_name = input_name
        self.aim_hint = aim_hint
        self.fps = fps
        self.state = {}             # latest state from the server (replaced on every message)
        self.got_at = 0.0           # when it arrived
        self.aim_dir = None
        self._flash = (None, 0.0)
        self._running = False
        self.action_topic = f"{BASE}/player/{name}/action"

        cid = f"potato-{name}-{uuid.uuid4().hex[:6]}"
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=cid)
        except AttributeError:
            self.client = mqtt.Client(client_id=cid)
        self.client.username_pw_set(USER, PASSWORD)
        # if this Pi crashes or loses power, the broker tells the server we left
        self.client.will_set(self.action_topic, json.dumps({"action": "leave"}))
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self.screen = None
        if screen:
            try:
                self.screen = Screen()
            except Exception as e:   # no PiTFT (e.g. running on a laptop) -> console only
                print(f"[screen] no PiTFT ({e.__class__.__name__}: {e}) - running without a screen")

    # ---------- what your input code calls ----------
    @property
    def mode(self):
        return self.state.get("mode")

    def aim(self, direction):
        if direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}")
        if direction != self.aim_dir:
            self.aim_dir = direction
            print(f"[{self.name}] aiming {direction} -> {(self.state.get('targets') or {}).get(direction)}")

    def press(self):
        """One button that does the right thing for the moment."""
        mode = self.mode
        if mode == "holding":
            if self.aim_dir:
                self.throw(self.aim_dir)
            else:
                self.flash("pick a direction first")
        elif mode in ("lobby", "gameover"):
            self.send("start")
        else:
            self.catch()   # the server decides: catch if it's flying at you, butterfingers if not

    def throw(self, direction=None):
        direction = direction or self.aim_dir
        if direction not in DIRECTIONS:
            self.flash("pick a direction first")
            return
        self.send("throw", dir=direction)
        self.aim_dir = None

    def catch(self):
        self.send("catch")

    def send(self, action, **extra):
        self.client.publish(self.action_topic, json.dumps({"action": action, **extra}))

    def flash(self, text, seconds=1.2):
        """Show a short message along the bottom of the screen."""
        self._flash = (text, time.time() + seconds)

    # ---------- lifecycle ----------
    def start(self):
        print(f"[{self.name}] connecting to {BROKER}:{PORT} ...")
        self.client.connect(BROKER, PORT, keepalive=15)
        self.client.loop_start()
        self._running = True
        threading.Thread(target=self._draw_loop, daemon=True).start()
        return self

    def stop(self):
        self._running = False
        try:
            self.send("leave")
            time.sleep(0.2)
            self.client.loop_stop()
            self.client.disconnect()
        finally:
            if self.screen:
                time.sleep(0.15)
                self.screen.off()

    # ---------- MQTT callbacks ----------
    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            print(f"[{self.name}] broker refused connection (rc={rc})")
            return
        client.subscribe(f"{BASE}/player/{self.name}/state")
        client.subscribe(f"{BASE}/player/{self.name}/error")
        join = {"action": "join", "input": self.input_name}
        if self.seat:
            join["seat"] = self.seat
        client.publish(self.action_topic, json.dumps(join))
        print(f"[{self.name}] connected, joining" + (f" seat {self.seat}" if self.seat else ""))

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload)
        except json.JSONDecodeError:
            return
        if msg.topic.endswith("/error"):
            self.flash(data.get("reason", "rejected"))
            return
        old = self.mode
        self.state = data
        self.got_at = time.time()
        new = data.get("mode")
        if new != old:
            if old == "holding" or new in ("boom", "lobby", "gameover"):
                self.aim_dir = None
            extra = ""
            if new == "incoming":
                extra = f" from {data.get('incoming_from')} - CATCH!"
            elif new == "boom":
                extra = f" ({data.get('boom_reason')})"
            print(f"[{self.name}] {str(new).upper()}{extra}")

    # ---------- screen ----------
    def _draw_loop(self):
        period = 1.0 / self.fps
        while self._running:
            text, until = self._flash
            img = render_frame(self.state, time.time() - self.got_at, self.aim_dir,
                               text if time.time() < until else None, self.aim_hint)
            if self.screen:
                try:
                    self.screen.show(img)
                except Exception as e:
                    print(f"[screen] draw failed: {e}")
                    self.screen = None
            time.sleep(period)
