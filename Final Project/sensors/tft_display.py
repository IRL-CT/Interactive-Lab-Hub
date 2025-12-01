import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

class TFTDisplay:
    def __init__(self):
        self.cs_pin = digitalio.DigitalInOut(board.CE0)
        self.dc_pin = digitalio.DigitalInOut(board.D25)
        self.reset_pin = digitalio.DigitalInOut(board.D27)
        self.baudrate = 64000000

        spi = board.SPI()

        self.display = st7789.ST7789(
            spi,
            cs=self.cs_pin,
            dc=self.dc_pin,
            rst=self.reset_pin,
            baudrate=self.baudrate,
            width=240,
            height=240,
            x_offset=0,
            y_offset=80
        )

        self.image = Image.new("RGB", (240, 240))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()

    def show_element(self, element):
        self.draw.rectangle((0, 0, 240, 240), fill="black")
        self.draw.text((20, 100), f"Element: {element}", fill=(255,255,255), font=self.font)
        self.display.image(self.image)
