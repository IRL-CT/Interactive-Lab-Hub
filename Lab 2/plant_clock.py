"""Plant clock for the 1.14-inch Adafruit Mini PiTFT (240 x 135 landscape).

Run inside the existing Raspberry Pi Lab 2 virtual environment:
    python plant_clock.py --prototype   # A: water seed into sprout; B: reset
    python plant_clock.py --demo        # simulate one day in 60 seconds
    python plant_clock.py               # real local time; A: water, B: time on/off

No image files are required. Pillow draws every frame.
Concept: Yangchen Jin. Implementation and debugging assistance: OpenAI ChatGPT.
Hardware reference:
https://learn.adafruit.com/adafruit-mini-pitft-135x240-color-tft-add-on-for-raspberry-pi/pinouts
"""

import argparse
from datetime import datetime, timedelta
from functools import lru_cache
import math
import random
import time

from PIL import Image, ImageDraw, ImageFont


SCREEN_WIDTH = 240
SCREEN_HEIGHT = 135
SCALE = 3  # Draw large, then shrink for smoother shapes on the tiny display.
DISPLAY_ROTATION = 90  # Change to 270 if the picture is upside down on your Pi.
STAGE_START_HOURS = (0, 6, 10, 15, 21)
DEMO_DAY_SECONDS = 60

# Each stage also has its own time-of-day sky.
PALETTES = [
    ((25, 31, 61), (91, 78, 117), (72, 49, 45)),      # seed / night
    ((250, 192, 164), (255, 232, 190), (104, 72, 50)), # sprout / dawn
    ((121, 201, 221), (229, 241, 209), (111, 78, 50)), # growth / day
    ((244, 180, 117), (251, 224, 171), (102, 69, 49)), # flower / sunset
    ((79, 67, 113), (181, 121, 139), (66, 45, 48)),    # picked / dusk
]


def scaled(values):
    return tuple(round(value * SCALE) for value in values)


def interpolate_color(start, end, amount):
    return tuple(
        round(start[channel] + (end[channel] - start[channel]) * amount)
        for channel in range(3)
    )


@lru_cache(maxsize=5)
def background_image(stage):
    top, bottom, soil = PALETTES[stage]
    image = Image.new("RGB", (SCREEN_WIDTH * SCALE, SCREEN_HEIGHT * SCALE))
    draw = ImageDraw.Draw(image)

    # Vertical sky gradient.
    for y in range(SCREEN_HEIGHT * SCALE):
        amount = y / (SCREEN_HEIGHT * SCALE - 1)
        draw.line(
            ((0, y), (SCREEN_WIDTH * SCALE, y)),
            fill=interpolate_color(top, bottom, amount),
        )

    # Sun or moon gives another subtle indication of time.
    celestial_positions = [(205, 25), (34, 29), (120, 18), (203, 31), (211, 22)]
    cx, cy = celestial_positions[stage]
    glow = (236, 236, 213) if stage in (0, 4) else (255, 235, 165)
    draw.ellipse(scaled((cx - 9, cy - 9, cx + 9, cy + 9)), fill=glow)

    # Soil and a few quiet specks.
    draw.rectangle(scaled((0, 98, SCREEN_WIDTH, SCREEN_HEIGHT)), fill=soil)
    speck_random = random.Random(91)
    for _ in range(34):
        x = speck_random.randrange(4, 237)
        y = speck_random.randrange(104, 133)
        shade = tuple(max(0, channel - 15) for channel in soil)
        draw.ellipse(scaled((x, y, x + 1.5, y + 1.5)), fill=shade)

    return image


def draw_background(stage):
    image = background_image(stage).copy()
    return image, ImageDraw.Draw(image)


