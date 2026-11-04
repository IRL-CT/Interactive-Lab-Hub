"""Pastel 240x135 ST7789 interface for the Raspberry Pi cooking assistant."""

import threading
import textwrap


CREAM = (255, 249, 240)
INK = (67, 61, 57)
PASTELS = {
    "LISTENING": (202, 232, 255),
    "PROCESSING": (255, 239, 181),
    "SPEAKING": (207, 242, 221),
    "ERROR": (255, 207, 210),
    "TIMER": (229, 216, 255),
    "READY": (244, 224, 200),
}


class ScreenDisplay:
    """Draws a friendly chef UI; silently falls back when no screen exists."""

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.lock = threading.Lock()
        if not enabled:
            return
        try:
            import board
            import digitalio
            from PIL import Image, ImageDraw, ImageFont
            import adafruit_rgb_display.st7789 as st7789

            self.Image = Image
            self.ImageDraw = ImageDraw
            self.small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12
            )
            self.medium = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17
            )
            self.large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 31
            )
            cs = digitalio.DigitalInOut(board.D5)
            dc = digitalio.DigitalInOut(board.D25)
            backlight = digitalio.DigitalInOut(board.D22)
            backlight.switch_to_output(value=True)
            self.display = st7789.ST7789(
                board.SPI(), cs=cs, dc=dc, rst=None, baudrate=64_000_000,
                width=135, height=240, x_offset=53, y_offset=40,
            )
            self.rotation = 90
            self.show("READY", "Cooking assistant")
        except Exception as error:
            self.enabled = False
            print(f"Screen unavailable; continuing without it: {error}")

    def _chef_hat(self, draw, x=13, y=25):
        outline = (119, 102, 91)
        white = (255, 254, 250)
        draw.ellipse((x + 4, y + 8, x + 28, y + 34), fill=white, outline=outline, width=2)
        draw.ellipse((x + 16, y, x + 42, y + 31), fill=white, outline=outline, width=2)
        draw.ellipse((x + 31, y + 9, x + 52, y + 34), fill=white, outline=outline, width=2)
        draw.rounded_rectangle((x + 8, y + 27, x + 48, y + 47), radius=5,
                               fill=white, outline=outline, width=2)
        draw.line((x + 17, y + 36, x + 40, y + 36), fill=(220, 202, 188), width=2)

    def show(self, status, message=""):
        if not self.enabled:
            return
        with self.lock:
            image = self.Image.new("RGB", (240, 135), CREAM)
            draw = self.ImageDraw.Draw(image)
            color = PASTELS.get(status, PASTELS["READY"])
            draw.rounded_rectangle((6, 7, 234, 128), radius=18, fill=color)
            self._chef_hat(draw)
            draw.text((76, 17), status.title(), font=self.medium, fill=INK)
            draw.rounded_rectangle((73, 44, 225, 116), radius=12,
                                   fill=(255, 255, 255), outline=(255, 255, 255))
            lines = textwrap.wrap(message or "Please wait", width=22)[:3]
            y = 53
            for line in lines:
                draw.text((82, y), line, font=self.small, fill=INK)
                y += 19
            self.display.image(image, self.rotation)

    def listening(self):
        self.show("LISTENING", "I'm listening...")

    def processing(self, transcript):
        self.show("PROCESSING", transcript)

    def speaking(self, reply):
        self.show("SPEAKING", reply)

    def error(self, message):
        self.show("ERROR", message)

    def timer(self, remaining, total):
        if not self.enabled:
            return
        with self.lock:
            image = self.Image.new("RGB", (240, 135), CREAM)
            draw = self.ImageDraw.Draw(image)
            draw.rounded_rectangle((6, 7, 234, 128), radius=18, fill=PASTELS["TIMER"])
            self._chef_hat(draw, 12, 28)
            minutes, seconds = divmod(max(0, remaining), 60)
            draw.text((78, 16), "Timer", font=self.medium, fill=INK)
            draw.text((75, 47), f"{minutes:02d}:{seconds:02d}", font=self.large, fill=INK)
            draw.rounded_rectangle((76, 99, 220, 112), radius=6, fill=(255, 255, 255))
            ratio = remaining / total if total else 0
            width = int(140 * max(0, min(1, ratio)))
            if width:
                draw.rounded_rectangle((78, 101, 78 + width, 110), radius=4,
                                       fill=(171, 143, 222))
            self.display.image(image, self.rotation)
