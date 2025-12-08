"""
DisplayController: shows current year + vibe color on the Pi ST7789 screen.

- Background color = current genre:
    chill      → blue
    energetic  → green
    warm       → yellow
    party      → red
- Center text = current year (e.g., 1950, 2020)

Requires:
    pip install pillow adafruit-blinka adafruit-circuitpython-rgb-display
"""

import threading
import time
from typing import Tuple

import board
import digitalio
from adafruit_rgb_display.rgb import color565
import adafruit_rgb_display.st7789 as st7789

from PIL import Image, ImageDraw, ImageFont

from audio_engine import AudioEngine


# Map genres to RGB colors (0–255)
GENRE_COLORS = {
    "chill": (80, 130, 255),       # blue
    "energetic": (80, 200, 120),   # green
    "warm": (255, 220, 120),       # yellow
    "party": (255, 120, 120),      # red
}


def debug(msg: str):
    # print(f"[DISPLAY] {msg}")
    return


class DisplayController:
    def __init__(self, engine: AudioEngine) -> None:
        self.engine = engine
        self._running = False
        self._thread: threading.Thread | None = None

        # --- ST7789 wiring / config (adapted from your example) ---
        debug("Initializing ST7789 display...")

        # These pins should match your rpi5_minipitft_st7789.py setup
        cs_pin = digitalio.DigitalInOut(board.D5)    # GPIO5  (PIN 29)
        dc_pin = digitalio.DigitalInOut(board.D25)   # GPIO25 (PIN 22)
        reset_pin = None

        BAUDRATE = 64_000_000
        spi = board.SPI()

        # Adjust width/height/x_offset/y_offset to your panel
        self.display = st7789.ST7789(
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

        # Optional backlight (if wired)
        try:
            self.backlight = digitalio.DigitalInOut(board.D22)
            self.backlight.switch_to_output(value=True)
            debug("Backlight control initialized on D22.")
        except Exception as e:
            debug(f"Backlight init failed (maybe not wired): {e}")
            self.backlight = None
        
        self.width = self.display.height
        self.height = self.display.width

        debug(f"Display resolution: {self.width}x{self.height}")

        # Prepare font
        try:
            self.font = ImageFont.truetype("PibotoCondensed-Bold.ttf", 125)
            debug("Loaded DejaVuSans-Bold.ttf font.")
        except Exception:
            self.font = ImageFont.load_default()
            debug("Falling back to default PIL font.")

        debug("DisplayController initialized.")

    def start(self) -> None:
        """Start the display loop in a background thread."""
        if self._running:
            debug("start() called but already running; ignoring.")
            return
        debug("Starting display loop thread...")
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the display loop."""
        debug("Stopping display loop...")
        self._running = False

    def _run_loop(self) -> None:
        debug("Entering display loop...")
        while self._running:
            # Get current status from audio engine
            status = self.engine.get_status() if hasattr(self.engine, "get_status") else {}

            year = status.get("year", None)
            if year is None and hasattr(self.engine, "get_year"):
                year = self.engine.get_year()

            if year is None:
                year = 1950  # safe default
                debug("No year in status; defaulting to 1950")

            genre = status.get("genre", None)
            if genre is None and hasattr(self.engine, "current_genre"):
                genre = self.engine.current_genre

            if genre is None:
                genre = "chill"
                debug("No genre in status; defaulting to 'chill'")

            debug(f"Rendering year={year}, genre={genre}")

            # Convert genre → RGB → color565
            r, g, b = self._get_rgb_for_genre(genre)
            bg_color = color565(r, g, b)

            # Create an image with PIL
            image = Image.new("RGB", (self.width, self.height), (r, g, b))
            draw = ImageDraw.Draw(image)

            text = str(year)
            bbox = draw.textbbox((0, 0), text, font=self.font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            # Center text
            x = (self.width - text_w) // 2
            y = (self.height - text_h) // 2 - 40

            # option 1: complementary color
            # text_r = 255 - r
            # text_g = 255 - g
            # text_b = 255 - b
            # draw.text((x, y), text, font=self.font, fill=(text_r, text_g, text_b))

            # option 2: curated vibe color
            FONT_COLORS = {
                "chill":      (30, 60, 120),      # deep navy
                "energetic":  (20, 80, 40),       # forest green
                "warm":       (120, 60, 30),      # warm brown
                "party":      (255, 255, 255),    # white pop
            }
            text_color = FONT_COLORS.get(genre, (0, 0, 0))
            draw.text(
                (x, y),
                text,
                font=self.font,
                fill=text_color,
            )

            # Push to display
            self.display.image(image)

            time.sleep(0.1)  # ~10 FPS

        debug("Exiting display loop.")

    def _get_rgb_for_genre(self, genre: str) -> Tuple[int, int, int]:
        genre = (genre or "").lower()
        rgb = GENRE_COLORS.get(genre, (200, 200, 200))  # default grey
        debug(f"_get_rgb_for_genre({genre}) -> {rgb}")
        return rgb
