
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789


class DreamDisplay:
    def __init__(self):
        spi = board.SPI()

        # Linux SPI manages chip select on Raspberry Pi 5
        cs = None
        dc = digitalio.DigitalInOut(board.D25)

        self.disp = st7789.ST7789(
            spi,
            cs=cs,
            dc=dc,
            rst=None,
            baudrate=24000000,
            width=135,
            height=240,
            x_offset=53,
            y_offset=40,
            rotation=90
        )

        # Draw in landscape orientation
        self.width = 240
        self.height = 135

        font_path = (
            "/usr/share/fonts/truetype/dejavu/"
            "DejaVuSans.ttf"
        )

        self.title_font = ImageFont.truetype(font_path, 20)
        self.body_font = ImageFont.truetype(font_path, 15)
        self.icon_font = ImageFont.truetype(font_path, 38)


    def draw_icon(self, draw, icon):
        """Draw a simple status icon using Pillow."""

        cx = self.width // 2
        cy = 30
        color = "#D4C4FF"

        if icon == "moon":
            # Crescent moon
            draw.ellipse(
                (cx - 19, cy - 19, cx + 19, cy + 19),
                fill=color
            )
            draw.ellipse(
                (cx - 8, cy - 25, cx + 25, cy + 9),
                fill="#151F38"
            )

            # Small stars
            draw.ellipse(
                (cx + 23, cy - 15, cx + 27, cy - 11),
                fill="#FFD38B"
            )

        elif icon == "scan":
            # Camera viewfinder
            draw.rectangle(
                (cx - 25, cy - 16, cx + 25, cy + 16),
                outline=color,
                width=3
            )
            draw.ellipse(
                (cx - 9, cy - 9, cx + 9, cy + 9),
                outline=color,
                width=3
            )

        elif icon == "magic":
            # Four-point star
            draw.polygon(
                [
                    (cx, cy - 24),
                    (cx + 7, cy - 7),
                    (cx + 24, cy),
                    (cx + 7, cy + 7),
                    (cx, cy + 24),
                    (cx - 7, cy + 7),
                    (cx - 24, cy),
                    (cx - 7, cy - 7)
                ],
                fill=color
            )

        elif icon == "sun":
            draw.ellipse(
                (cx - 14, cy - 14, cx + 14, cy + 14),
                fill="#FFD38B"
            )

            for dx, dy in [
                (0, -23), (0, 23),
                (-23, 0), (23, 0),
                (-17, -17), (17, 17),
                (-17, 17), (17, -17)
            ]:
                draw.line(
                    (cx + dx * 0.75,
                     cy + dy * 0.75,
                     cx + dx,
                     cy + dy),
                    fill="#FFD38B",
                    width=3
                )

        elif icon == "speaker":
            draw.polygon(
                [
                    (cx - 22, cy - 8),
                    (cx - 12, cy - 8),
                    (cx, cy - 18),
                    (cx, cy + 18),
                    (cx - 12, cy + 8),
                    (cx - 22, cy + 8)
                ],
                fill=color
            )
            draw.arc(
                (cx - 5, cy - 20,
                 cx + 27, cy + 20),
                start=290,
                end=70,
                fill=color,
                width=3
            )

        elif icon == "check":
            draw.ellipse(
                (cx - 20, cy - 20,
                 cx + 20, cy + 20),
                outline="#A7E5C0",
                width=3
            )
            draw.line(
                [
                    (cx - 10, cy),
                    (cx - 2, cy + 9),
                    (cx + 13, cy - 10)
                ],
                fill="#A7E5C0",
                width=4,
                joint="curve"
            )

        elif icon == "error":
            draw.ellipse(
                (cx - 20, cy - 20,
                 cx + 20, cy + 20),
                outline="#FF8B8B",
                width=3
            )
            draw.line(
                (cx, cy - 11, cx, cy + 5),
                fill="#FF8B8B",
                width=4
            )
            draw.ellipse(
                (cx - 2, cy + 10,
                 cx + 2, cy + 14),
                fill="#FF8B8B"
            )

    def show(
        self,
        title,
        message="",
        icon="*",
        background="#151F38"
    ):
        """Display a status screen on the Mini PiTFT."""

        image = Image.new(
            "RGB",
            (self.width, self.height),
            background
        )

        draw = ImageDraw.Draw(image)

        def centered(text, y, font, color):
            bounds = draw.textbbox((0, 0), text, font=font)
            text_width = bounds[2] - bounds[0]

            x = (self.width - text_width) // 2

            draw.text(
                (x, y),
                text,
                font=font,
                fill=color
            )

        # Decorative symbol
        self.draw_icon(draw, icon)

        # Main title
        centered(
            title,
            53,
            self.title_font,
            "#FFFFFF"
        )

        # Status message (up to two lines)
        for i, line in enumerate(message.split("\n")[:2]):
            centered(
                line,
                87 + i * 20,
                self.body_font,
                "#BFC9E2"
            )

        self.disp.image(image)


if __name__ == "__main__":
    screen = DreamDisplay()

    screen.show(
        "Dream Machine",
        "Press to start",
        icon="*"
    )
