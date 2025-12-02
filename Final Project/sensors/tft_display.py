try:
    import board
    import busio
    from PIL import Image, ImageDraw, ImageFont
    import adafruit_ssd1306
except ImportError:
    board = None
    busio = None
    Image = None
    ImageDraw = None
    ImageFont = None
    adafruit_ssd1306 = None


class TFTDisplay:


    def __init__(self):
        self.display = None
        self.enabled = False

        if board is None or busio is None or adafruit_ssd1306 is None or Image is None:
            print("[OLED] Libraries missing, running in dummy mode.")
            return

        try:
            i2c = board.I2C()  # uses SCL, SDA
            self.display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
            self.display.fill(0)
            self.display.show()

            self.image = Image.new("1", (128, 64))
            self.draw = ImageDraw.Draw(self.image)
            self.font = ImageFont.load_default()

            self.enabled = True
            print("[OLED] SSD1306 initialized at 0x3C (128x64).")

        except Exception as e:
            print(f"[OLED] Could not initialize OLED: {e}")
            self.display = None
            self.enabled = False

        def show_element(self, element: str):
        if not self.enabled or self.display is None:
            print(f"[OLED] Element -> {element}")
            return

        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        
        try:
            from PIL import ImageFont
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except Exception:
            self.font = ImageFont.load_default()

        title = "Inner Constellation"
        line = f"Element: {element}"

        title_w, title_h = self.draw.textsize(title, font=self.font)
        line_w, line_h = self.draw.textsize(line, font=self.font)

        title_x = (128 - title_w) // 2
        line_x = (128 - line_w) // 2

        self.draw.text((title_x, 10), title, font=self.font, fill=255)
        self.draw.text((line_x, 10 + title_h + 6), line, font=self.font, fill=255)

        self.display.image(self.image)
        self.display.show()