def draw_leaf(draw, base_x, base_y, angle_degrees, length, color):
    """Draw one pointed leaf from a stem without needing an image asset."""
    angle = math.radians(angle_degrees)
    direction_x = math.cos(angle)
    direction_y = math.sin(angle)
    tip_x = base_x + direction_x * length
    tip_y = base_y + direction_y * length
    middle_x = base_x + direction_x * length * 0.52
    middle_y = base_y + direction_y * length * 0.52
    perpendicular_x = -direction_y * length * 0.20
    perpendicular_y = direction_x * length * 0.20

    points = [
        (base_x, base_y),
        (middle_x + perpendicular_x, middle_y + perpendicular_y),
        (tip_x, tip_y),
        (middle_x - perpendicular_x, middle_y - perpendicular_y),
    ]
    draw.polygon([scaled(point) for point in points], fill=color)
    draw.line(
        (scaled((base_x, base_y)), scaled((tip_x, tip_y))),
        fill=(62, 105, 67),
        width=SCALE,
    )


def draw_flower(draw, center_x, center_y, variant=0):
    petal_colors = [(235, 113, 139), (225, 136, 190), (244, 146, 116)]
    petal_color = petal_colors[variant % len(petal_colors)]
    petal_count = 7
    for petal in range(petal_count):
        angle = (2 * math.pi * petal / petal_count) + variant * 0.12
        px = center_x + math.cos(angle) * 10
        py = center_y + math.sin(angle) * 8
        draw.ellipse(scaled((px - 6, py - 5, px + 6, py + 5)), fill=petal_color)
    draw.ellipse(
        scaled((center_x - 5, center_y - 5, center_x + 5, center_y + 5)),
        fill=(239, 189, 66),
    )


def draw_seed(draw):
    draw.ellipse(scaled((111, 106, 129, 118)), fill=(190, 125, 72))
    draw.arc(scaled((115, 107, 128, 117)), 190, 325, fill=(111, 73, 47), width=2 * SCALE)
    draw.line((scaled((120, 106)), scaled((120, 100))), fill=(110, 158, 83), width=2 * SCALE)


def draw_sprout(draw, variant):
    lean = (variant % 9) - 4
    draw.line(
        (scaled((120, 99)), scaled((120 + lean, 73))),
        fill=(70, 126, 69),
        width=3 * SCALE,
    )
    draw_leaf(draw, 120 + lean * 0.55, 84, 205, 18, (91, 157, 84))
    draw_leaf(draw, 120 + lean * 0.8, 78, -28, 18, (111, 174, 91))


def draw_growing_plant(draw, variant, flower=False):
    plant_random = random.Random(300 + variant)
    top_x = 120 + plant_random.randint(-6, 6)
    top_y = 35 if flower else 42

    draw.line(
        (scaled((120, 99)), scaled((top_x, top_y))),
        fill=(54, 113, 62),
        width=4 * SCALE,
    )

    leaf_levels = [82, 68, 54]
    if flower:
        leaf_levels.append(44)

    for index, y in enumerate(leaf_levels):
        x = 120 + (top_x - 120) * ((99 - y) / (99 - top_y))
        side = -1 if (index + variant) % 2 == 0 else 1
        angle = 205 if side < 0 else -25
        angle += plant_random.randint(-9, 9)
        length = plant_random.randint(19, 26)
        green = (74 + index * 5, 137 + index * 4, 71)
        draw_leaf(draw, x, y, angle, length, green)

        # Some variants branch in both directions, making growth feel organic.
        if (variant + index) % 3 == 0:
            opposite_angle = -28 if side < 0 else 208
            draw_leaf(draw, x, y + 3, opposite_angle, length - 5, (96, 153, 77))

    if flower:
        draw_flower(draw, top_x, top_y - 2, variant)
    else:
        # A small bud makes the transition toward the next state visible.
        draw.ellipse(scaled((top_x - 4, top_y - 6, top_x + 4, top_y + 3)), fill=(207, 105, 128))


