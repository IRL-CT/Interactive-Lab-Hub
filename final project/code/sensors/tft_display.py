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

        if not (board and busio and adafruit_ssd1306):
            print("[OLED] Missing libraries, OLED disabled.")
            return

        try:
            i2c = board.I2C()
            self.display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
            self.display.fill(0)
            self.display.show()

            # High-contrast monochrome buffer
            self.image = Image.new("1", (128, 64))
            self.draw = ImageDraw.Draw(self.image)

            # Larger readable font
            self.font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
            )

            self.enabled = True
            print("[OLED] Ready (SSD1306 at 0x3C).")

        except Exception as e:
            print(f"[OLED] init failed → {e}")
            self.enabled = False

    # ------------------------------------------------------------
    # Show ONE element (big centered)
    # ------------------------------------------------------------
    def show_element(self, name: str):
        if not self.enabled:
            print(f"[OLED] {name}")
            return

        # Clear screen
        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)

        # Compute text size (use Pillow >=10 compatible API)
        bbox = self.draw.textbbox((0, 0), name, font=self.font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        # Center text
        x = (128 - w) // 2
        y = (64 - h) // 2
        self.draw.text((x, y), name, font=self.font, fill=255)

        self.display.image(self.image)
        self.display.show()

    # ------------------------------------------------------------
    # Show list of chosen elements (up to 3)
    # ------------------------------------------------------------
    def show_element_list(self, elements):
        if not self.enabled:
            print("[OLED] Selected:", elements)
            return

        # Clear screen
        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)

        # Title
        self.draw.text((2, 2), "Chosen:", font=self.font, fill=255)

        # List elements
        y = 20
        for e in elements:
            self.draw.text((4, y), e, font=self.font, fill=255)
            y += 16

        self.display.image(self.image)
        self.display.show()
