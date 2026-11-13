"""Plant clock for the 1.14-inch Adafruit Mini PiTFT (240 x 135 landscape).

Run inside the existing Raspberry Pi Lab 2 virtual environment:
    python plant_clock.py --prototype   # A: water seed into sprout; B: reset
    python plant_clock.py --demo        # simulate one day in 60 seconds
    python plant_clock.py --pick-demo   # repeat just the picking scene
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
PICK_SECONDS = 5.0
ANIMATION_FPS = 15
PICK_DEMO_SECONDS = 10.0

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


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def bezier(start, control_a, control_b, end, steps=12):
    points = []
    for index in range(steps + 1):
        t = index / steps
        u = 1 - t
        points.append(tuple(u**3 * start[i] + 3*u*u*t * control_a[i]
                            + 3*u*t*t * control_b[i] + t**3 * end[i] for i in (0, 1)))
    return points


def transform_point(point, pivot, offset=(0, 0), angle=0):
    radians = math.radians(angle)
    x, y = point[0] - pivot[0], point[1] - pivot[1]
    return (pivot[0] + offset[0] + x * math.cos(radians) - y * math.sin(radians),
            pivot[1] + offset[1] + x * math.sin(radians) + y * math.cos(radians))


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


def draw_flower(draw, center_x, center_y, variant=0, rotation=0):
    petal_colors = [(235, 113, 139), (225, 136, 190), (244, 146, 116)]
    petal_color = petal_colors[variant % len(petal_colors)]
    petal_count = 7
    for petal in range(petal_count):
        angle = (2 * math.pi * petal / petal_count) + variant * 0.12 + math.radians(rotation)
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


def plant_geometry(variant, flower=False):
    """Keep one stem and leaf arrangement through blooming and picking."""
    plant_random = random.Random(300 + variant)
    top_x = 120 + plant_random.randint(-6, 6)
    top_y = 35 if flower else 42
    leaves = []
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
        leaves.append((x, y, angle, length, green))

        # Some variants branch in both directions, making growth feel organic.
        if (variant + index) % 3 == 0:
            opposite_angle = -28 if side < 0 else 208
            leaves.append((x, y + 3, opposite_angle, length - 5, (96, 153, 77)))
    return top_x, top_y, leaves


def draw_growing_plant(draw, variant, flower=False):
    top_x, top_y, leaves = plant_geometry(variant, flower)
    # Use the same two stem sections as the picking scene for a pixel-exact join.
    sections = ((99, 60), (60, top_y)) if flower else ((99, top_y),)
    for bottom, top in sections:
        stem_x = lambda y: 120 + (top_x-120) * (99-y)/(99-top_y)
        draw.line((scaled((stem_x(bottom), bottom)), scaled((stem_x(top), top))),
                  fill=(54, 113, 62), width=4 * SCALE)
        for x, y, angle, length, color in leaves:
            if top <= y < bottom:
                draw_leaf(draw, x, y, angle, length, color)

    if flower:
        draw_flower(draw, top_x, top_y - 2, variant)
    else:
        # A small bud makes the transition toward the next state visible.
        draw.ellipse(scaled((top_x - 4, top_y - 6, top_x + 4, top_y + 3)), fill=(207, 105, 128))


def draw_hand(draw, grip, opening, angle=0, front=False):
    """A soft outlined hand. Draw the thumb in front of the held flower stem."""
    skin, shade, highlight = (235, 183, 157), (185, 125, 114), (251, 206, 178)
    gap = opening * 9

    def point(p):
        return scaled(transform_point(p, (0, 0), grip, angle))

    def shape(points, fill, outline=None):
        path = [point(p) for p in points]
        draw.polygon(path, fill=fill)
        if outline:
            draw.line(path + path[:1], fill=outline, width=SCALE, joint="curve")

    if not front:
        # Palm and forearm, then the curved index finger reaching over the stem.
        palm = bezier((112, -14), (82, -14), (64, -14), (48, -12))
        palm += bezier((48, -12), (30, -15), (16, -22-gap/3), (1, -6-gap))
        palm += bezier((1, -6-gap), (-6, -2-gap), (-4, 3-gap), (2, 3-gap))
        palm += bezier((2, 3-gap), (13, 0-gap/2), (18, -8), (27, -3))
        palm += bezier((27, -3), (25, 1), (17, 6), (20, 14))
        palm += bezier((20, 14), (27, 25), (44, 23), (57, 16))
        palm += bezier((57, 16), (77, 14), (94, 16), (112, 16))
        shape(palm, skin, shade)
        # Three quiet creases distinguish curled fingers from the palm.
        for x in (28, 37, 46):
            crease = bezier((x, 11), (x-2, 17), (x+2, 20), (x+7, 18), 8)
            draw.line([point(p) for p in crease], fill=(208, 145, 128), width=SCALE)
        # Pale sleeve/cuff makes the arm entrance easy to read on the tiny display.
        shape([(78, -15), (112, -16), (112, 18), (78, 17)], (191, 198, 219), (139, 153, 181))
        draw.line([point((82, -13)), point((82, 16))], fill=(227, 229, 237), width=2*SCALE)
    else:
        thumb = bezier((39, 7), (29, 7), (20, 13+gap/2), (6, 6+gap))
        thumb += bezier((6, 6+gap), (-4, 1+gap), (-6, 9+gap), (2, 13+gap))
        thumb += bezier((2, 13+gap), (21, 25+gap/2), (37, 23), (47, 13))
        shape(thumb, highlight, shade)
        nail = bezier((2, 6+gap), (5, 5+gap), (10, 8+gap), (10, 10+gap), 8)
        nail += bezier((10, 10+gap), (7, 12+gap), (1, 9+gap), (2, 6+gap), 8)
        shape(nail, (250, 223, 203))


def draw_falling_petals(draw, variant, center, progress):
    color = [(235, 113, 139), (225, 136, 190), (244, 146, 116)][variant % 3]
    for i, (dx, start_y, delay) in enumerate(((-13, 6, 0), (19, 14, 0.12))):
        fall = max(0.0, min(1.0, (progress - delay) / (1-delay)))
        if progress < delay:
            continue
        x = center[0] + dx * fall + math.sin(fall*math.pi*3+i)*5*math.sin(fall*math.pi)
        y = center[1] + start_y + (99-center[1]-start_y) * smoothstep(fall)
        # A petal curls, falls, then comes to rest on the soil.
        angle = 24 + i*95 + fall*140
        points = bezier((-4, 0), (-2, -4), (4, -3), (5, 0), 8)
        points += bezier((5, 0), (1, 3), (-3, 3), (-4, 0), 8)
        draw.polygon([scaled(transform_point(p, (0, 0), (x, y), angle)) for p in points], fill=color)


def draw_picked_scene(draw, variant, progress=1.0):
    """Reach, close fingers, gently bend, detach, carry away, settle."""
    progress = max(0.0, min(1.0, progress))
    top_x, top_y, leaves = plant_geometry(variant, flower=True)
    cut_y = 60
    cut = (120 + (top_x-120) * (99-cut_y)/(99-top_y), cut_y)
    grip_local = (120 + (top_x-120) * (99-47)/(99-top_y), 47)
    reach = smoothstep((progress-0.08)/0.30)
    close = smoothstep((progress-0.38)/0.12)
    bend = smoothstep((progress-0.50)/0.08)
    carry = smoothstep((progress-0.58)/0.34)
    detached = progress >= 0.58
    angle = 8*bend + 15*carry
    offset = (185*carry, -34*carry - 8*math.sin(carry*math.pi))
    upper = lambda p: transform_point(p, cut, offset, angle)

    # Rooted part keeps exactly the same geometry and leaf variant as the flower.
    draw.line((scaled((120, 99)), scaled(cut)), fill=(54, 113, 62), width=4*SCALE)
    for x, y, leaf_angle, length, color in leaves:
        if y >= cut_y:
            draw_leaf(draw, x, y, leaf_angle, length, color)
    if detached:
        draw.line((scaled((cut[0]-2, cut[1]+1)), scaled((cut[0]+2, cut[1]-1))),
                  fill=(149, 172, 104), width=SCALE)

    grip = upper(grip_local)
    hand_grip = (grip[0] + (1-reach)*168, grip[1] - (1-reach)*13)
    hand_angle = -5*carry
    hand_visible = 0.08 < progress < 0.96
    if hand_visible:
        draw_hand(draw, hand_grip, 1-close, hand_angle, front=False)

    # Flower, upper stem and upper leaves travel together, held at the same grip.
    if progress < 0.96:
        draw.line((scaled(upper(cut)), scaled(upper((top_x, top_y)))),
                  fill=(54, 113, 62), width=4*SCALE)
        for x, y, leaf_angle, length, color in leaves:
            if y < cut_y:
                nx, ny = upper((x, y))
                draw_leaf(draw, nx, ny, leaf_angle+angle, length, color)
        flower_center = upper((top_x, top_y-2))
        draw_flower(draw, *flower_center, variant, rotation=angle)
    if hand_visible:
        draw_hand(draw, hand_grip, 1-close, hand_angle, front=True)
    if detached:
        draw_falling_petals(draw, variant, (top_x, top_y-2), (progress-0.58)/0.42)


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


def render_scene(stage, variant=0, watering_phase=None, clock_text=None, mode_label="", pick_progress=None):
    """Create one complete 240 x 135 frame using only Pillow drawing."""
    image, draw = draw_background(stage)
    if stage == 4 and pick_progress is not None and pick_progress < 0.22:
        image = Image.blend(background_image(3), image, smoothstep(pick_progress/0.22))
        draw = ImageDraw.Draw(image)

    if stage == 0:
        draw_seed(draw)
    elif stage == 1:
        draw_sprout(draw, variant)
    elif stage == 2:
        draw_growing_plant(draw, variant, flower=False)
    elif stage == 3:
        draw_growing_plant(draw, variant, flower=True)
    else:
        draw_picked_scene(draw, variant, 1.0 if pick_progress is None else pick_progress)

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
        self.pick_started = None
        self.update(datetime.now() if now is None else now, 0.0)

    def update(self, now, elapsed):
        if self.mode == "pick-demo":
            self.now = now.replace(hour=20, minute=59, second=58, microsecond=0) + timedelta(seconds=elapsed % PICK_DEMO_SECONDS)
        else:
            self.now = demo_datetime(elapsed, now) if self.mode == "demo" else now
        cycle_length = {"demo": DEMO_DAY_SECONDS, "pick-demo": PICK_DEMO_SECONDS}.get(self.mode)
        day_key = (now.date(), int(elapsed // cycle_length) if cycle_length else 0)
        new_day = self.day_key != day_key
        if self.day_key != day_key:
            self.day_key = day_key
            self.variant = (now.date().toordinal() + day_key[1]) % 9
        if self.mode != "prototype":
            next_stage = stage_from_time(self.now)
            if next_stage == 4 and (self.stage != 4 or new_day):
                self.pick_started = elapsed
                self.watering_until = 0.0
            elif next_stage != 4:
                self.pick_started = None
            self.stage = next_stage

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
        label = {"clock": "", "prototype": "TEST", "demo": "DEMO", "pick-demo": "DEMO"}[self.mode]
        pick_progress = None
        if self.stage == 4:
            elapsed_pick = PICK_SECONDS if self.pick_started is None else max(0, elapsed-self.pick_started)
            # At most 15 drawing updates per second, independent of clock polling.
            pick_progress = min(1.0, int(elapsed_pick*ANIMATION_FPS)/(PICK_SECONDS*ANIMATION_FPS))
        return self.stage, self.variant, phase, text, label, pick_progress


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
    modes.add_argument("--pick-demo", action="store_true")
    args = parser.parse_args()
    mode = "prototype" if args.prototype else "demo" if args.demo else "pick-demo" if args.pick_demo else "clock"

    # Hardware imports live here so render_scene() can also be previewed on a laptop.
    import board
    import digitalio
    import adafruit_rgb_display.st7789 as st7789

    # Match the CS setting in Yangchen's working screen_clock.py on this Pi.
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
    last_draw_at = -1.0 / ANIMATION_FPS
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
            if state != last_frame and elapsed-last_draw_at >= 1.0/ANIMATION_FPS:
                display.image(render_scene(*state), DISPLAY_ROTATION)
                last_frame = state
                last_draw_at = elapsed
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
