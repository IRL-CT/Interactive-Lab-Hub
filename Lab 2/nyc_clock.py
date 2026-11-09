# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
NYC skyline clock.

Renders a day/night NYC skyline with the sun (7am-7pm) or moon (7pm-6am)
following an hourly arc across the screen.

The NYCClock class is usable from another script, e.g. screen_clock.py:

    clock = NYCClock(width, height)
    frame = clock.frame()   # RGB Image sized (width, height)
    disp.image(frame, rotation)

Running this file directly (`python3 nyc_clock.py`) sets up its own display
and loops forever.
"""

import math
from datetime import datetime
from PIL import Image

DAY_BG = "images/daytimeNYCskyline.jpeg"
NIGHT_BG = "images/nighttimeNYCskyline.jpeg"
SUN_SPRITE = "images/sunsprite.webp"
MOON_SPRITE = "images/moonsprite.gif"

SPRITE_WIDTH = 56
SOLAR_START_HOUR = 7    # sun rises (leftmost) at 7am
SOLAR_END_HOUR = 19     # sun sets (rightmost); night picture starts at 7pm
LUNAR_START_HOUR = 19   # moon rises (leftmost) when night falls at 7pm
LUNAR_END_HOUR = 6      # moon sets (rightmost) at 6am


def load_background(path, width, height):
    image = Image.open(path)

    # Scale the image to the smaller screen dimension
    image_ratio = image.width / image.height
    screen_ratio = width / height
    if screen_ratio < image_ratio:
        scaled_width = image.width * height // image.height
        scaled_height = height
    else:
        scaled_width = width
        scaled_height = image.height * width // image.width
    image = image.resize((scaled_width, scaled_height), Image.BICUBIC)

    # Crop and center the image
    x = scaled_width // 2 - width // 2
    y = scaled_height // 2 - height // 2
    image = image.crop((x, y, x + width, y + height))

    return image.convert("RGB")


def load_sprite(path, target_width):
    image = Image.open(path).convert("RGBA")
    scaled_height = round(image.height * target_width / image.width)
    return image.resize((target_width, scaled_height), Image.BICUBIC)


class NYCClock:
    """Renders a day/night NYC skyline frame for a (width, height) screen."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.day_bg = load_background(DAY_BG, width, height)
        self.night_bg = load_background(NIGHT_BG, width, height)
        self.sun_sprite = load_sprite(SUN_SPRITE, SPRITE_WIDTH)
        self.moon_sprite = load_sprite(MOON_SPRITE, SPRITE_WIDTH)

    def _sprite_position(self, t, sprite):
        # t travels 0 (left, mid-height) -> 0.5 (center, top) -> 1 (right, mid-height)
        sh = sprite.height
        mid = self.height // 2  # start/end at the vertical middle of the picture
        amp = (self.height - sh) // 2  # arc top stays just on screen
        x = t * self.width  # centered on the left edge to centered on the right edge
        y = mid - math.sin(math.pi * t) * amp
        return int(x), int(y)

    def _paste_sprite(self, frame, sprite, cx, cy):
        sw, sh = sprite.size
        x = int(cx - sw / 2)
        y = int(cy - sh / 2)
        frame.paste(sprite, (x, y), sprite)

    def frame(self, hour=None):
        """Return an RGB Image of the skyline for `hour` (default: current hour)."""
        if hour is None:
            hour = datetime.now().hour

        if SOLAR_START_HOUR <= hour < SOLAR_END_HOUR:
            # Daytime sky with the sun, one step per hour from 7am-7pm.
            frame = self.day_bg.copy()
            t = (hour - SOLAR_START_HOUR) / (SOLAR_END_HOUR - SOLAR_START_HOUR)
            self._paste_sprite(
                frame, self.sun_sprite, *self._sprite_position(t, self.sun_sprite)
            )
        else:
            # Nighttime sky with the moon, one step per hour from 7pm-6am.
            frame = self.night_bg.copy()
            if hour >= LUNAR_START_HOUR or hour <= LUNAR_END_HOUR:
                p = (hour - LUNAR_START_HOUR) % 24
                t = p / ((LUNAR_END_HOUR - LUNAR_START_HOUR) % 24)
                self._paste_sprite(
                    frame, self.moon_sprite, *self._sprite_position(t, self.moon_sprite)
                )

        return frame


if __name__ == "__main__":
    import digitalio
    import board
    import adafruit_rgb_display.st7789 as st7789
    from time import sleep

    # Configuration for CS and DC pins (these are PiTFT defaults):
    cs_pin = digitalio.DigitalInOut(board.D5)
    dc_pin = digitalio.DigitalInOut(board.D25)
    reset_pin = digitalio.DigitalInOut(board.D24)

    # Config for display baudrate (default max is 24mhz):
    BAUDRATE = 24000000

    # Setup SPI bus using hardware SPI:
    spi = board.SPI()

    disp = st7789.ST7789(
        spi,
        cs=cs_pin,
        dc=dc_pin,
        rst=reset_pin,
        baudrate=BAUDRATE,
        width=135,
        height=240,
        x_offset=53,
        y_offset=40,
        rotation=90,
    )

    # Make sure to create image with mode 'RGB' for full color.
    if disp.rotation % 180 == 90:
        height = disp.width  # we swap height/width to rotate it to landscape!
        width = disp.height
    else:
        width = disp.width  # we swap height/width to rotate it to landscape!
        height = disp.height

    backlight = digitalio.DigitalInOut(board.D22)
    backlight.switch_to_output()
    backlight.value = True

    clock = NYCClock(width, height)
    while True:
        disp.image(clock.frame())
        sleep(1)