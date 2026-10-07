"""Everything the vending machine draws on the 240x135 MiniPiTFT.

Pure PIL: each function returns an RGB Image, so the screens can be previewed
on a laptop without any Pi hardware (see `python screens.py`).
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 240, 135

BG = (18, 18, 28)
FG = (240, 240, 240)
DIM = (110, 110, 130)
ACCENT = (255, 204, 0)

STATUS_COLORS = {
    "BROWSE": (90, 90, 110),
    "TALKING": (40, 120, 220),
    "LISTENING": (30, 170, 70),
    "THINKING": (220, 150, 0),
    "ENJOY": (200, 60, 160),
}

ITEMS = ["Chips", "Cookies", "Candy Bar", "Soda"]

_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]


def font(size: int) -> ImageFont.ImageFont:
    for path in _FONT_PATHS:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


F_SMALL, F_MED, F_BIG = font(11), font(16), font(22)


# --- item art ---------------------------------------------------------------
# Each sprite is drawn on a transparent 64x64 canvas so it can be scaled for the
# side previews and the fly-out animation.

def _chips(d: ImageDraw.ImageDraw) -> None:
    zig_top = [(8 + i * 6, 6 if i % 2 else 12) for i in range(9)]
    zig_bot = [(56 - i * 6, 58 if i % 2 else 52) for i in range(9)]
    d.polygon(zig_top + [(58, 30)] + zig_bot + [(6, 30)], fill=(220, 40, 40))
    d.ellipse((14, 20, 50, 44), fill=(255, 210, 60))
    d.text((32, 32), "CHIPS", font=font(8), fill=(160, 20, 20), anchor="mm")


def _cookies(d: ImageDraw.ImageDraw) -> None:
    d.ellipse((6, 6, 58, 58), fill=(198, 134, 66), outline=(150, 95, 40), width=3)
    for x, y in [(20, 20), (38, 16), (44, 34), (26, 40), (16, 30), (34, 30), (36, 48)]:
        d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(70, 40, 20))


def _candy_bar(d: ImageDraw.ImageDraw) -> None:
    d.rectangle((12, 20, 52, 44), fill=(120, 50, 170))
    for side in (-1, 1):
        x0 = 12 if side < 0 else 52
        tips = [(x0 + side * (4 if i % 2 else 9), 20 + i * 4) for i in range(7)]
        d.polygon([(x0, 20)] + tips + [(x0, 44)], fill=(90, 35, 130))
    d.text((32, 32), "BAR", font=font(10), fill=(255, 230, 120), anchor="mm")


def _soda(d: ImageDraw.ImageDraw) -> None:
    d.rounded_rectangle((18, 6, 46, 58), radius=6, fill=(30, 100, 210))
    d.ellipse((18, 3, 46, 11), fill=(200, 200, 210))
    d.arc((14, 24, 50, 44), 200, 340, fill=FG, width=3)
    d.text((32, 44), "SODA", font=font(8), fill=FG, anchor="mm")


_ART = {"Chips": _chips, "Cookies": _cookies, "Candy Bar": _candy_bar, "Soda": _soda}


def sprite(name: str, size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    _ART[name](ImageDraw.Draw(img))
    return img if size == 64 else img.resize((size, size), Image.LANCZOS)


def _paste_center(base: Image.Image, spr: Image.Image, cx: int, cy: int) -> None:
    base.paste(spr, (cx - spr.width // 2, cy - spr.height // 2), spr)


# --- chrome -----------------------------------------------------------------

def _status_bar(d: ImageDraw.ImageDraw, status: str, hint: str) -> None:
    d.rectangle((0, 0, WIDTH, 18), fill=(30, 30, 45))
    color = STATUS_COLORS[status]
    pill_w = d.textlength(status, font=F_SMALL) + 12
    d.rounded_rectangle((3, 2, 3 + pill_w, 16), radius=7, fill=color)
    d.text((3 + pill_w / 2, 9), status, font=F_SMALL, fill=FG, anchor="mm")
    d.text((WIDTH - 4, 9), hint, font=F_SMALL, fill=DIM, anchor="rm")


def _arrow(d: ImageDraw.ImageDraw, cx: int, cy: int, direction: int, color) -> None:
    d.polygon([(cx + direction * 7, cy), (cx - direction * 5, cy - 9),
               (cx - direction * 5, cy + 9)], fill=color)


def _mic(d: ImageDraw.ImageDraw, cx: int, cy: int, color) -> None:
    d.rounded_rectangle((cx - 6, cy - 14, cx + 6, cy + 4), radius=6, fill=color)
    d.arc((cx - 11, cy - 8, cx + 11, cy + 10), 0, 180, fill=color, width=3)
    d.line((cx, cy + 10, cx, cy + 16), fill=color, width=3)
    d.line((cx - 6, cy + 16, cx + 6, cy + 16), fill=color, width=3)


# --- screens ----------------------------------------------------------------

def browse(index: int, selected: bool = False, status: str = "BROWSE") -> Image.Image:
    """The menu: current item big in the middle, neighbours dimmed at the sides."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    hint = "press = pick" if not selected else "selected!"
    _status_bar(d, status, hint)

    n = len(ITEMS)
    for offset, cx in [(-1, 40), (1, 200)]:
        side = sprite(ITEMS[(index + offset) % n], 34)
        faded = Image.new("RGBA", side.size, (0, 0, 0, 0))
        faded = Image.blend(faded, side, 0.6)
        _paste_center(img, faded, cx, 66)
    _arrow(d, 12, 66, -1, FG)
    _arrow(d, WIDTH - 12, 66, 1, FG)

    if selected:
        d.rounded_rectangle((80, 26, 160, 106), radius=10, outline=ACCENT, width=4)
    _paste_center(img, sprite(ITEMS[index], 64), 120, 64)

    d.text((120, 116), ITEMS[index], font=F_MED,
           fill=ACCENT if selected else FG, anchor="mm")
    for i in range(n):
        x = 120 + (i - (n - 1) / 2) * 10
        d.ellipse((x - 2, 129, x + 2, 133), fill=FG if i == index else DIM)
    return img


