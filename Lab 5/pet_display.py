"""Lab 2's GPIO5 CS wiring and 240x135 landscape display; terminal fallback."""
import select
import sys
import textwrap
import time


class Display:
    def __init__(self, terminal=False):
        self.resources = []
        self.spi = self.panel = self.backlight = None
        self.pins = []
        self.was_a = False
        self.b_since = None
        self.b_fired = False
        self.last_a = 0
        if not terminal:
            try:
                import board
                import digitalio
                from adafruit_rgb_display import st7789
                from PIL import Image, ImageDraw, ImageFont
                self.Image, self.ImageDraw = Image, ImageDraw
                try:
                    self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
                except OSError:
                    self.font = ImageFont.load_default()
                def pin(name):
                    obj = digitalio.DigitalInOut(name)
                    self.resources.append(obj)
                    return obj
                cs, dc = pin(board.D5), pin(board.D25)
                self.spi = board.SPI()
                self.panel = st7789.ST7789(self.spi, cs=cs, dc=dc, rst=None,
                                         baudrate=64000000, width=135, height=240,
                                         x_offset=53, y_offset=40)
                self.backlight = pin(board.D22)
                self.backlight.switch_to_output(value=True)
                for name in (board.D23, board.D24):
                    button = pin(name)
                    button.switch_to_input(pull=digitalio.Pull.UP)
                    self.pins.append(button)
                self.show('Pet Night Diary', 'Press A to start')
            except Exception as error:
                print('PiTFT unavailable; terminal fallback:', error, flush=True)
                self.close()
        print('Terminal: a + Enter = start/next; b + Enter = stop/exit. Ctrl-C = safe stop.', flush=True)

    def show(self, *lines):
        print(' | '.join(lines), flush=True)
        if self.panel:
            image = self.Image.new('RGB', (240, 135), '#101925')
            draw = self.ImageDraw.Draw(image)
            y = 5
            for line in lines:
                for part in textwrap.wrap(line, 27) or ['']:
                    draw.text((6, y), part, font=self.font, fill='white')
                    y += 18
            self.backlight.value = True
            self.panel.image(image, 90)

    def blank(self):
        if self.backlight:
            self.backlight.value = False

    def poll(self):
        if self.pins:
            now = time.monotonic()
            a, b = (not pin.value for pin in self.pins)
            event = None
            if a and not self.was_a and now-self.last_a > .25:
                event, self.last_a = 'a', now
            self.was_a = a
            if b:
                if self.b_since is None:
                    self.b_since = now
                if now-self.b_since >= 1.5 and not self.b_fired:
                    event, self.b_fired = 'b', True
            else:
                self.b_since, self.b_fired = None, False
            if event:
                return event
        if sys.stdin.isatty() and select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.readline().strip().lower()
        return None

    def close(self):
        if self.backlight:
            try:
                self.backlight.value = False
            except Exception:
                pass
        for resource in reversed(self.resources):
            try:
                resource.deinit()
            except Exception:
                pass
        if self.spi:
            self.spi.deinit()
        self.resources, self.pins = [], []
        self.panel = self.backlight = self.spi = None