def draw_picked_scene(draw, variant):
    # The plant remains, but its flower is gone.
    draw.line(
        (scaled((120, 99)), scaled((116, 48))),
        fill=(54, 103, 60),
        width=4 * SCALE,
    )
    draw_leaf(draw, 118, 77, 206, 22, (74, 127, 73))
    draw_leaf(draw, 117, 63, -27, 22, (89, 139, 78))
    draw.line((scaled((112, 49)), scaled((120, 46))), fill=(81, 75, 56), width=2 * SCALE)

    # A hand enters from the upper-right holding the flower by its stem.
    skin = (224, 177, 150)
    draw.polygon(
        [scaled(point) for point in [(240, 13), (240, 51), (207, 45), (184, 37), (188, 29), (211, 35)]],
        fill=skin,
    )
    draw.line((scaled((190, 36)), scaled((171, 48))), fill=(53, 102, 58), width=3 * SCALE)
    draw.ellipse(scaled((180, 29, 194, 41)), fill=skin)
    draw_flower(draw, 168, 49, variant)

    # Two drifting petals sell the sense of motion without a full animation.
    draw.ellipse(scaled((145, 59, 153, 64)), fill=(232, 119, 145))
    draw.ellipse(scaled((158, 74, 165, 79)), fill=(240, 139, 157))


def draw_watering_overlay(draw, phase):
    # Watering can entering from the left.
    can_color = (77, 133, 145)
    draw.rounded_rectangle(scaled((12, 55, 49, 82)), radius=7 * SCALE, fill=can_color)
    draw.arc(scaled((4, 44, 38, 76)), 210, 70, fill=(54, 103, 115), width=4 * SCALE)
    draw.polygon(
        [scaled(point) for point in [(46, 59), (84, 67), (82, 73), (45, 70)]],
        fill=can_color,
    )
    draw.ellipse(scaled((79, 65, 90, 75)), fill=(62, 113, 125))

    # Droplets move downward as phase increases.
    for index in range(5):
        x = 91 + index * 7
        y = 70 + ((phase * 7 + index * 9) % 28)
        draw.ellipse(scaled((x, y, x + 3, y + 6)), fill=(117, 201, 223))


