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
        self.image = None
        self.draw = None
        self.font = None


        if not (board and busio and adafruit_ssd1306 and Image and ImageDraw and ImageFont):
            print("[OLED] Missing libraries, OLED disabled.")
            return

        try:
            i2c = board.I2C()
            # 128x64, address 0x3C
            self.display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
            self.display.fill(0)
            self.display.show()


            self.image = Image.new("1", (128, 64))
            self.draw = ImageDraw.Draw(self.image)

            try:
                self.font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12
                )
            except Exception:
                self.font = ImageFont.load_default()

            self.enabled = True
            print("[OLED] Ready (SSD1306 at 0x3C).")

        except Exception as e:
            print(f"[OLED] init failed → {e}")
            self.enabled = False

    def _measure_text(self, text: str):

        if not self.font:
            return (len(text) * 6, 10)


        try:
            return self.font.getsize(text)
        except Exception:
            pass

        # 尝试 getbbox
        try:
            bbox = self.font.getbbox(text)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            return (w, h)
        except Exception:
            pass


        return (len(text) * 6, 10)

    def show_element(self, name: str):

        if not self.enabled:
            print(f"[OLED] {name}")
            return


        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)


        w, h = self._measure_text(name)
        x = (128 - w) // 2
        y = (64 - h) // 2


        self.draw.text((x, y), name, font=self.font, fill=255)


        self.display.image(self.image)
        self.display.show()
        print(f"[OLED] Display element: {name}")
