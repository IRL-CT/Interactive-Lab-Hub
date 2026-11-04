"""
tram_display.py: show the tram tracker on the Adafruit Mini PiTFT (240x135).

    python tram_display.py             # on the PiTFT (run next to tram_watch.py, e.g. in tmux)
    python tram_display.py --preview   # no PiTFT: write tram_display.png every second instead

It only reads tram_state.json, which tram_watch.py rewrites every second, so the two can be
started and stopped separately.

Screens (top button switches, bottom button turns the backlight on/off):
  clock  : big clock, TRAM IN VIEW / last pass, next pass estimate, a bar filling up toward
           the typical gap between trams
  stats  : passes today, typical gap, what the prediction is based on

PiTFT libraries (same as Lab 2), if they are not in this venv yet:
    uv pip install adafruit-circuitpython-rgb-display adafruit-blinka
"""
import argparse
import datetime
import json
import time

from PIL import Image, ImageDraw, ImageFont

from tram_common import STATE

W, H = 240, 135
BG, FG, DIM = (0, 0, 0), (255, 255, 255), (140, 140, 140)
RED, GREEN, AMBER = (230, 40, 40), (60, 200, 90), (255, 180, 0)


def font(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default(size=size)


F_CLOCK, F_BIG, F_MED, F_SMALL = font(34, True), font(17, True), font(14), font(11)


def hm(iso):
    return iso[11:16] if iso else "--:--"


def ago(seconds):
    m = int(seconds // 60)
    return f"{m} min ago" if m else "just now"


def read_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def render(state, screen, now, blink):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 4), now.strftime("%H:%M:%S"), font=F_CLOCK, fill=FG, anchor="ma")

    stale = state is None or (now - datetime.datetime.fromisoformat(state["time"])).total_seconds() > 15
    if stale:
        d.text((W // 2, 62), "tracker not running", font=F_BIG, fill=AMBER, anchor="ma")
        d.text((W // 2, 90), "start tram_watch.py", font=F_SMALL, fill=DIM, anchor="ma")
        return img

    nxt = state.get("next") or {}
    last = state.get("last_pass")

    if screen == "stats":
        lines = [f"passes today: {state.get('passes_today', 0)}"]
        if nxt.get("typical_gap_s"):
            lines.append(f"typical gap: {nxt['typical_gap_s'] / 60:.1f} min")
        if last and last.get("seconds"):
            lines.append(f"last in view: {last['seconds']} s")
        lines.append(f"from: {nxt.get('based_on', '-')}")
        for i, line in enumerate(lines):
            d.text((8, 46 + i * 21), line, font=F_MED if i < 3 else F_SMALL, fill=FG if i < 3 else DIM)
        return img

    # status line: tram in view (blinking red) / closed / last pass
    if state.get("tram_in_view"):
        if blink:
            d.rounded_rectangle((6, 44, W - 6, 70), radius=6, fill=RED)
        d.text((W // 2, 47), "TRAM IN VIEW", font=F_BIG, fill=FG, anchor="ma")
    elif not state.get("in_service"):
        d.text((W // 2, 47), f"closed - opens {hm(nxt.get('opens'))}", font=F_BIG, fill=DIM, anchor="ma")
    elif last:
        since = (now - datetime.datetime.fromisoformat(last["start"])).total_seconds()
        arrow = f"  {last['direction']}" if last.get("direction") else ""
        d.text((W // 2, 49), f"last {hm(last['start'])} ({ago(since)}){arrow}", font=F_MED,
               fill=GREEN, anchor="ma")
    else:
        d.text((W // 2, 49), "waiting for first tram", font=F_MED, fill=DIM, anchor="ma")

    # prediction
    status = nxt.get("status")
    if status == "ok":
        text = f"next ~{hm(nxt.get('eta'))}"
        if nxt.get("low") and nxt.get("high"):
            text += f"  ({hm(nxt['low'])}-{hm(nxt['high'])})"
        d.text((W // 2, 76), text, font=F_MED, fill=FG, anchor="ma")
        p5 = nxt.get("p_within_5min")
        if p5 is not None:
            chance = ">95%" if p5 >= 0.95 else "<5%" if p5 <= 0.05 else f"{p5:.0%}"
            d.text((W // 2, 96), f"{chance} chance within 5 min", font=F_SMALL, fill=DIM, anchor="ma")
    elif status == "overdue":
        d.text((W // 2, 76), "due any moment", font=F_MED, fill=AMBER, anchor="ma")
        d.text((W // 2, 96), "(later than usual)", font=F_SMALL, fill=DIM, anchor="ma")
    elif status and status != "closed":
        d.text((W // 2, 76), status, font=F_SMALL, fill=DIM, anchor="ma")

    # bar: time since last pass vs the typical gap
    gap, since = nxt.get("typical_gap_s"), nxt.get("since_last_s")
    if gap and since is not None and state.get("in_service"):
        frac = min(1.0, since / gap)
        d.rectangle((10, H - 14, W - 10, H - 6), outline=DIM)
        d.rectangle((10, H - 14, 10 + int((W - 20) * frac), H - 6), fill=AMBER if frac >= 1 else GREEN)
    return img


class PiTFT:
    """The Mini PiTFT, wired as in Lab 2: ST7789 on SPI, backlight on D22, buttons on D23/D24."""

    def __init__(self):
        try:
            import board
            import digitalio
            from adafruit_rgb_display import st7789
        except ImportError as e:
            raise SystemExit(f"PiTFT libraries missing ({e}).\n"
                             "  uv pip install adafruit-circuitpython-rgb-display adafruit-blinka\n"
                             "or test without the screen: python tram_display.py --preview")
        self.disp = st7789.ST7789(board.SPI(), cs=digitalio.DigitalInOut(board.CE0),
                                  dc=digitalio.DigitalInOut(board.D25), rst=None,
                                  baudrate=64000000, width=135, height=240,
                                  x_offset=53, y_offset=40, rotation=90)
        self.backlight = digitalio.DigitalInOut(board.D22)
        self.backlight.switch_to_output()
        self.backlight.value = True
        self.a = digitalio.DigitalInOut(board.D23)
        self.b = digitalio.DigitalInOut(board.D24)
        self.a.switch_to_input()
        self.b.switch_to_input()

    def show(self, img):
        self.disp.image(img)

    def pressed(self):
        """'a' (top), 'b' (bottom) or None. The buttons read False while pressed."""
        if not self.a.value:
            return "a"
        if not self.b.value:
            return "b"
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="write tram_display.png instead")
    args = parser.parse_args()
    tft = None if args.preview else PiTFT()
    screen, light, blink, last_press = "clock", True, False, 0.0
    print("display running (Ctrl-C to stop)", flush=True)
    try:
        while True:
            now = datetime.datetime.now()
            if tft:
                button = tft.pressed()
                if button and time.time() - last_press > 0.4:          # simple debounce
                    last_press = time.time()
                    if button == "a":
                        screen = "stats" if screen == "clock" else "clock"
                    else:
                        light = not light
                        tft.backlight.value = light
            img = render(read_state(), screen, now, blink)
            if tft:
                tft.show(img)
            else:
                img.save("tram_display.png")
            blink = not blink
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
