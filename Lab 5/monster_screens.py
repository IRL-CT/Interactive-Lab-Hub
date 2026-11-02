"""Everything the monster draws on the 240x135 MiniPiTFT.

Pure PIL, like Lab 3's screens.py: every function returns an RGB image, so you can
preview all the screens on a laptop without a Pi:

    python monster_screens.py        # writes previews/*.png
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 240, 135

BG = (6, 4, 12)
BODY = (58, 30, 92)
BODY_EDGE = (88, 50, 130)
BED = (35, 28, 24)
EYE = (245, 240, 210)
PUPIL = (20, 10, 30)
ANGRY_EYE = (255, 70, 50)
TEXT = (235, 230, 245)
DIM = (120, 110, 140)

LEVEL_NAMES = ["calm", "annoyed", "grumpy", "furious"]

_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]


def font(size: int) -> ImageFont.ImageFont:
    for path in _FONT_PATHS:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


F_SMALL, F_MED, F_BIG, F_HUGE = font(11), font(14), font(20), font(46)


def _dim(img: Image.Image, factor: float) -> Image.Image:
    """Night screens are drawn dark so the glow under the bed stays soft."""
    if factor >= 1:
        return img
    return Image.eval(img, lambda v: int(v * factor))


def _monster(d: ImageDraw.ImageDraw, cx: int, cy: int, level: int, eyes: str) -> None:
    """The monster peeking out from under the bed frame.

    eyes: "closed", "one" (one eye open), "open", "wide" (countdown), "squint" (thinking)
    level: 0..3, sets brows, eye color and steam.
    """
    # body: a blob rising from the bottom of the screen
    d.ellipse((cx - 70, cy - 40, cx + 70, cy + 80), fill=BODY, outline=BODY_EDGE, width=2)
    # little horns
    for side in (-1, 1):
        hx = cx + side * 42
        d.polygon([(hx - 9, cy - 28), (hx + 9, cy - 28), (hx + side * 6, cy - 50)], fill=BODY_EDGE)

    eye_color = ANGRY_EYE if level >= 3 else EYE
    for i, side in enumerate((-1, 1)):
        ex, ey = cx + side * 26, cy + 2
        state = eyes
        if eyes == "one":
            state = "open" if side == 1 else "closed"
        if state == "closed":
            d.arc((ex - 14, ey - 8, ex + 14, ey + 10), 20, 160, fill=EYE, width=3)
        elif state == "squint":
            d.line((ex - 13, ey + 2, ex + 13, ey + 2), fill=EYE, width=3)
        else:
            r = 16 if state == "wide" else 13
            d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=eye_color)
            pr = 6 if state == "wide" else 5
            py = ey - 4 if state == "wide" else ey + 1        # wide eyes look up at you in bed
            d.ellipse((ex - pr, py - pr, ex + pr, py + pr), fill=PUPIL)
        # brows: flat when calm, angled down toward the middle as anger grows
        if level >= 1:
            tilt = 4 + 4 * level
            inner, outer = ex - side * 14, ex + side * 14
            d.line((outer, ey - 20, inner, ey - 20 + tilt), fill=BODY_EDGE if level < 3 else (200, 40, 40),
                   width=4)

    # mouth
    if level == 0:
        d.arc((cx - 12, cy + 22, cx + 12, cy + 34), 20, 160, fill=EYE, width=2)
    else:
        teeth = 3 + level
        x0, w = cx - 6 * teeth, 12
        d.line((x0, cy + 28, x0 + w * teeth, cy + 28), fill=EYE, width=2)
        for t in range(teeth):
            x = x0 + t * w
            d.polygon([(x, cy + 28), (x + w, cy + 28), (x + w / 2, cy + 36)], fill=EYE)

    # steam when furious
    if level >= 3:
        for side in (-1, 1):
            sx = cx + side * 62
            for k in range(3):
                d.ellipse((sx - 5 + side * k * 4, cy - 34 - k * 10, sx + 5 + side * k * 4, cy - 24 - k * 10),
                          outline=DIM, width=2)


def _bed_edge(d: ImageDraw.ImageDraw) -> None:
    d.rectangle((0, 0, WIDTH, 14), fill=BED)
    d.line((0, 14, WIDTH, 14), fill=(70, 55, 45), width=2)


def idle() -> Image.Image:
    """Daytime: the monster has faded away (the PiTFT backlight is off, so this is invisible there).
    In the preview window you see a faint sleeping monster and the hint for bedtime."""
    img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    d = ImageDraw.Draw(img)
    _monster(d, WIDTH // 2, 100, 0, "closed")
    img = _dim(img, 0.25)
    d = ImageDraw.Draw(img)
    d.text((WIDTH // 2, 12), 'say "I\'m going to sleep"', font=F_SMALL, fill=(90, 85, 105), anchor="mm")
    return img


def countdown(seconds_left: int, last_night: str = "") -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    _bed_edge(d)
    _monster(d, 78, 80, 0, "wide")
    d.text((190, 62), str(seconds_left), font=F_HUGE, fill=TEXT, anchor="mm")
    d.text((190, 100), "get in bed!", font=F_SMALL, fill=DIM, anchor="mm")
    if last_night:
        d.text((WIDTH // 2, 7), last_night, font=F_SMALL, fill=DIM, anchor="mm")
    return img


FACES = {0: "closed", 1: "one", 2: "open", 3: "open"}   # 0 asleep, 1 one eye, 2 both eyes, 3 rage


def night(stage: int, feet_now: bool, trips: int) -> Image.Image:
    """While you sleep. The face depends only on how many times you've got up:
    0 trips: asleep.  1st trip: one eye open.  2nd trip: both eyes open.  3+: rage face.
    It keeps that face after you get back in bed, and glows brighter while feet are on the floor."""
    stage = min(stage, 3)
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    _bed_edge(d)
    _monster(d, WIDTH // 2, 82, stage, FACES[stage])
    if stage == 0:
        d.text((WIDTH - 22, 34), "z", font=F_MED, fill=DIM)
        d.text((WIDTH - 32, 46), "z", font=F_SMALL, fill=DIM)
    d.text((6, HEIGHT - 6), "x" * trips if trips <= 10 else f"x{trips}", font=F_SMALL, fill=DIM, anchor="ls")
    return _dim(img, 0.8 if feet_now else 0.45)    # low glow at night, brighter while it's watching you


def dark() -> Image.Image:
    """The camera can't see: honest about it rather than pretending the floor is empty."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    _bed_edge(d)
    _monster(d, WIDTH // 2, 82, 0, "squint")
    d.text((WIDTH // 2, 30), "too dark to see", font=F_SMALL, fill=DIM, anchor="mm")
    return _dim(img, 0.45)


def thinking(level: int, facts: str) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    _bed_edge(d)
    _monster(d, 62, 92, level, "squint")
    d.text((128, 40), facts, font=F_SMALL, fill=TEXT)
    d.text((128, 100), "grr...", font=F_MED, fill=DIM)
    return img


def morning(level: int, facts: str, line: str, brightness: float = 1.0) -> Image.Image:
    """The verdict: the computed facts on top, the monster's line underneath."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    _monster(d, 50, 100, level, "open")
    d.multiline_text((112, 6), facts, font=F_SMALL, fill=TEXT, spacing=2)
    wrapped = "\n".join(textwrap.wrap(line, 20)[:5])
    d.multiline_text((112, 52), wrapped, font=F_SMALL, fill=(255, 210, 120), spacing=2)
    return _dim(img, brightness)


if __name__ == "__main__":
    out = Path("previews")
    out.mkdir(exist_ok=True)
    countdown(42, "last night: 2 trips").save(out / "1_countdown.png")
    night(0, False, 0).save(out / "2_asleep_0_trips.png")
    night(1, True, 1).save(out / "3_one_eye_1st_trip.png")
    night(2, True, 2).save(out / "4_two_eyes_2nd_trip.png")
    night(3, True, 3).save(out / "5_rage_3rd_trip.png")
    dark().save(out / "6_too_dark.png")
    facts = "2 trips\n1:12 AM, 3:40 AM\n7 min on my floor"
    thinking(2, facts).save(out / "7_thinking.png")
    morning(2, facts, "Two trips. TWO. My floor is not a hallway. Grrr.").save(out / "8_morning.png")
    morning(0, "0 trips\nquiet night", "You never left the bed. I slept like a baby. A scary baby.").save(
        out / "9_morning_quiet.png")
    print(f"wrote previews to {out}/")
