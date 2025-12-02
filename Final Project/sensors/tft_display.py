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

            # Larger font (default is too small)
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)

            self.enabled = True
            print("[OLED] Ready (SSD1306 at 0x3C).")

        except Exception as e:
            print(f"[OLED] init failed → {e}")
            self.enabled = False


    def show_element(self, name: str):
        """Show ONLY the element name, large and centered."""
        if not self.enabled:
            print(f"[OLED] {name}")
            return

        # Clear screen
        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)

        # Compute text size to center it
        w, h = self.draw.textsize(name, font=self.font)
        x = (128 - w) // 2
        y = (64 - h) // 2

        # Draw text
        self.draw.text((x, y), name, font=self.font, fill=255)

        # Show on the OLED
        self.display.image(self.image)
        self.display.show()
