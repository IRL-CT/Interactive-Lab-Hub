"""
The Mini PiTFT from Lab 2, as a tiny helper for the night device.

Stop the IP-address service first, or two scripts will fight over the screen (Lab 2 README):

    sudo systemctl stop piscreen.service --now
    sudo systemctl start piscreen.service --now      # in the morning, to bring the IP screen back

If the screen cannot be set up (service still running, library missing, not on the Pi), every
method does nothing and says why once, so the rest of the night device keeps working.
"""
from PIL import Image, ImageDraw, ImageFont

FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


class Screen:
    def __init__(self):
        self.ok = False
        try:
            import board
            import digitalio
            from adafruit_rgb_display import st7789
            self._cs = digitalio.DigitalInOut(board.D5)         # same wiring and settings as Lab 2
            self._dc = digitalio.DigitalInOut(board.D25)
            self._disp = st7789.ST7789(board.SPI(), cs=self._cs, dc=self._dc, rst=None,
                                       baudrate=64000000, width=135, height=240, x_offset=53, y_offset=40)
            self._backlight = digitalio.DigitalInOut(board.D22)
            self._backlight.switch_to_output(value=True)
            self.width, self.height = self._disp.height, self._disp.width     # rotated to landscape
            self._font = ImageFont.truetype(FONT_FILE, 22)
            self._small = ImageFont.truetype(FONT_FILE, 16)
            self.ok = True
        except Exception as e:
            print(f"mini PiTFT not available ({e!r}); is piscreen.service stopped?", flush=True)

    def _show(self, image):
        self._backlight.value = True
        self._disp.image(image, 90)

    def text(self, *lines, color="#FFFFFF"):
        """Show up to a few short lines of text."""
        if not self.ok:
            return
        image = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        y = 8
        for line in lines:
            draw.text((8, y), line, font=self._font, fill=color)
            y += 30
        self._show(image)

    def bar(self, title, fraction, color="#00C800"):
        """A title and a progress bar, 0 (empty) to 1 (full)."""
        if not self.ok:
            return
        fraction = max(0.0, min(1.0, fraction))
        image = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        draw.text((8, 12), title, font=self._font, fill="#FFFFFF")
        left, top, right, bottom = 10, 70, self.width - 10, 105
        draw.rectangle((left, top, right, bottom), outline="#FFFFFF", width=2)
        draw.rectangle((left + 2, top + 2, left + 2 + int((right - left - 4) * fraction), bottom - 2), fill=color)
        draw.text((8, 110), f"{int(fraction * 100)} %", font=self._small, fill="#AAAAAA")
        self._show(image)

    def off(self):
        """Black screen and backlight off, for the night."""
        if not self.ok:
            return
        self._disp.image(Image.new("RGB", (self.width, self.height)), 90)
        self._backlight.value = False
