# sensors/tft_display.py

try:
    import digitalio
    import board
    from PIL import Image, ImageDraw, ImageFont
    import adafruit_rgb_display.st7789 as st7789
except ImportError:
    digitalio = None
    board = None
    Image = None
    ImageDraw = None
    ImageFont = None
    st7789 = None


class TFTDisplay:
    def __init__(self):
        self.display = None
        self.enabled = False

        if digitalio is None or board is None or st7789 is None or Image is None:
            print("[TFTDisplay] Library not available. Running in dummy mode.")
            return

        try:
            # 这些 pin 按你原来的设置来
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
                y_offset=80,
            )

            self.image = Image.new("RGB", (240, 240))
            self.draw = ImageDraw.Draw(self.image)
            self.font = ImageFont.load_default()

            self.enabled = True
            print("[TFTDisplay] TFT initialized successfully.")

        except Exception as e:
            print(f"[TFTDisplay] Could not initialize TFT: {e}")
            self.display = None
            self.enabled = False

    def show_element(self, element):
        if not self.enabled or self.display is None:
            print(f"[TFTDisplay] Element -> {element}")
            return

        self.draw.rectangle((0, 0, 240, 240), fill="black")
        text = f"Element: {element}"
        self.draw.text((20, 100), text, fill=(255, 255, 255), font=self.font)
        self.display.image(self.image)