def confirm(index: int, status: str, heard: str = "") -> Image.Image:
    """'Do you want this one?' with the mic showing whether we're listening."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    _status_bar(d, status, "joystick press = yes")

    d.rounded_rectangle((8, 28, 84, 104), radius=10, outline=ACCENT, width=3)
    _paste_center(img, sprite(ITEMS[index], 60), 46, 66)

    d.text((162, 36), f"{ITEMS[index]}?", font=F_BIG, fill=FG, anchor="mm")
    color = STATUS_COLORS[status]
    if status == "THINKING":
        for i in range(3):
            d.ellipse((140 + i * 16, 62, 150 + i * 16, 72), fill=color)
    else:
        _mic(d, 162, 70, color)
    label = {"LISTENING": "Say YES or NO", "THINKING": "Got it...",
             "TALKING": "Do you want it?"}[status]
    d.text((162, 100), label, font=F_MED, fill=color, anchor="mm")
    if heard:
        d.text((WIDTH // 2, 124), f'heard: "{heard[:30]}"', font=F_SMALL,
               fill=DIM, anchor="mm")
    return img


def dispense_frames(index: int) -> list[Image.Image]:
    """Item drops from its slot into the tray, then flies out at the viewer."""
    name = ITEMS[index]
    frames = []

    def machine() -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        d = ImageDraw.Draw(img)
        _status_bar(d, "ENJOY", "vending...")
        d.rectangle((60, 22, 180, 98), outline=DIM, width=2)        # glass window
        d.line((60, 62, 180, 62), fill=DIM, width=2)                # shelf
        d.rectangle((70, 108, 170, 128), fill=(45, 45, 60))         # pickup tray
        d.text((120, 118), "PUSH", font=F_SMALL, fill=DIM, anchor="mm")
        return img, d

    # 1. wiggle on the shelf
    for i in range(6):
        img, _ = machine()
        _paste_center(img, sprite(name, 34), 120 + (3 if i % 2 else -3), 44)
        frames.append(img)
    # 2. fall with gravity into the tray
    for i in range(10):
        img, _ = machine()
        t = (i + 1) / 10
        _paste_center(img, sprite(name, 34), 120, int(44 + 74 * t * t))
        frames.append(img)
    # 3. fly out toward the viewer, growing past the edges of the screen
    for i in range(14):
        t = (i + 1) / 14
        img, d = machine()
        size = int(34 + 230 * t ** 2)
        cy = int(118 - 50 * math.sin(t * math.pi / 2))
        for k in range(8):                                          # speed lines
            ang = k * math.pi / 4 + 0.3
            r0, r1 = 30 + 60 * t, 60 + 120 * t
            d.line((120 + r0 * math.cos(ang), cy + r0 * math.sin(ang),
                    120 + r1 * math.cos(ang), cy + r1 * math.sin(ang)),
                   fill=ACCENT, width=2)
        _paste_center(img, sprite(name, size), 120, cy)
        frames.append(img)
    # 4. enjoy card
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    _status_bar(d, "ENJOY", "move joystick for more")
    _paste_center(img, sprite(name, 70), 120, 62)
    d.text((120, 116), f"Enjoy your {name}!", font=F_MED, fill=ACCENT, anchor="mm")
    frames.append(img)
    return frames


if __name__ == "__main__":
    # Writes every screen to ./preview/ so you can check the art on a laptop.
    out = Path(__file__).parent / "preview"
    out.mkdir(exist_ok=True)
    browse(1).save(out / "browse.png")
    browse(1, selected=True, status="TALKING").save(out / "selected.png")
    for s in ("TALKING", "LISTENING", "THINKING"):
        confirm(1, s, heard="yeah" if s == "THINKING" else "").save(out / f"confirm_{s.lower()}.png")
    frames = dispense_frames(1)
    frames[0].save(out / "dispense.gif", save_all=True, append_images=frames[1:],
                   duration=60, loop=0)
    print(f"wrote previews to {out}")


def payment(index: int, price_cents: int, stage: str, status: str = "LISTENING") -> Image.Image:
    """Payment prompt artwork for the two-button vending demo."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    _status_bar(d, status, "DEMO PAYMENT")
    d.text((120, 34), f"{ITEMS[index]}  ${price_cents / 100:.2f}", font=F_MED, fill=ACCENT, anchor="mm")
    lines = {
        "method": ("Cash or card?", "NEXT=cash  SELECT=card"),
        "card": ("Say 4 digits", "Example: one two three four"),
        "cash": ("How much cash?", "Example: two dollars"),
        "failed": ("Payment stopped", "Returning to snacks..."),
    }
    title, hint = lines[stage]
    d.text((120, 66), title, font=F_BIG, fill=FG, anchor="mm")
    d.text((120, 94), hint, font=F_SMALL, fill=FG, anchor="mm")
    footer = "NEXT cancels" if stage in ("card", "cash") else "Simulated payment"
    d.text((120, 121), footer, font=F_SMALL, fill=DIM, anchor="mm")
    return img