@lru_cache(maxsize=1)
def clock_font():
    for name in ("DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, 13 * SCALE)
        except OSError:
            pass
    # Older Pillow versions may not accept a size argument for load_default().
    return None


def draw_clock_label(draw, clock_text, mode_label):
    label = (clock_text + ("  " + mode_label if mode_label else "")).strip()
    font = clock_font()
    if font is None:
        return  # The fallback label is drawn after resizing, at native resolution.
    box = draw.textbbox((0, 0), label, font=font)
    width = (box[2] - box[0]) / SCALE + 12
    draw.rounded_rectangle(scaled((4, 4, 4 + width, 25)), radius=4 * SCALE, fill=(30, 36, 45))
    draw.text(scaled((10, 5)), label, font=font, fill=(250, 243, 220))


def render_scene(stage, variant=0, watering_phase=None, clock_text=None, mode_label=""):
    """Create one complete 240 x 135 frame using only Pillow drawing."""
    image, draw = draw_background(stage)

    if stage == 0:
        draw_seed(draw)
    elif stage == 1:
        draw_sprout(draw, variant)
    elif stage == 2:
        draw_growing_plant(draw, variant, flower=False)
    elif stage == 3:
        draw_growing_plant(draw, variant, flower=True)
    else:
        draw_picked_scene(draw, variant)

    if watering_phase is not None and stage < 4:
        draw_watering_overlay(draw, watering_phase)

    if clock_text is not None or mode_label:
        draw_clock_label(draw, clock_text or "", mode_label)
    result = image.resize(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        getattr(Image, "Resampling", Image).LANCZOS,
    )
    if (clock_text is not None or mode_label) and clock_font() is None:
        draw = ImageDraw.Draw(result)
        label = ((clock_text or "") + ("  " + mode_label if mode_label else "")).strip()
        box = draw.textbbox((0, 0), label)
        draw.rectangle((4, 4, box[2] - box[0] + 16, 24), fill=(30, 36, 45))
        draw.text((10, 7), label, fill=(250, 243, 220))
    return result


def stage_from_time(now=None):
    """The same mapping is used by the real clock and the accelerated demo."""
    now = datetime.now() if now is None else now
    return sum(now.hour >= hour for hour in STAGE_START_HOURS) - 1


def demo_datetime(elapsed, day):
    midnight = day.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds = (elapsed % DEMO_DAY_SECONDS) / DEMO_DAY_SECONDS * 86400
    return midnight + timedelta(seconds=seconds)


class PlantClock:
    """Clock/interaction logic, separated from the hardware for verification."""

    def __init__(self, mode="clock", now=None):
        self.mode = mode
        self.show_time = True
        self.day_key = None
        self.stage = 0
        self.variant = 0
        self.watering_until = 0.0
        self.update(datetime.now() if now is None else now, 0.0)

    def update(self, now, elapsed):
        self.now = demo_datetime(elapsed, now) if self.mode == "demo" else now
        day_key = (now.date(), int(elapsed // DEMO_DAY_SECONDS) if self.mode == "demo" else 0)
        if self.day_key != day_key:
            self.day_key = day_key
            self.variant = (now.date().toordinal() + day_key[1]) % 9
        if self.mode != "prototype":
            self.stage = stage_from_time(self.now)

    def water(self, elapsed):
        if self.stage == 4 or elapsed < self.watering_until:
            return
        self.watering_until = elapsed + 1.2
        self.variant = (self.variant + random.randrange(1, 9)) % 9
        if self.mode == "prototype":
            self.stage = 1  # The first iteration only demonstrates seed -> sprout.

    def press_b(self):
        if self.mode == "prototype":
            self.stage = 0
            self.watering_until = 0.0
        else:
            self.show_time = not self.show_time

    def frame_state(self, elapsed):
        phase = int(elapsed * 15) % 12 if elapsed < self.watering_until and self.stage < 4 else None
        # The DEMO label stays visible even when B hides the digital time.
        text = self.now.strftime("%H:%M") if self.show_time else None
        label = {"clock": "", "prototype": "TEST", "demo": "DEMO"}[self.mode]
        return self.stage, self.variant, phase, text, label


class Button:
    """Debounce: one event per press, including when a button is held down."""

    def __init__(self, pin):
        self.pin = pin
        self.raw = True
        self.stable = True
        self.changed_at = 0.0

    def pressed(self, now):
        value = self.pin.value
        if value != self.raw:
            self.raw = value
            self.changed_at = now
        if value != self.stable and now - self.changed_at >= 0.03:
            self.stable = value
            return not value
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--prototype", action="store_true")
    modes.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    mode = "prototype" if args.prototype else "demo" if args.demo else "clock"

    # Hardware imports live here so render_scene() can also be previewed on a laptop.
    import board
    import digitalio
    import adafruit_rgb_display.st7789 as st7789

    cs_pin = digitalio.DigitalInOut(board.D5)
    dc_pin = digitalio.DigitalInOut(board.D25)
    spi = board.SPI()

    display = st7789.ST7789(
        spi,
        cs=cs_pin,
        dc=dc_pin,
        rst=None,
        baudrate=24_000_000,
        width=135,
        height=240,
        x_offset=53,
        y_offset=40,
    )

    backlight = digitalio.DigitalInOut(board.D22)
    backlight.switch_to_output(value=True)

    # Built-in Mini PiTFT buttons; LOW means pressed.
    button_a = digitalio.DigitalInOut(board.D23)
    button_b = digitalio.DigitalInOut(board.D24)
    button_a.switch_to_input(pull=digitalio.Pull.UP)
    button_b.switch_to_input(pull=digitalio.Pull.UP)

    model = PlantClock(mode)
    a, b = Button(button_a), Button(button_b)
    started = time.monotonic()
    last_frame = None
    print("Mode:", mode, "| A: water | B:", "reset" if mode == "prototype" else "toggle time")
    print("Press Ctrl+C to stop. Pi local time:", datetime.now().astimezone().isoformat(timespec="seconds"))
    try:
        while True:
            elapsed = time.monotonic() - started
            model.update(datetime.now(), elapsed)
            if a.pressed(elapsed):
                model.water(elapsed)
            if b.pressed(elapsed):
                model.press_b()
            state = model.frame_state(elapsed)
            if state != last_frame:
                display.image(render_scene(*state), DISPLAY_ROTATION)
                last_frame = state
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        backlight.value = False
        for pin in (button_a, button_b, backlight, cs_pin, dc_pin):
            pin.deinit()
        spi.deinit()


if __name__ == "__main__":
    main()
